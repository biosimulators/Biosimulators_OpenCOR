from biosimulators_opencor import get_simulator_version
from biosimulators_opencor import utils
from biosimulators_opencor.data_model import KISAO_ALGORITHM_MAP, CvodeIterationType, CvodeIntegrationMethod
from biosimulators_utils.log.data_model import TaskLog
from biosimulators_utils.sedml.data_model import (SedDocument, Model, ModelLanguage, UniformTimeCourseSimulation, Task,
                                                  RepeatedTask, VectorRange, SubTask,
                                                  Algorithm, AlgorithmParameterChange, DataGenerator, Variable, Symbol)
from biosimulators_utils.sedml.io import SedmlSimulationReader, SedmlSimulationWriter
from biosimulators_utils.warnings import BioSimulatorsWarning
from kisao.exceptions import AlgorithmCannotBeSubstitutedException
from kisao.warnings import AlgorithmSubstitutedWarning
from unittest import mock
import copy
import lxml.etree
import numpy
import numpy.testing
import opencor
import os
import tempfile
import unittest


class TestCase(unittest.TestCase):
    NAMESPACES = {
        None: 'http://sed-ml.org/sed-ml/level1/version3',
        'cellml': 'http://www.cellml.org/cellml/1.0#',
    }

    def test_get_simulator_version(self):
        version = get_simulator_version()
        self.assertIsInstance(version, str)
        self.assertNotEqual(version, '')
        self.assertNotIn('\n', version)

        with self.assertRaises(RuntimeError):
            with mock.patch('subprocess.run', return_value=mock.Mock(returncode=1, stderr=mock.Mock(decode=lambda: 'error'))):
                get_simulator_version()

    def test_get_opencor_parameter_value(self):
        param_specs = KISAO_ALGORITHM_MAP['KISAO_0000019']['parameters']

        self.assertEqual(utils.get_opencor_parameter_value('1.0', param_specs['KISAO_0000467']['type'], None), (True, '1.0'))
        self.assertEqual(utils.get_opencor_parameter_value('1', param_specs['KISAO_0000467']['type'], None), (True, '1'))
        self.assertEqual(utils.get_opencor_parameter_value('1e-1', param_specs['KISAO_0000467']['type'], None), (True, '1e-1'))
        self.assertEqual(utils.get_opencor_parameter_value('x', param_specs['KISAO_0000467']['type'], None), (False, None))

        self.assertEqual(utils.get_opencor_parameter_value('1', param_specs['KISAO_0000415']['type'], None), (True, '1'))
        self.assertEqual(utils.get_opencor_parameter_value('1.0', param_specs['KISAO_0000415']['type'], None), (False, None))
        self.assertEqual(utils.get_opencor_parameter_value('x', param_specs['KISAO_0000415']['type'], None), (False, None))

        self.assertEqual(utils.get_opencor_parameter_value('KISAO_0000408',
                                                           param_specs['KISAO_0000476']['type'],
                                                           CvodeIterationType),
                         (True, 'Newton'))
        self.assertEqual(utils.get_opencor_parameter_value('KISAO:0000408',
                                                           param_specs['KISAO_0000476']['type'],
                                                           CvodeIterationType),
                         (True, 'Newton'))
        self.assertEqual(utils.get_opencor_parameter_value('Newton',
                                                           param_specs['KISAO_0000476']['type'],
                                                           CvodeIterationType),
                         (True, 'Newton'))
        self.assertEqual(utils.get_opencor_parameter_value('x', param_specs['KISAO_0000476']['type'], CvodeIterationType), (False, None))

        self.assertEqual(utils.get_opencor_parameter_value('KISAO_0000288',
                                                           param_specs['KISAO_0000475']['type'],
                                                           CvodeIntegrationMethod),
                         (True, 'BDF'))
        self.assertEqual(utils.get_opencor_parameter_value('KISAO:0000288',
                                                           param_specs['KISAO_0000475']['type'],
                                                           CvodeIntegrationMethod),
                         (True, 'BDF'))
        self.assertEqual(utils.get_opencor_parameter_value('BDF',
                                                           param_specs['KISAO_0000475']['type'],
                                                           CvodeIntegrationMethod),
                         (True, 'BDF'))
        self.assertEqual(utils.get_opencor_parameter_value(
            'x', param_specs['KISAO_0000475']['type'], CvodeIntegrationMethod), (False, None))

    def test_get_opencor_algorithm(self):
        alg = Algorithm(kisao_id='KISAO_0000019', changes=[
            AlgorithmParameterChange(kisao_id='KISAO_0000467', new_value='1.0'),
            AlgorithmParameterChange(kisao_id='KISAO_0000415', new_value='200'),
            AlgorithmParameterChange(kisao_id='KISAO_0000476', new_value='Newton'),
            AlgorithmParameterChange(kisao_id='KISAO_0000475', new_value='KISAO_0000288'),
        ])
        with mock.patch.dict('os.environ', {'ALGORITHM_SUBSTITUTION_POLICY': 'NONE'}):
            actual_alg = utils.get_opencor_algorithm(alg)
        self.assertTrue(actual_alg.is_equal(Algorithm(kisao_id='KISAO_0000019', changes=[
            AlgorithmParameterChange(kisao_id='KISAO_0000467', new_value='1.0'),
            AlgorithmParameterChange(kisao_id='KISAO_0000415', new_value='200'),
            AlgorithmParameterChange(kisao_id='KISAO_0000476', new_value='Newton'),
            AlgorithmParameterChange(kisao_id='KISAO_0000475', new_value='BDF'),
        ])))

        alg = Algorithm(kisao_id='KISAO_0000019', changes=[
            AlgorithmParameterChange(kisao_id='KISAO_0000467', new_value='x'),
        ])
        with mock.patch.dict('os.environ', {'ALGORITHM_SUBSTITUTION_POLICY': 'NONE'}):
            with self.assertRaises(ValueError):
                utils.get_opencor_algorithm(alg)
        with mock.patch.dict('os.environ', {'ALGORITHM_SUBSTITUTION_POLICY': 'SIMILAR_VARIABLES'}):
            with self.assertWarns(BioSimulatorsWarning):
                actual_alg = utils.get_opencor_algorithm(alg)
        self.assertTrue(actual_alg.is_equal(Algorithm(kisao_id='KISAO_0000019', changes=[])))

        alg = Algorithm(kisao_id='KISAO_0000019', changes=[
            AlgorithmParameterChange(kisao_id='KISAO_0000488', new_value='x'),
        ])
        with mock.patch.dict('os.environ', {'ALGORITHM_SUBSTITUTION_POLICY': 'NONE'}):
            with self.assertRaises(NotImplementedError):
                utils.get_opencor_algorithm(alg)
        with mock.patch.dict('os.environ', {'ALGORITHM_SUBSTITUTION_POLICY': 'SIMILAR_VARIABLES'}):
            with self.assertWarns(BioSimulatorsWarning):
                actual_alg = utils.get_opencor_algorithm(alg)
        self.assertTrue(actual_alg.is_equal(Algorithm(kisao_id='KISAO_0000019', changes=[])))

        alg = Algorithm(kisao_id='KISAO_0000560', changes=[
            AlgorithmParameterChange(kisao_id='KISAO_0000467', new_value='1.0'),
        ])
        with mock.patch.dict('os.environ', {'ALGORITHM_SUBSTITUTION_POLICY': 'NONE'}):
            with self.assertRaises(AlgorithmCannotBeSubstitutedException):
                utils.get_opencor_algorithm(alg)
        with mock.patch.dict('os.environ', {'ALGORITHM_SUBSTITUTION_POLICY': 'SIMILAR_VARIABLES'}):
            with self.assertWarns(AlgorithmSubstitutedWarning):
                actual_alg = utils.get_opencor_algorithm(alg)
        self.assertTrue(actual_alg.is_equal(Algorithm(kisao_id='KISAO_0000019', changes=[])))

        alg = Algorithm(kisao_id='KISAO_0000029', changes=[])
        with mock.patch.dict('os.environ', {'ALGORITHM_SUBSTITUTION_POLICY': 'NONE'}):
            with self.assertRaises(AlgorithmCannotBeSubstitutedException):
                utils.get_opencor_algorithm(alg)
        with mock.patch.dict('os.environ', {'ALGORITHM_SUBSTITUTION_POLICY': 'SIMILAR_VARIABLES'}):
            with self.assertRaises(AlgorithmCannotBeSubstitutedException):
                utils.get_opencor_algorithm(alg)

    def test_validate_variable_xpaths(self):
        task, variables = self._get_simulation()
        model_etree = lxml.etree.parse(task.model.source)
        var_names = utils.validate_variable_xpaths(variables, model_etree)
        self.assertEqual(var_names, {
            't': 'main/t',
            'sigma': 'main/sigma',
            'x': 'main/x',
            'x_prime': 'main/x/prime',
        })

        task, variables = self._get_simulation()
        variables[0].target = "/cellml:model/cellml:component[@name='main']/cellml:variable[@name='undefined']"
        with self.assertRaisesRegex(ValueError, 'does not match any'):
            utils.validate_variable_xpaths(variables, model_etree)

        task, variables = self._get_simulation()
        variables[0].target = "/cellml:model/cellml:component[@name='main']/cellml:variable"
        with self.assertRaisesRegex(ValueError, 'matches multiple'):
            utils.validate_variable_xpaths(variables, model_etree)

        task, variables = self._get_simulation()
        variables[0].target = "/cellml:model/cellml:component[@name='main']/mathml:math"
        variables[0].target_namespaces['mathml'] = 'http://www.w3.org/1998/Math/MathML'
        with self.assertRaisesRegex(ValueError, 'not a valid observable'):
            utils.validate_variable_xpaths(variables, model_etree)

        task, variables = self._get_simulation()
        variables = [
            Variable(
                id='var',
                symbol=Symbol.time.value,
                task=task,
            )
        ]
        with self.assertRaisesRegex(NotImplementedError, 'Symbols are not supported.'):
            utils.validate_variable_xpaths(variables, model_etree)

    def test_validate_task(self):
        task, variables = self._get_simulation()
        actual_task, model_etree, opencor_variable_names = utils.validate_task(task, variables)
        self.assertEqual(opencor_variable_names, {
            't': 'main/t',
            'sigma': 'main/sigma',
            'x': 'main/x',
            'x_prime': 'main/x/prime',
        })

        task, variables = self._get_simulation()
        task.simulation.output_start_time = 5.
        utils.validate_task(task, variables)

        task, variables = self._get_simulation()
        task.simulation.output_start_time = 5.1
        with self.assertRaisesRegex(NotImplementedError, 'Number of steps must be an integer'):
            utils.validate_task(task, variables)

        task, variables = self._get_simulation()
        variables[0].task = None
        with self.assertRaisesRegex(ValueError, 'Variable must reference a task'):
            utils.validate_task(task, variables)

        task, variables = self._get_simulation()
        variables[0].target = 'undefined'
        with self.assertRaisesRegex(ValueError, 'must reference unique observables'):
            utils.validate_task(task, variables)

        task, variables = self._get_simulation()
        task.simulation.algorithm.kisao_id = 'KISAO_0000560'
        with mock.patch.dict('os.environ', {'ALGORITHM_SUBSTITUTION_POLICY': 'NONE'}):
            with self.assertRaises(AlgorithmCannotBeSubstitutedException):
                utils.validate_task(task, variables)

        task, variables = self._get_simulation()
        task.simulation.algorithm.kisao_id = 'KISAO_0000560'
        with mock.patch.dict('os.environ', {'ALGORITHM_SUBSTITUTION_POLICY': 'SIMILAR_VARIABLES'}):
            utils.validate_task(task, variables)

    def test_save_task_to_opencor_sedml_file(self):
        task, variables = self._get_simulation()

        expected_doc = copy.deepcopy(SedDocument(
            models=[task.model],
            simulations=[task.simulation],
            tasks=[
                task,
                RepeatedTask(
                    id='repeatedTask',
                    range=VectorRange(id='once', values=[1]),
                    sub_tasks=[
                        SubTask(order=1, task=task),
                    ],
                    reset_model_for_each_iteration=True,
                )
            ],
            data_generators=[
                DataGenerator(id='data_generator_t', variables=[variables[0]], math=variables[0].id),
                DataGenerator(id='data_generator_x', variables=[variables[1]], math=variables[1].id),
                DataGenerator(id='data_generator_x_prime', variables=[variables[2]], math=variables[2].id),
            ],
        ))
        expected_doc.models[0].id = 'model'
        expected_doc.simulations[0].id = 'simulation1'
        expected_doc.tasks[0].id = 'task1'
        expected_doc.tasks[1].ranges = [expected_doc.tasks[1].range]
        for data_generator in expected_doc.data_generators:
            data_generator.variables[0].task = expected_doc.tasks[1]

        doc = utils.build_opencor_sedml_doc(task, variables, include_data_generators=True)
        self.assertTrue(doc.is_equal(expected_doc))

        filename = utils.save_task_to_opencor_sedml_file(task, variables, include_data_generators=True)
        with mock.patch.dict('sys.modules', libcellml=utils.get_mock_libcellml()):
            doc = SedmlSimulationReader().run(filename, validate_models_with_languages=False)
        expected_doc.models[0].source = os.path.relpath(expected_doc.models[0].source, os.path.dirname(filename))
        self.assertTrue(doc.is_equal(expected_doc))

    def test_load_opencor_simulation(self):
        task, variables = self._get_simulation()
        doc = utils.build_opencor_sedml_doc(task, variables)
        fid, sed_filename = tempfile.mkstemp(suffix='.sedml')
        os.close(fid)
        with mock.patch.dict('sys.modules', libcellml=utils.get_mock_libcellml()):
            SedmlSimulationWriter().run(doc, sed_filename)

        sim = opencor.open_simulation(sed_filename)
        os.remove(sed_filename)
        with self.assertRaises(ValueError):
            utils.validate_opencor_simulation(sim)

    @unittest.skip('causes segmentation fault')
    def test_load_opencor_simulation_error_handling_unsupported_algorithm(self):
        task, variables = self._get_simulation()
        task.simulation.algorithm.kisao_id = 'KISAO_0000029'
        task.simulation.algorithm.changes = []
        utils.load_opencor_simulation(task, variables)

    @unittest.skip('causes segmentation fault')
    def test_load_opencor_simulation_error_handling_unsupported_algorithm_parameter(self):
        task, variables = self._get_simulation()
        task.simulation.algorithm.changes.append(
            AlgorithmParameterChange(kisao_id='KISAO_0000219', new_value='12'),
        )
        utils.load_opencor_simulation(task, variables)

    @unittest.expectedFailure
    def test_load_opencor_simulation_error_handling_unsupported_algorithm_parameter_value(self):
        task, variables = self._get_simulation()
        task.simulation.algorithm.changes[1].value = 'undefined'
        with self.assertRaises(Exception):
            utils.load_opencor_simulation(task, variables)

    def test_get_results_from_opencor_simulation(self):
        filename = os.path.abspath(os.path.join(os.path.dirname(__file__), 'fixtures', 'lorenz.sedml'))
        task, variables = self._get_simulation()
        model_etree = lxml.etree.parse(task.model.source)

        sim = task.simulation
        sim.initial_time = 0.
        sim.output_start_time = 0.
        sim.output_end_time = 50.
        sim.number_of_steps = 50000
        variable_names = utils.validate_variable_xpaths(variables, model_etree)
        opencor_sim = opencor.open_simulation(filename)
        opencor_sim.run()
        results = utils.get_results_from_opencor_simulation(opencor_sim, task, variables, variable_names)
        numpy.testing.assert_allclose(results['t'], numpy.linspace(sim.initial_time, sim.output_end_time, sim.number_of_steps + 1))
        for result in results.values():
            self.assertEqual(result.shape, (sim.number_of_steps + 1,))
            self.assertFalse(numpy.any(numpy.isnan(result)))

        # generated SED-ML file
        task, variables = self._get_simulation()
        variable_names = utils.validate_variable_xpaths(variables, model_etree)
        sim = task.simulation
        opencor_sim = utils.load_opencor_simulation(task, variables)
        opencor_sim.run()
        results = utils.get_results_from_opencor_simulation(opencor_sim, task, variables, variable_names)
        numpy.testing.assert_allclose(results['t'], numpy.linspace(sim.output_start_time, sim.output_end_time, sim.number_of_steps + 1))
        for result in results.values():
            self.assertEqual(result.shape, (sim.number_of_steps + 1,))
            self.assertFalse(numpy.any(numpy.isnan(result)))

    def test_get_results_from_opencor_simulation_non_zero_initial_time(self):
        task, variables = self._get_simulation()
        task.simulation.initial_time = 5.
        task.simulation.output_start_time = 5.
        model_etree = lxml.etree.parse(task.model.source)
        variable_names = utils.validate_variable_xpaths(variables, model_etree)
        sim = task.simulation
        opencor_sim = utils.load_opencor_simulation(task, variables)
        opencor_sim.run()
        results = utils.get_results_from_opencor_simulation(opencor_sim, task, variables, variable_names)
        numpy.testing.assert_allclose(results['t'], numpy.linspace(sim.output_start_time, sim.output_end_time, sim.number_of_steps + 1))
        for result in results.values():
            self.assertEqual(result.shape, (sim.number_of_steps + 1,))
            self.assertFalse(numpy.any(numpy.isnan(result)))

    @unittest.skip('causes segmentation fault')
    def test_get_results_from_opencor_simulation_output_start_time_not_equal_initial_time(self):
        task, variables = self._get_simulation()
        task.simulation.initial_time = 0.
        task.simulation.output_start_time = 5.
        model_etree = lxml.etree.parse(task.model.source)
        variable_names = utils.validate_variable_xpaths(variables, model_etree)
        sim = task.simulation
        opencor_sim = utils.load_opencor_simulation(task, variables)
        opencor_sim.run()
        results = utils.get_results_from_opencor_simulation(opencor_sim, task, variables, variable_names)
        numpy.testing.assert_allclose(results['t'], numpy.linspace(sim.output_start_time, sim.output_end_time, sim.number_of_steps + 1))
        for result in results.values():
            self.assertEqual(result.shape, (sim.number_of_steps + 1,))
            self.assertFalse(numpy.any(numpy.isnan(result)))

    def test_get_results_from_opencor_simulation_invalid_observable(self):
        task, variables = self._get_simulation()
        model_etree = lxml.etree.parse(task.model.source)
        variable_names = utils.validate_variable_xpaths(variables, model_etree)
        opencor_sim = utils.load_opencor_simulation(task, variables)
        opencor_sim.run()
        variable_names['x'] = 'main/undefined'
        with self.assertRaisesRegex(ValueError, 'must be a valid observable'):
            utils.get_results_from_opencor_simulation(opencor_sim, task, variables, variable_names)

    def _get_simulation(self):
        model_source = os.path.abspath(os.path.join(os.path.dirname(__file__), 'fixtures', 'lorenz.cellml'))

        task = Task(
            model=Model(source=model_source, language=ModelLanguage.CellML.value),
            simulation=UniformTimeCourseSimulation(
                initial_time=0.,
                output_start_time=0.,
                output_end_time=10.,
                number_of_steps=10,
                algorithm=Algorithm(
                    kisao_id='KISAO_0000019',
                    changes=[
                        AlgorithmParameterChange(kisao_id='KISAO_0000467', new_value='1.0'),
                        AlgorithmParameterChange(kisao_id='KISAO_0000475', new_value='BDF'),
                    ],
                )
            ),
        )

        variables = [
            Variable(
                id='t',
                target="/cellml:model/cellml:component[@name='main']/cellml:variable[@name='t']",
                target_namespaces=self.NAMESPACES,
                task=task,
            ),
            Variable(
                id='sigma',
                target="/cellml:model/cellml:component[@name='main']/cellml:variable[@name='sigma']",
                target_namespaces=self.NAMESPACES,
                task=task,
            ),
            Variable(
                id='x',
                target="/cellml:model/cellml:component[@name='main']/cellml:variable[@name='x']",
                target_namespaces=self.NAMESPACES,
                task=task,
            ),
            Variable(
                id='x_prime',
                target="/cellml:model/cellml:component[@name='main']/cellml:variable[@name='x']/@prime",
                target_namespaces=self.NAMESPACES,
                task=task,
            ),
        ]

        return task, variables

    def test_log_opencor_execution(self):
        # supported algorithm
        task, _ = self._get_simulation()

        log = TaskLog()
        utils.log_opencor_execution(task, log)

        self.assertEqual(log.algorithm, 'KISAO_0000019')
        self.assertEqual(log.simulator_details['algorithmParameters'], [
            {'kisaoID': 'KISAO_0000467', 'value': '1.0'},
            {'kisaoID': 'KISAO_0000475', 'value': 'BDF'},
        ])

        # alternative algorithm
        task, _ = self._get_simulation()
        task.simulation.algorithm.kisao_id = 'KISAO_0000560'
        with mock.patch.dict('os.environ', {'ALGORITHM_SUBSTITUTION_POLICY': 'SIMILAR_VARIABLES'}):
            task.simulation.algorithm = utils.get_opencor_algorithm(task.simulation.algorithm)

        log = TaskLog()
        utils.log_opencor_execution(task, log)

        self.assertEqual(log.algorithm, 'KISAO_0000019')
        self.assertEqual(log.simulator_details['algorithmParameters'], [])
