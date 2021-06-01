""" Tests of the data model

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-05-30
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from biosimulators_opencor import data_model
from biosimulators_utils.data_model import ValueType
from biosimulators_utils.utils.core import parse_value
import json
import os
import unittest


class DataModelTestCase(unittest.TestCase):
    def test(self):
        self.assertEqual(data_model.CvodeIntegrationMethod.KISAO_0000288.value, 'BDF')
        self.assertEqual(data_model.CvodeIterationType.KISAO_0000408.value, 'Newton')
        self.assertEqual(data_model.CvodeLinearSolver.KISAO_0000625.value, 'Dense')
        self.assertEqual(data_model.CvodePreconditioner.KISAO_0000629.value, 'None')
        self.assertEqual(data_model.KinsolLinearSolver.KISAO_0000625.value, 'Dense')
        self.assertEqual(data_model.KISAO_ALGORITHM_MAP['KISAO_0000019']['kisao_id'], 'KISAO_0000019')

    def test_consistent_with_specs(self):
        with open(os.path.join(os.path.dirname(__file__), '..', 'biosimulators.json'), 'r') as file:
            specs = json.load(file)

        self.assertEqual(set(data_model.KISAO_ALGORITHM_MAP.keys()), set(alg_specs['kisaoId']['id'] for alg_specs in specs['algorithms']))

        for alg_specs in specs['algorithms']:
            alg_props = data_model.KISAO_ALGORITHM_MAP[alg_specs['kisaoId']['id']]

            self.assertEqual(set(alg_props['parameters'].keys()),
                             set(param_specs['kisaoId']['id'] for param_specs in alg_specs['parameters']))

            for param_specs in alg_specs['parameters']:
                param_props = alg_props['parameters'][param_specs['kisaoId']['id']]
                if param_specs['type'] == 'kisaoId':
                    self.assertEqual(param_props['type'].name, 'string')
                else:
                    self.assertEqual(param_props['type'].name, param_specs['type'])

                if param_props['type'] == ValueType.float and param_specs['value'] is None and param_props['default'] == 0:
                    pass
                elif param_specs['type'] == 'kisaoId' and param_specs['value'] == param_props['default']:
                    pass
                else:
                    self.assertEqual(param_props['default'], parse_value(param_specs['value'], param_props['type']))

                specs_range = param_specs['recommendedRange']
                if specs_range is not None:
                    specs_range = set(specs_range)
                props_enum = param_props.get('enum', None)
                if props_enum:
                    props_range = set(props_enum.__members__.keys())
                else:
                    props_range = None
                self.assertEqual(props_range, specs_range)
