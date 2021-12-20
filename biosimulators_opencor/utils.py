""" Utilities for OpenCOR

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-05-28
:Copyright: 2021, BioSimulators Team
:License: MIT
"""

from .data_model import KISAO_ALGORITHM_MAP
from biosimulators_utils.config import get_config, Config  # noqa: F401
from biosimulators_utils.data_model import ValueType  # noqa: F401
from biosimulators_utils.log.data_model import TaskLog  # noqa: F401
from biosimulators_utils.report.data_model import VariableResults  # noqa: F401
from biosimulators_utils.sedml.data_model import (  # noqa: F401
    SedDocument, ModelLanguage, ModelAttributeChange, UniformTimeCourseSimulation, Algorithm, Task, RepeatedTask,
    VectorRange, SubTask, DataGenerator, Variable)
from biosimulators_utils.sedml.io import SedmlSimulationWriter
from biosimulators_utils.sedml import validation
from biosimulators_utils.simulator.utils import get_algorithm_substitution_policy
from biosimulators_utils.utils.core import validate_str_value, raise_errors_warnings
from biosimulators_utils.warnings import warn, BioSimulatorsWarning
from kisao.data_model import AlgorithmSubstitutionPolicy, ALGORITHM_SUBSTITUTION_POLICY_LEVELS
from kisao.utils import get_preferred_substitute_algorithm_by_ids
from unittest import mock
import copy
import lxml.etree
import opencor
import os
import tempfile


__all__ = [
    'validate_task',
    'validate_variable_xpaths',
    'validate_simulation',
    'get_opencor_algorithm',
    'get_opencor_parameter_value',
    'build_opencor_sedml_doc',
    'save_task_to_opencor_sedml_file',
    'load_opencor_simulation',
    'validate_opencor_simulation',
    'get_results_from_opencor_simulation',
    'log_opencor_execution',
    'get_mock_libcellml',
]


def validate_task(task, variables, config=None):
    """ Validate that a simulation can be executed with OpenCOR

    Args:
        task (:obj:`Task`): request simulation task
        variables (:obj:`list` of :obj:`Variable`): variables that should be recorded
        config (:obj:`Config`, optional): BioSimulators common configuration

    Returns:
        :obj:`tuple:`:

            * :obj:`Task`: possibly alternate task that OpenCOR should execute
            * :obj:`lxml.etree._ElementTree`: element tree for model
            * :obj:`dict`: dictionary that maps the id of each SED variable to the name that OpenCOR uses to reference it
    """
    config = config or get_config()
    model = task.model
    sim = task.simulation

    if config.VALIDATE_SEDML:
        raise_errors_warnings(validation.validate_task(task),
                              error_summary='Task `{}` is invalid.'.format(task.id))
        raise_errors_warnings(validation.validate_model_language(model.language, ModelLanguage.CellML),
                              error_summary='Language for model `{}` is not supported.'.format(model.id))
        raise_errors_warnings(validation.validate_model_change_types(model.changes, (ModelAttributeChange,)),
                              error_summary='Changes for model `{}` are not supported.'.format(model.id))
        raise_errors_warnings(*validation.validate_model_changes(model),
                              error_summary='Changes for model `{}` are invalid.'.format(model.id))
        raise_errors_warnings(validation.validate_simulation_type(sim, (UniformTimeCourseSimulation, )),
                              error_summary='{} `{}` is not supported.'.format(sim.__class__.__name__, sim.id))
        raise_errors_warnings(*validation.validate_simulation(sim),
                              error_summary='Simulation `{}` is invalid.'.format(sim.id))
        raise_errors_warnings(*validation.validate_data_generator_variables(variables),
                              error_summary='Data generator variables for task `{}` are invalid.'.format(task.id))

    # read model; TODO: support imports
    model_etree = lxml.etree.parse(model.source)

    # validate variables
    opencor_variable_names = validate_variable_xpaths(variables, model_etree)

    # validate simulation
    opencor_simulation = validate_simulation(task.simulation)

    # check that OpenCOR can execute the request algorithm (or a similar one)
    opencor_algorithm = get_opencor_algorithm(task.simulation.algorithm, config=config)

    # create new task to manage configuration for OpenCOR
    opencor_task = copy.deepcopy(task)
    opencor_task.simulation = opencor_simulation
    opencor_task.simulation.algorithm = opencor_algorithm

    return opencor_task, model_etree, opencor_variable_names


