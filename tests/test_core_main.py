""" Tests of the command-line interface

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-05-28
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from biosimulators_opencor import __main__
from biosimulators_opencor import core
from biosimulators_opencor import utils
from biosimulators_opencor.data_model import KISAO_ALGORITHM_MAP
from biosimulators_utils.combine import data_model as combine_data_model
from biosimulators_utils.combine.io import CombineArchiveWriter
from biosimulators_utils.config import get_config
from biosimulators_utils.log.data_model import TaskLog
from biosimulators_utils.report import data_model as report_data_model
from biosimulators_utils.report.io import ReportReader
from biosimulators_utils.simulator.specs import gen_algorithms_from_specs
from biosimulators_utils.sedml import data_model as sedml_data_model
from biosimulators_utils.sedml.io import SedmlSimulationWriter
from unittest import mock
import datetime
import dateutil.tz
import numpy
import numpy.testing
import os
import shutil
import tempfile
import unittest


class TestCase(unittest.TestCase):
    DOCKER_IMAGE = 'ghcr.io/biosimulators/biosimulators_opencor/opencor:latest'
    NAMESPACES = {
        'cellml': 'http://www.cellml.org/cellml/1.0#',
    }

    def setUp(self):
        self.dirname = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dirname)

    def test_exec_sed_task(self):
        task, variables = self._get_simulation()
        log = TaskLog()
        results, log = core.exec_sed_task(task, variables, log=log)
        self._assert_variable_results(task, variables, results)

    def test_exec_sed_task_with_algebraic_variable(self):
        task, variables = self._get_simulation()
        task.model.source = os.path.abspath(os.path.join(os.path.dirname(__file__), 'fixtures', 'parabola_variant_dae_model.cellml'))
        variables[0].target = "/cellml:model/cellml:component[@name='main']/cellml:variable[@name='time']"
        variables.pop()
        log = TaskLog()
        results, log = core.exec_sed_task(task, variables, log=log)
        self._assert_variable_results(task, variables, results)

    def test_exec_sed_task_with_changes(self):
        task, _ = self._get_simulation()
        var_names = ['t', 'x', 'y', 'z']
        variables = []
        for var_name in var_names:
            task.model.changes.append(sedml_data_model.ModelAttributeChange(
                target="/cellml:model/cellml:component[@name='main']/cellml:variable[@name='{}']/@initial_value".format(var_name),
                target_namespaces=self.NAMESPACES,
                new_value=None
            ))
            variables.append(sedml_data_model.Variable(
                id=var_name,
                target="/cellml:model/cellml:component[@name='main']/cellml:variable[@name='{}']".format(var_name),
                target_namespaces=self.NAMESPACES,
                task=task,
            ))
        preprocessed_task = core.preprocess_sed_task(task, variables)

        task.model.changes = []
        results, _ = core.exec_sed_task(task, variables, preprocessed_task=preprocessed_task)
        self.assertEqual(
            results['x'][0:int(task.simulation.number_of_steps / 2) + 1].shape,
            results['x'][-(int(task.simulation.number_of_steps / 2) + 1):].shape,
        )
        with self.assertRaises(AssertionError):
            numpy.testing.assert_allclose(
                results['x'][0:int(task.simulation.number_of_steps / 2) + 1],
                results['x'][-(int(task.simulation.number_of_steps / 2) + 1):],
            )

        task.simulation.output_end_time = task.simulation.output_end_time / 2
        task.simulation.number_of_steps = int(task.simulation.number_of_steps / 2)

        results2, _ = core.exec_sed_task(task, variables, preprocessed_task=preprocessed_task)
        numpy.testing.assert_allclose(
            results2['x'],
            results['x'][0:task.simulation.number_of_steps + 1],
        )

        task.simulation.initial_time += task.simulation.output_end_time
        task.simulation.output_start_time += task.simulation.output_end_time
        task.simulation.output_end_time += task.simulation.output_end_time
        for var_name in var_names:
            task.model.changes.append(sedml_data_model.ModelAttributeChange(
                target="/cellml:model/cellml:component[@name='main']/cellml:variable[@name='{}']/@initial_value".format(var_name),
                target_namespaces=self.NAMESPACES,
                new_value=results2[var_name][-1],
            ))

        results3, _ = core.exec_sed_task(task, variables, preprocessed_task=preprocessed_task)

        numpy.testing.assert_allclose(
            results3['x'],
            results['x'][-(task.simulation.number_of_steps + 1):],
            rtol=5e-5,
        )

    def test_exec_sedml_docs_in_combine_archive(self):
        doc, archive_filename = self._build_combine_archive()

        out_dir = os.path.join(self.dirname, 'out')

        config = get_config()
        config.REPORT_FORMATS = [report_data_model.ReportFormat.h5]
        config.BUNDLE_OUTPUTS = True
        config.KEEP_INDIVIDUAL_OUTPUTS = True

        _, log = core.exec_sedml_docs_in_combine_archive(archive_filename, out_dir, config=config)
        if log.exception:
            raise log.exception

        self._assert_combine_archive_outputs(doc, out_dir)

    def test_exec_sedml_docs_in_combine_archive_with_all_algorithms(self):
        for alg in gen_algorithms_from_specs(os.path.join(os.path.dirname(__file__), '..', 'biosimulators.json')).values():
            alg_props = KISAO_ALGORITHM_MAP[alg.kisao_id]
            alg.changes = []
            for param_kisao_id, param_props in alg_props.parameters.items():
                alg.changes.append(sedml_data_model.AlgorithmParameterChange(
                    kisao_id=param_kisao_id,
                    new_value=str(param_props['default']),
                ))
            doc, archive_filename = self._build_combine_archive(algorithm=alg)

            out_dir = os.path.join(self.dirname, 'out')

            config = get_config()
            config.REPORT_FORMATS = [report_data_model.ReportFormat.h5]
            config.BUNDLE_OUTPUTS = True
            config.KEEP_INDIVIDUAL_OUTPUTS = True

            _, log = core.exec_sedml_docs_in_combine_archive(archive_filename, out_dir, config=config)
            if log.exception:
                raise log.exception

            self._assert_combine_archive_outputs(doc, out_dir)

    def _get_simulation(self, algorithm=None):
        model_source = os.path.abspath(os.path.join(os.path.dirname(__file__), 'fixtures', 'lorenz.cellml'))

        if algorithm is None:
            algorithm = sedml_data_model.Algorithm(
                kisao_id='KISAO_0000019',
                changes=[
                    sedml_data_model.AlgorithmParameterChange(kisao_id='KISAO_0000467', new_value='1.0'),
                    sedml_data_model.AlgorithmParameterChange(kisao_id='KISAO_0000475', new_value='BDF'),
                ],
            )

        task = sedml_data_model.Task(
            model=sedml_data_model.Model(source=model_source, language=sedml_data_model.ModelLanguage.CellML.value),
            simulation=sedml_data_model.UniformTimeCourseSimulation(
                initial_time=0.,
                output_start_time=0.,
                output_end_time=10.,
                number_of_steps=10,
                algorithm=algorithm,
            ),
        )

        variables = [
            sedml_data_model.Variable(
                id='t',
                target="/cellml:model/cellml:component[@name='main']/cellml:variable[@name='t']",
                target_namespaces=self.NAMESPACES,
                task=task,
            ),
            sedml_data_model.Variable(
                id='x',
                target="/cellml:model/cellml:component[@name='main']/cellml:variable[@name='x']",
                target_namespaces=self.NAMESPACES,
                task=task,
            ),
            sedml_data_model.Variable(
                id='x_prime',
                target="/cellml:model/cellml:component[@name='main']/cellml:variable[@name='x']/@prime",
                target_namespaces=self.NAMESPACES,
                task=task,
            ),
        ]

        return task, variables

    def _build_sed_doc(self, algorithm=None):
        task, variables = self._get_simulation(algorithm=algorithm)

        doc = sedml_data_model.SedDocument()

        model = task.model
        model.id = 'model1'
        doc.models.append(model)

        sim = task.simulation
        sim.id = 'simulation'
        doc.simulations.append(sim)

        task.id = 'task'
        doc.tasks.append(task)

        report = sedml_data_model.Report(id='report1')
        doc.outputs.append(report)
        for variable in variables:
            data_gen = sedml_data_model.DataGenerator(
                id='data_generator_' + variable.id,
                variables=[
                    variable,
                ],
                math=variable.id,
            )
            doc.data_generators.append(data_gen)
            report.data_sets.append(sedml_data_model.DataSet(id='data_set_' + variable.id, label=variable.id, data_generator=data_gen))

        return doc

    def _build_combine_archive(self, algorithm=None):
        doc = self._build_sed_doc(algorithm=algorithm)

        archive_dirname = os.path.join(self.dirname, 'archive')
        if not os.path.isdir(archive_dirname):
            os.mkdir(archive_dirname)

        model_filename = os.path.join(archive_dirname, 'model1.cellml')
        shutil.copyfile(doc.models[0].source, model_filename)
        doc.models[0].source = 'model1.cellml'

        sim_filename = os.path.join(archive_dirname, 'simulation.sedml')
        with mock.patch.dict('sys.modules', libcellml=utils.get_mock_libcellml()):
            SedmlSimulationWriter().run(doc, sim_filename)

        archive = combine_data_model.CombineArchive(
            contents=[
                combine_data_model.CombineArchiveContent(
                    'model1.cellml', combine_data_model.CombineArchiveContentFormat.CellML.value),
                combine_data_model.CombineArchiveContent(
                    'simulation.sedml', combine_data_model.CombineArchiveContentFormat.SED_ML.value),
            ],
        )
        archive_filename = os.path.join(self.dirname, 'archive.omex')
        CombineArchiveWriter().run(archive, archive_dirname, archive_filename)

        return (doc, archive_filename)

    def _assert_variable_results(self, task, variables, results):
        sim = task.simulation
        self.assertTrue(set(results.keys()), set([var.id for var in variables]))
        numpy.testing.assert_allclose(results['t'], numpy.linspace(sim.output_start_time, sim.output_end_time, sim.number_of_points + 1))
        for result in results.values():
            self.assertEqual(result.shape, (sim.number_of_points + 1,))
            self.assertFalse(numpy.any(numpy.isnan(result)))

    def _assert_combine_archive_outputs(self, doc, out_dir):
        sim = doc.simulations[0]
        report = doc.outputs[0]

        # check HDF report
        report_results = ReportReader().run(report, out_dir, 'simulation.sedml/report1', format=report_data_model.ReportFormat.h5)

        self.assertEqual(sorted(report_results.keys()), sorted([d.id for d in report.data_sets]))

        numpy.testing.assert_allclose(report_results['data_set_t'], numpy.linspace(
            sim.output_start_time, sim.output_end_time, sim.number_of_points + 1))
        for result in report_results.values():
            self.assertEqual(result.shape, (sim.number_of_points + 1,))
            self.assertFalse(numpy.any(numpy.isnan(result)))

    def test_raw_cli(self):
        with mock.patch('sys.argv', ['', '--help']):
            with self.assertRaises(SystemExit) as context:
                __main__.main()
                self.assertRegex(context.Exception, 'usage: ')

    def test_exec_sedml_docs_in_combine_archive_with_cli(self):
        doc, archive_filename = self._build_combine_archive()
        out_dir = os.path.join(self.dirname, 'out')
        env = self._get_combine_archive_exec_env()

        with mock.patch.dict(os.environ, env):
            with __main__.App(argv=['-i', archive_filename, '-o', out_dir]) as app:
                app.run()

        self._assert_combine_archive_outputs(doc, out_dir)

    def _get_combine_archive_exec_env(self):
        return {
            'REPORT_FORMATS': 'h5'
        }
