""" Methods for using OpenCOR to execute SED tasks in COMBINE archives and save their outputs

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-05-28
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .utils import (validate_task, validate_simulation, load_opencor_simulation,
                    get_results_from_opencor_simulation, log_opencor_execution, get_mock_libcellml)
from biosimulators_utils.combine.exec import exec_sedml_docs_in_archive
from biosimulators_utils.config import get_config, Config  # noqa: F401
from biosimulators_utils.utils.core import raise_errors_warnings
from biosimulators_utils.log.data_model import CombineArchiveLog, TaskLog, StandardOutputErrorCapturerLevel  # noqa: F401
from biosimulators_utils.viz.data_model import VizFormat  # noqa: F401
from biosimulators_utils.report.data_model import ReportFormat, VariableResults, SedDocumentResults  # noqa: F401
from biosimulators_utils.sedml import validation
from biosimulators_utils.sedml.data_model import Task, ModelAttributeChange, Variable  # noqa: F401
from biosimulators_utils.sedml.exec import exec_sed_doc as base_exec_sed_doc
from biosimulators_utils.sedml.utils import apply_changes_to_xml_model
from unittest import mock
import copy
import os
import tempfile

__all__ = [
    'exec_sedml_docs_in_combine_archive', 'exec_sed_doc', 'exec_sed_task', 'preprocess_sed_task',
]


def exec_sedml_docs_in_combine_archive(archive_filename, out_dir, config=None):
    """ Execute the SED tasks defined in a COMBINE/OMEX archive and save the outputs

    Args:
        archive_filename (:obj:`str`): path to COMBINE/OMEX archive
        out_dir (:obj:`str`): path to store the outputs of the archive

            * CSV: directory in which to save outputs to files
              ``{ out_dir }/{ relative-path-to-SED-ML-file-within-archive }/{ report.id }.csv``
            * HDF5: directory in which to save a single HDF5 file (``{ out_dir }/reports.h5``),
              with reports at keys ``{ relative-path-to-SED-ML-file-within-archive }/{ report.id }`` within the HDF5 file

        config (:obj:`Config`, optional): BioSimulators common configuration

    Returns:
        :obj:`tuple`:

            * :obj:`SedDocumentResults`: results
            * :obj:`CombineArchiveLog`: log
    """
    with mock.patch.dict('sys.modules', libcellml=get_mock_libcellml()):
        return exec_sedml_docs_in_archive(exec_sed_doc, archive_filename, out_dir,
                                          apply_xml_model_changes=True,
                                          log_level=StandardOutputErrorCapturerLevel.python,
                                          config=config)


def exec_sed_doc(doc, working_dir, base_out_path, rel_out_path=None,
                 apply_xml_model_changes=False,
                 log=None, indent=0, pretty_print_modified_xml_models=False,
                 log_level=StandardOutputErrorCapturerLevel.c, config=None):
    """ Execute the tasks specified in a SED document and generate the specified outputs

    Args:
        doc (:obj:`SedDocument` or :obj:`str`): SED document or a path to SED-ML file which defines a SED document
        working_dir (:obj:`str`): working directory of the SED document (path relative to which models are located)

        base_out_path (:obj:`str`): path to store the outputs

            * CSV: directory in which to save outputs to files
              ``{base_out_path}/{rel_out_path}/{report.id}.csv``
            * HDF5: directory in which to save a single HDF5 file (``{base_out_path}/reports.h5``),
              with reports at keys ``{rel_out_path}/{report.id}`` within the HDF5 file

        rel_out_path (:obj:`str`, optional): path relative to :obj:`base_out_path` to store the outputs
        apply_xml_model_changes (:obj:`bool`, optional): if :obj:`True`, apply any model changes specified in the SED-ML file before
            calling :obj:`task_executer`.
        log (:obj:`SedDocumentLog`, optional): log of the document
        indent (:obj:`int`, optional): degree to indent status messages
        pretty_print_modified_xml_models (:obj:`bool`, optional): if :obj:`True`, pretty print modified XML models
        log_level (:obj:`StandardOutputErrorCapturerLevel`, optional): level at which to log output
        config (:obj:`Config`, optional): BioSimulators common configuration
        simulator_config (:obj:`SimulatorConfig`, optional): tellurium configuration

    Returns:
        :obj:`tuple`:

            * :obj:`ReportResults`: results of each report
            * :obj:`SedDocumentLog`: log of the document
    """
    return base_exec_sed_doc(exec_sed_task, doc, working_dir, base_out_path,
                             rel_out_path=rel_out_path,
                             apply_xml_model_changes=apply_xml_model_changes,
                             log=log,
                             indent=indent,
                             pretty_print_modified_xml_models=pretty_print_modified_xml_models,
                             log_level=log_level,
                             config=config)


def exec_sed_task(task, variables, preprocessed_task=None, log=None, config=None):
    ''' Execute a task and save its results

    Args:
        task (:obj:`Task`): task
        variables (:obj:`list` of :obj:`Variable`): variables that should be recorded
        preprocessed_task (:obj:`dict`, optional): preprocessed information about the task, including possible
            model changes and variables. This can be used to avoid repeatedly executing the same initialization
            for repeated calls to this method.
        log (:obj:`TaskLog`, optional): log for the task
        config (:obj:`Config`, optional): BioSimulators common configuration

    Returns:
        :obj:`tuple`:

            :obj:`VariableResults`: results of variables
            :obj:`TaskLog`: log

    Raises:
        :obj:`ValueError`: if the task or an aspect of the task is not valid, or the requested output variables
            could not be recorded
        :obj:`NotImplementedError`: if the task is not of a supported type or involves an unsupported feature
    '''
    if not config:
        config = get_config()

    # initialize a log of the execution of this task
    if config.LOG and not log:
        log = TaskLog()

    if preprocessed_task is None:
        preprocessed_task = preprocess_sed_task(task, variables, config=config)

    # modify model
    if task.model.changes:
        raise_errors_warnings(validation.validate_model_change_types(task.model.changes, (ModelAttributeChange,)),
                              error_summary='Changes for model `{}` are not supported.'.format(task.model.id))

        model_etree = preprocessed_task['model_etree']

        model = copy.deepcopy(task.model)
        for change in model.changes:
            change.new_value = str(change.new_value)

        apply_changes_to_xml_model(model, model_etree, sed_doc=None, working_dir=None)

        model_file, model_filename = tempfile.mkstemp(suffix='.xml')
        os.close(model_file)

        model_etree.write(model_filename,
                          xml_declaration=True,
                          encoding="utf-8",
                          standalone=False,
                          pretty_print=False)
    else:
        model_filename = task.model.source

    # set up OpenCOR task
    opencor_task = copy.deepcopy(preprocessed_task['task'])
    opencor_task.model.source = model_filename
    opencor_task.model.changes = []
    opencor_task.simulation.initial_time = task.simulation.initial_time
    opencor_task.simulation.output_start_time = task.simulation.output_start_time
    opencor_task.simulation.output_end_time = task.simulation.output_end_time
    opencor_task.simulation.number_of_steps = task.simulation.number_of_steps
    opencor_task.simulation = validate_simulation(opencor_task.simulation)

    # load an OpenCOR simulation
    opencor_sim = load_opencor_simulation(opencor_task, variables)

    # clean up temporary model
    if task.model.changes:
        os.remove(model_filename)

    # execute the simulation
    if not opencor_sim.run():
        raise RuntimeError('OpenCOR failed unexpectedly.')

    # collect the results of the simulation
    variable_results = get_results_from_opencor_simulation(opencor_sim, task, variables, preprocessed_task['variable_names'])

    # log action
    if config.LOG:
        log_opencor_execution(opencor_task, log)

    # return results and log
    return variable_results, log


def preprocess_sed_task(task, variables, config=None):
    """ Preprocess a SED task, including its possible model changes and variables. This is useful for avoiding
    repeatedly initializing tasks on repeated calls of :obj:`exec_sed_task`.

    Args:
        task (:obj:`Task`): task
        variables (:obj:`list` of :obj:`Variable`): variables that should be recorded
        config (:obj:`Config`, optional): BioSimulators common configuration

    Returns:
        :obj:`dict`: preprocessed information about the task
    """
    if not config:
        config = get_config()

    opencor_task, model_etree, opencor_variable_names = validate_task(task, variables, config=config)

    # return preprocessed information
    return {
        'task': opencor_task,
        'model_etree': model_etree,
        'variable_names': opencor_variable_names,
    }