def validate_variable_xpaths(sed_variables, model_etree):
    """ Get the names OpenCOR uses to refer to model variable

    Args:
        model_etree (:obj:`lxml.etree._ElementTree`): element tree for model
        sed_variables (:obj:`list` of :obj:`Variable`): SED variables

    Returns:
        :obj:`dict`: dictionary that maps the id of each SED variable to the name that OpenCOR uses to reference it
    """
    opencor_variable_names = {}
    for sed_variable in sed_variables:
        if not sed_variable.target:
            msg = 'Symbols are not supported.'
            raise NotImplementedError(msg)

        namespaces = copy.copy(sed_variable.target_namespaces)
        namespaces.pop(None, None)

        obj_target, _, attrib_target = sed_variable.target.partition('/@')
        xml_objs = model_etree.xpath(obj_target, namespaces=namespaces)

        if len(xml_objs) == 0:
            msg = (
                'XPath targets of variables must reference unique observables. '
                'The target `{}` of variable `{}` does not match any model elements.'
            ).format(sed_variable.target, sed_variable.id)
            raise ValueError(msg)

        if len(xml_objs) > 1:
            msg = (
                'XPath targets of variables must reference unique observables. '
                'The target `{}` of variable `{}` matches multiple model elements.'
            ).format(sed_variable.target, sed_variable.id)
            raise ValueError(msg)

        xml_obj = xml_objs[0]

        names = []
        while True:
            name = xml_obj.attrib.get('name', None)
            names.append(name)
            xml_obj = xml_obj.getparent()
            ns, _, tag = xml_obj.tag[1:].partition('}')
            if not name or not ns.startswith('http://www.cellml.org/cellml/'):
                msg = 'Target `{}` of variable `{}` is not a valid observable.'.format(sed_variable.target, sed_variable.id)
                raise ValueError(msg)
            if tag == 'model':
                break

        if attrib_target:
            names.insert(0, attrib_target)
        opencor_variable_names[sed_variable.id] = '/'.join(reversed(names))

    return opencor_variable_names


def validate_simulation(simulation):
    """ Validate a simulation

    Args:
        simulation (:obj:`UniformTimeCourseSimulation`): requested simulation

    Returns:
        :obj:`UniformTimeCourseSimulation`: simulation instructions for OpenCOR
    """
    number_of_steps = (
        simulation.output_end_time - simulation.initial_time
    ) / (
        simulation.output_end_time - simulation.output_start_time
    ) * simulation.number_of_steps
    output_start_time = simulation.initial_time

    if abs(number_of_steps - round(number_of_steps)) > 1e-8:
        msg = (
            'Number of steps must be an integer, not `{}`:'
            '\n  Initial time: {}'
            '\n  Output start time: {}'
            '\n  Output end time: {}'
            '\n  Number of steps (output start - end time) time: {}'
        ).format(
            number_of_steps, simulation.initial_time,
            simulation.output_start_time, simulation.output_end_time,
            simulation.number_of_steps,
        )
        raise NotImplementedError(msg)
    else:
        number_of_steps = round(number_of_steps)

    opencor_simulation = copy.deepcopy(simulation)
    opencor_simulation.number_of_steps = number_of_steps
    opencor_simulation.output_start_time = output_start_time

    return opencor_simulation


def get_opencor_algorithm(requested_alg, config=None):
    """ Get a possibly alternative algorithm that OpenCOR should execute

    Args:
        requested_alg (:obj:`Algorithm`): requested algorithm
        config (:obj:`Config`, optional): configuration

    Returns:
        :obj:`Algorithm`: possibly alternative algorithm that OpenCOR should execute
    """
    exec_alg = copy.deepcopy(requested_alg)

    algorithm_substitution_policy = get_algorithm_substitution_policy(config=config)
    exec_alg.kisao_id = get_preferred_substitute_algorithm_by_ids(
        requested_alg.kisao_id, KISAO_ALGORITHM_MAP.keys(),
        substitution_policy=algorithm_substitution_policy)

    if exec_alg.kisao_id == requested_alg.kisao_id:
        alg_specs = KISAO_ALGORITHM_MAP[exec_alg.kisao_id]
        params_specs = alg_specs['parameters']

        for change in list(exec_alg.changes):
            param_specs = params_specs.get(change.kisao_id, None)
            if param_specs:
                is_valid, change.new_value = get_opencor_parameter_value(
                    change.new_value, param_specs['type'], param_specs.get('enum', None))

                if not is_valid:
                    if (
                        ALGORITHM_SUBSTITUTION_POLICY_LEVELS[algorithm_substitution_policy]
                        > ALGORITHM_SUBSTITUTION_POLICY_LEVELS[AlgorithmSubstitutionPolicy.NONE]
                    ):
                        warn('Unsupported value `{}` of {}-valued algorithm parameter `{}` (`{}`) was ignored.'.format(
                            change.new_value, param_specs['type'].name, param_specs['name'], change.kisao_id), BioSimulatorsWarning)
                        exec_alg.changes.remove(change)

                    else:
                        msg = '`{}` (`{}`) must a {}, not `{}`.'.format(
                            param_specs['name'], change.kisao_id, param_specs['type'].name, change.new_value)
                        raise ValueError(msg)
            else:
                if (
                    ALGORITHM_SUBSTITUTION_POLICY_LEVELS[algorithm_substitution_policy]
                    > ALGORITHM_SUBSTITUTION_POLICY_LEVELS[AlgorithmSubstitutionPolicy.NONE]
                ):
                    warn('Unsupported algorithm parameter `{}` was ignored.'.format(
                        change.kisao_id), BioSimulatorsWarning)
                    exec_alg.changes.remove(change)

                else:
                    msg = '{} ({}) does not support parameter `{}`. {} support the following parameters:\n  {}'.format(
                        alg_specs['name'], alg_specs['kisao_id'], change.kisao_id, alg_specs['name'],
                        '\n  '.join(sorted('{}: {}'.format(param_kisao_id, param_specs['name'])
                                           for param_kisao_id, param_specs in params_specs.items()))
                    )
                    raise NotImplementedError(msg)

    else:
        exec_alg.changes = []

    return exec_alg


