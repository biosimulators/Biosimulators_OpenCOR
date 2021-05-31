""" BioSimulators-compliant command-line interface to the `OpenCOR <https://opencor.ws/>`_ simulation program.

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-05-28
:Copyright: 2021, BioSimulators Team
:License: MIT
"""

from ._version import __version__
from .utils import get_opencor_version
from .core import exec_sedml_docs_in_combine_archive
from biosimulators_utils.simulator.cli import build_cli

App = build_cli('opencor', __version__,
                'OpenCOR', get_opencor_version(), 'https://opencor.ws',
                exec_sedml_docs_in_combine_archive)


def main():
    with App() as app:
        app.run()


if __name__ == "__main__":
    main()
