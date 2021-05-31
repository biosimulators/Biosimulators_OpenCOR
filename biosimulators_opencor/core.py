""" Methods for using OpenCOR to execute SED tasks in COMBINE archives and save their outputs

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-05-28
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .utils import (validate_simulation, load_opencor_simulation,
                    get_results_from_opencor_simulation, log_opencor_execution, get_mock_libcellml)
from biosimulators_utils.combine.exec import exec_sedml_docs_in_archive
from biosimulators_utils.log.data_model import CombineArchiveLog, TaskLog, StandardOutputErrorCapturerLevel  # noqa: F401
from biosimulators_utils.plot.data_model import PlotFormat  # noqa: F401
from biosimulators_utils.report.data_model import ReportFormat, VariableResults  # noqa: F401
from biosimulators_utils.sedml.data_model import Task, Variable  # noqa: F401
from biosimulators_utils.sedml.exec import exec_sed_doc
from unittest import mock
import functools

__all__ = [
    'exec_sedml_docs_in_combine_archive', 'exec_sed_task',
]


def exec_sedml_docs_in_combine_archive(archive_filename, out_dir,
                                       report_formats=None, plot_formats=None,
                                       bundle_outputs=None, keep_individual_outputs=None):
    """ Execute the SED tasks defined in a COMBINE/OMEX archive and save the outputs

    Args:
        archive_filename (:obj:`str`): path to COMBINE/OMEX archive
        out_dir (:obj:`str`): path to store the outputs of the archive

            * CSV: directory in which to save outputs to files
              ``{ out_dir }/{ relative-path-to-SED-ML-file-within-archive }/{ report.id }.csv``
            * HDF5: directory in which to save a single HDF5 file (``{ out_dir }/reports.h5``),
              with reports at keys ``{ relative-path-to-SED-ML-file-within-archive }/{ report.id }`` within the HDF5 file

        report_formats (:obj:`list` of :obj:`ReportFormat`, optional): report format (e.g., csv or h5)
        plot_formats (:obj:`list` of :obj:`PlotFormat`, optional): report format (e.g., pdf)
        bundle_outputs (:obj:`bool`, optional): if :obj:`True`, bundle outputs into archives for reports and plots
        keep_individual_outputs (:obj:`bool`, optional): if :obj:`True`, keep individual output files

    Returns:
        :obj:`CombineArchiveLog`: log
    """
    sed_doc_executer = functools.partial(exec_sed_doc, exec_sed_task)

    with mock.patch.dict('sys.modules', libcellml=get_mock_libcellml()):
        return exec_sedml_docs_in_archive(sed_doc_executer, archive_filename, out_dir,
                                          apply_xml_model_changes=True,
                                          report_formats=report_formats,
                                          plot_formats=plot_formats,
                                          bundle_outputs=bundle_outputs,
                                          keep_individual_outputs=keep_individual_outputs,
                                          log_level=StandardOutputErrorCapturerLevel.python)


def exec_sed_task(sed_task, sed_variables, log=None):
    ''' Execute a task and save its results

    Args:
       sed_task (:obj:`Task`): task
       sed_variables (:obj:`list` of :obj:`Variable`): variables that should be recorded
       log (:obj:`TaskLog`, optional): log for the task

    Returns:
        :obj:`tuple`:

            :obj:`VariableResults`: results of variables
            :obj:`TaskLog`: log

    Raises:
        :obj:`ValueError`: if the task or an aspect of the task is not valid, or the requested output variables
            could not be recorded
        :obj:`NotImplementedError`: if the task is not of a supported type or involves an unsupported feature
    '''
    # initialize a log of the execution of this task
    log = log or TaskLog()

    # check that a simulation (or a similar simulation) can be executed with OpenCOR
    opencor_sed_task, opencor_variable_names = validate_simulation(sed_task, sed_variables)

    # load an OpenCOR simulation
    opencor_sim = load_opencor_simulation(opencor_sed_task, sed_variables)

    # execute the simulation
    if not opencor_sim.run():
        raise RuntimeError('OpenCOR failed unexpectedly.')

    # collect the results of the simulation
    variable_results = get_results_from_opencor_simulation(opencor_sim, sed_task, sed_variables, opencor_variable_names)

    # log action
    log_opencor_execution(opencor_sed_task, log)

    # return results and log
    return variable_results, log