def get_opencor_parameter_value(value, value_type, enum_cls=None):
    """ Get the OpenCOR representation of a value of a parameter

    Args:
        value (:obj:`str`): string-encoded parameter value
        value_type (:obj:`ValueType`): expected type of the value
        enum_cls (:obj:`type`): allowed values of the parameter

    Returns:
        :obj:`tuple`:

            * :obj:`bool`: whether the value is valid
            * :obj:`str`: OpenCOR representation of a value of a parameter
    """
    if not validate_str_value(value, value_type):
        return False, None

    if enum_cls:
        try:
            return True, enum_cls[value].value
        except KeyError:
            pass

        try:
            return True, enum_cls[value.replace('KISAO:', 'KISAO_')].value
        except KeyError:
            pass

        try:
            return True, enum_cls(value).value
        except ValueError:
            pass

        return False, None

    else:
        return True, value


def build_opencor_sedml_doc(task, variables, include_data_generators=False):
    """ Create an OpenCOR-compatible SED-ML document for a task and its output variables

    Args:
        task (:obj:`Task`): SED task
        variables (:obj:`list` of :obj:`Variable`): SED variables
        include_data_generators (:obj:`bool`, optional): whether to export data generators

    Returns:
        :obj:`SedDocument`: SED document
    """
    doc = SedDocument()

    model_copy = copy.deepcopy(task.model)
    model_copy.id = 'model'
    model_copy.source = os.path.abspath(model_copy.source)
    doc.models.append(model_copy)

    sim_copy = copy.deepcopy(task.simulation)
    sim_copy.id = 'simulation1'
    doc.simulations.append(sim_copy)

    basic_task = Task(id='task1', model=model_copy, simulation=sim_copy)
    repeated_task = RepeatedTask(
        id='repeatedTask',
        range=VectorRange(id="once", values=[1]),
        sub_tasks=[
            SubTask(order=1, task=basic_task),
        ],
        reset_model_for_each_iteration=True,
    )
    repeated_task.ranges = [repeated_task.range]
    doc.tasks.append(basic_task)
    doc.tasks.append(repeated_task)

    if include_data_generators:
        for variable in variables:
            doc.data_generators.append(
                DataGenerator(
                    id='data_generator_' + variable.id,
                    variables=[
                        Variable(id=variable.id, target=variable.target, target_namespaces=variable.target_namespaces, task=repeated_task),
                    ],
                    math=variable.id,
                )
            )

    return doc


def save_task_to_opencor_sedml_file(task, variables, include_data_generators=False):
    """ Save a SED task to an OpenCOR-compatible SED-ML file

    Args:
        task (:obj:`Task`): SED task
        variables (:obj:`list` of :obj:`Variable`): SED variables
        include_data_generators (:obj:`bool`, optional): whether to export data generators

    Returns:
        :obj:`str`: path to SED-ML file for the SED document
    """
    doc = build_opencor_sedml_doc(task, variables, include_data_generators=include_data_generators)

    fid, sed_filename = tempfile.mkstemp(suffix='.sedml')
    os.close(fid)

    doc.models[0].source = os.path.relpath(doc.models[0].source, os.path.dirname(sed_filename))

    # use a mocked version because libCellML cannot be installed into the OpenCOR docker image
    with mock.patch.dict('sys.modules', libcellml=get_mock_libcellml()):
        SedmlSimulationWriter().run(doc, sed_filename, validate_models_with_languages=False)

    return sed_filename


