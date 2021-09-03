from ._version import __version__  # noqa: F401
# :obj:`str`: version

from .core import exec_sed_task, preprocess_sed_task, exec_sed_doc, exec_sedml_docs_in_combine_archive  # noqa: F401
import subprocess

__all__ = [
    '__version__',
    'get_simulator_version',
    'exec_sed_task',
    'preprocess_sed_task',
    'exec_sed_doc',
    'exec_sedml_docs_in_combine_archive',
]


def get_simulator_version():
    """ Get the version of OpenCOR

    Returns:
        :obj:`str`: version of OpenCOR
    """
    result = subprocess.run(['OpenCOR', '--version'],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            check=False)

    if result.returncode != 0:
        raise RuntimeError('The version of OpenCOR could not be retrieved:\n\n  {}'.format(
            result.stderr.decode().strip().replace('\n', '\n  ')))

    return result.stdout.decode().strip().replace('OpenCOR ', '')
