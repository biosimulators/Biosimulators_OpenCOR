""" Data model for OpenCOR algorithms and their parameters

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-05-28
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from biosimulators_utils.data_model import ValueType
import collections
import enum

__all__ = [
    'CvodeIntegrationMethod',
    'CvodeIterationType',
    'CvodeLinearSolver',
    'CvodePreconditioner',
    'KinsolLinearSolver',
    'KISAO_ALGORITHM_MAP',
]


class CvodeIntegrationMethod(str, enum.Enum):
    """ CVODE integration method """
    KISAO_0000288 = 'BDF'
    KISAO_0000280 = 'Adams-Moulton'


class CvodeIterationType(str, enum.Enum):
    """ CVODE iteration type  """
    KISAO_0000408 = 'Newton'
    KISAO_0000632 = 'Functional'  # only suitable for non-stiff systems


class CvodeLinearSolver(str, enum.Enum):
    """ CVODE linear solver """
    KISAO_0000625 = "Dense"  # dense direct solvers
    KISAO_0000626 = "Banded"  # band direct solvers
    KISAO_0000627 = "Diagonal"  # diagonal approximate Jacobian solver
    KISAO_0000353 = "GMRES"  # generalized minimal residual method
    KISAO_0000392 = "BiCGStab"  # Biconjugate gradient stabilized method
    KISAO_0000396 = "TFQMR"  # transpose-free quasi-minimal residual algorithm


class CvodePreconditioner(str, enum.Enum):
    """ CVODE preconditioner """
    KISAO_0000626 = 'Banded'
    KISAO_0000629 = 'None'


class KinsolLinearSolver(str, enum.Enum):
    """ KINSOL linear solver """
    KISAO_0000625 = "Dense"
    KISAO_0000626 = "Banded"
    KISAO_0000353 = "GMRES"
    KISAO_0000392 = "BiCGStab"
    KISAO_0000396 = "TFQMR"


KISAO_ALGORITHM_MAP = collections.OrderedDict([
    ('KISAO_0000019', {
        'kisao_id': 'KISAO_0000019',
        'name': 'CVODE',
        'parameters': {
            'KISAO_0000467': {
                'id': 'MaximumStepId',
                'name': 'maximum step',
                'type': ValueType.float,
                'default': 0.,
            },
            'KISAO_0000415': {
                'id': 'MaximumNumberOfStepsId',
                'name': 'maximum number of steps',
                'type': ValueType.integer,
                'default': 500,
            },
            'KISAO_0000475': {
                'id': 'IntegrationMethodId',
                'name': 'integration method',
                'type': ValueType.string,
                'default': CvodeIntegrationMethod.KISAO_0000288.name,
                'enum': CvodeIntegrationMethod,
            },
            'KISAO_0000476': {
                'id': 'IterationTypeId',
                'name': 'iteration type',
                'type': ValueType.string,
                'default': CvodeIterationType.KISAO_0000408.name,
                'enum': CvodeIterationType,
            },
            'KISAO_0000477': {
                'id': 'LinearSolverId',
                'name': 'linear solver',
                'type': ValueType.string,
                'default': CvodeLinearSolver.KISAO_0000625.name,
                'enum': CvodeLinearSolver,
            },
            'KISAO_0000478': {
                'id': 'PreconditionerId',
                'name': 'preconditioner',
                'type': ValueType.string,
                'default': CvodePreconditioner.KISAO_0000626.name,
                'enum': CvodePreconditioner,
            },
            'KISAO_0000479': {
                'id': 'UpperHalfBandwidthId',
                'name': 'upper half-bandwith',
                'type': ValueType.integer,
                'default': 0,
            },
            'KISAO_0000480': {
                'id': 'LowerHalfBandwidthId',
                'name': 'lower half-bandwith',
                'type': ValueType.integer,
                'default': 0,
            },
            'KISAO_0000209': {
                'id': 'RelativeToleranceId',
                'name': 'relative tolerance',
                'type': ValueType.float,
                'default': 1e-7,
            },
            'KISAO_0000211': {
                'id': 'AbsoluteToleranceId',
                'name': 'absolute tolerance',
                'type': ValueType.float,
                'default': 1e-7,
            },
            'KISAO_0000481': {
                'id': 'InterpolateSolutionId',
                'name': 'iterpolate solution',
                'type': ValueType.boolean,
                'default': True,
            },
        }
    }),
    ('KISAO_0000030', {
        'kisao_id': 'KISAO_0000030',
        'id': 'forward-euler',
        'name': 'Forward Euler method',
        'parameters': {
            'KISAO_0000483': {
                'id': 'step',
                'name': 'step',
                'type': ValueType.float,
                'default': 1.,
            },
        },
    }),
    ('KISAO_0000032', {
        'kisao_id': 'KISAO_0000032',
        'id': 'rk4',
        'name': 'Explicit fourth-order Runge-Kutta method',
        'parameters': {
            'KISAO_0000483': {
                'id': 'step',
                'name': 'step',
                'type': ValueType.float,
                'default': 1.,
            },
        },
    }),
    ('KISAO_0000381', {
        'kisao_id': 'KISAO_0000381',
        'id': 'rk2',
        'name': 'Second-order Runge-Kutta method',
        'parameters': {
            'KISAO_0000483': {
                'id': 'step',
                'name': 'step',
                'type': ValueType.float,
                'default': 1.,
            },
        },
    }),
    ('KISAO_0000301', {
        'kisao_id': 'KISAO_0000301',
        'id': 'heun',
        'name': 'Heun method',
        'parameters': {
            'KISAO_0000483': {
                'id': 'step',
                'name': 'step',
                'type': ValueType.float,
                'default': 1.,
            },
        },
    }),
    ('KISAO_0000282', {
        'kisao_id': 'KISAO_0000282',
        'id': 'kinsol',
        'name': 'KINSOL',
        'parameters': {
            'KISAO_0000486': {
                'id': 'MaximumNumberOfIterationsId',
                'name': 'maximum number of iterations',
                'type': ValueType.integer,
                'default': 200,
            },
            'KISAO_0000477': {
                'id': 'LinearSolverId',
                'name': 'linear solver',
                'type': ValueType.string,
                'default': KinsolLinearSolver.KISAO_0000625.name,
                "enum": KinsolLinearSolver,
            },
            'KISAO_0000479': {
                'id': 'UpperHalfBandwidthId',
                'name': 'upper half-bandwith',
                'type': ValueType.integer,
                'default': 0,
            },
            'KISAO_0000480': {
                'id': 'LowerHalfBandwidthId',
                'name': 'lower half-bandwith',
                'type': ValueType.integer,
                'default': 0,
            },
        },
    }),
])