def load_opencor_simulation(task, variables, include_data_generators=False):
    """ Load an OpenCOR simulation

    Args:
        task (:obj:`Task`): SED task
        variables (:obj:`list` of :obj:`Variable`): SED variables
        include_data_generators (:obj:`bool`, optional): whether to export data generators

    Returns:
        :obj:`PythonQt.private.SimulationSupport.Simulation`: OpenCOR simulation
    """
    # save SED-ML to a file
    filename = save_task_to_opencor_sedml_file(task, variables, include_data_generators=include_data_generators)

    # Read the SED-ML file
    try:
        opencor_sim = opencor.open_simulation(filename)
    finally:
        # clean up temporary SED-ML file
        os.remove(filename)

    validate_opencor_simulation(opencor_sim)

    return opencor_sim


def validate_opencor_simulation(sim):
    """ Validate an OpenCOR simulation

    Args:
        sim (:obj:`PythonQt.private.SimulationSupport.Simulation`): OpenCOR simulation)

    Raises:
        :obj:`ValueError`: if the simulation is invalid
    """
    if sim.hasBlockingIssues() or not sim.valid():
        msg = 'The task does not describe a valid simulation:\n\n  {}'.format(
            '\n\n  '.join(
                ''.join(lxml.etree.fromstring('<root>' + issue + '</root>').itertext())
                for issue in sim.issues()
            )
        )
        raise ValueError(msg)


def get_results_from_opencor_simulation(opencor_sim, sed_task, sed_variables, opencor_variable_names):
    """ Get the results of SED variables from an OpenCOR simulation

    Args:
        opencor_sim (:obj:`PythonQt.private.SimulationSupport.Simulation`): OpenCOR simulation
        sed_task (:obj:`Task`): requested SED task
        sed_variables (:obj:`list` of :obj:`Variable`): SED variables
        opencor_variable_names (:obj:`dict`): dictionary that maps the id of each SED variable to the name that OpenCOR uses to reference it)

    Returns:
        :obj:`VariableResults`: results of the SED variables
    """
    opencor_results = opencor_sim.results()
    opencor_voi_results = opencor_results.voi()
    opencor_states_results = opencor_results.states()
    opencor_rates_results = opencor_results.rates()
    opencor_constants_results = opencor_results.constants()
    opencor_algebraic_results = opencor_results.algebraic()

    sed_results = VariableResults()
    invalid_variables = []
    for sed_variable in sed_variables:
        opencor_name = opencor_variable_names[sed_variable.id]

        if opencor_name == opencor_voi_results.uri():
            sed_results[sed_variable.id] = opencor_voi_results.values()[-(sed_task.simulation.number_of_steps + 1):]

        elif opencor_name in opencor_states_results:
            sed_results[sed_variable.id] = opencor_states_results[opencor_name].values()[-(sed_task.simulation.number_of_steps + 1):]

        elif opencor_name in opencor_rates_results:
            sed_results[sed_variable.id] = opencor_rates_results[opencor_name].values()[-(sed_task.simulation.number_of_steps + 1):]

        elif opencor_name in opencor_constants_results:
            sed_results[sed_variable.id] = opencor_constants_results[opencor_name].values()[-(sed_task.simulation.number_of_steps + 1):]

        elif opencor_name in opencor_algebraic_results:
            sed_results[sed_variable.id] = opencor_algebraic_results[opencor_name].values()[-(sed_task.simulation.number_of_steps + 1):]

        else:
            invalid_variables.append('{}: {}'.format(sed_variable.id, sed_variable.target))

    if invalid_variables:
        msg = (
            'The target of each variable must be a valid observable. '
            'The targets of the following variables are not valid observables.\n  {}'
        ).format('\n  '.join(invalid_variables))
        raise ValueError(msg)

    return sed_results


def log_opencor_execution(task, log):
    """ Log information about how OpenCOR was used to execute the simulation

    Args:
        task (:obj:`Task`): SED task
        log (:obj:`TaskLog`): execution log
    """
    log.algorithm = task.simulation.algorithm.kisao_id
    log.simulator_details = {
        'method': 'OpenCOR.SimulationSupport.Simulation.run',
        'algorithmParameters': [
            {'kisaoID': change.kisao_id, 'value': change.new_value}
            for change in task.simulation.algorithm.changes
        ],
    }


def get_mock_libcellml():
    """ Get a mocked version of libCellML

    Returns:
        :obj:`mock.Mock`: mocked libcellml module
    """
    return mock.Mock(
        Parser=lambda: mock.Mock(
            parseModel=lambda: None,
            errorCount=lambda: 0,
            warningCount=lambda: 0,
        ),
        Validator=lambda: mock.Mock(
            validateModel=lambda model: None,
            errorCount=lambda: 0,
            warningCount=lambda: 0,
        ),
    )
