[![Latest release](https://img.shields.io/github/v/tag/biosimulators/Biosimulators_OpenCOR)](https://github.com/biosimulations/Biosimulators_OpenCOR/releases)
[![PyPI](https://img.shields.io/pypi/v/biosimulators_opencor)](https://pypi.org/project/biosimulators_opencor/)
[![CI status](https://github.com/biosimulators/Biosimulators_OpenCOR/workflows/Continuous%20integration/badge.svg)](https://github.com/biosimulators/Biosimulators_OpenCOR/actions?query=workflow%3A%22Continuous+integration%22)
[![Test coverage](https://codecov.io/gh/biosimulators/Biosimulators_OpenCOR/branch/dev/graph/badge.svg)](https://codecov.io/gh/biosimulators/Biosimulators_OpenCOR)

# BioSimulators-OpenCOR
BioSimulators-compliant command-line interface and Docker image for the [OpenCOR](https://opencor.ws/) simulation program.

This command-line interface and Docker image enable users to use OpenCOR to execute [COMBINE/OMEX archives](https://combinearchive.org/) that describe one or more simulation experiments (in [SED-ML format](https://sed-ml.org)) of one or more models (in [CellML format](https://cellml.org])).

A list of the algorithms and algorithm parameters supported by OpenCOR is available at [BioSimulators](https://biosimulators.org/simulators/opencor).

A simple web application and web service for using OpenCOR to execute COMBINE/OMEX archives is also available at [runBioSimulations](https://run.biosimulations.org).

## Installation

### Install Python package and command-line application

1. Install the requirements for OpenCOR:

   ```sh
   apt-get install -y \
       curl \
       libpulse-mainloop-glib0 \
       libx11-6 \
       libxext6 \
       libxslt1.1 \
       sqlite3
   ```

2. Install [OpenCOR](https://opencor.ws/downloads/index.html):

   ```sh
   url=https://opencor.ws/downloads/snapshots/2021-05-19/OpenCOR-2021-05-19-Linux.tar.gz
   curl $url | tar -xz --directory=/opt/
   ```

3. Add OpenCOR to your system path:

   ```sh
   export PATH=/opt/OpenCOR-2021-05-19-Linux:$PATH
   ```

4. Install pip for this version of Python:

   ```sh
   curl https://bootstrap.pypa.io/get-pip.py | OpenCOR -c PythonShell
   ```

5. Use pip to install this package:

   ```sh
   /opt/OpenCOR-2021-05-19-Linux/python/bin/python -m pip install biosimulators-opencor
   ```

### Install Docker image
```
docker pull ghcr.io/biosimulators/opencor
```

## Usage

### Local usage
```
usage: opencor [-h] [-d] [-q] -i ARCHIVE [-o OUT_DIR] [-v]

BioSimulators-compliant command-line interface to the OpenCOR <https://opencor.ws> simulation program.

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           full application debug mode
  -q, --quiet           suppress all console output
  -i ARCHIVE, --archive ARCHIVE
                        Path to OMEX file which contains one or more SED-ML-
                        encoded simulation experiments
  -o OUT_DIR, --out-dir OUT_DIR
                        Directory to save outputs
  -v, --version         show program's version number and exit
```

### Usage through Docker container
The entrypoint to the Docker image supports the same command-line interface described above.

For example, the following command could be used to use the Docker image to execute the COMBINE/OMEX archive `./modeling-study.omex` and save its outputs to `./`.

```
docker run \
  --tty \
  --rm \
  --mount type=bind,source="$(pwd)",target=/root/in,readonly \
  --mount type=bind,source="$(pwd)",target=/root/out \
  ghcr.io/biosimulators/opencor:latest \
    -i /root/in/modeling-study.omex \
    -o /root/out
```

## Documentation
Documentation is available at https://docs.biosimulators.org/Biosimulators_OpenCOR/.

## License
This package is released under the [MIT](LICENSE).

## Development team
This package was developed by the [Karr Lab](https://www.karrlab.org) at the Icahn School of Medicine at Mount Sinai and the [Center for Reproducible Biomedical Modeling](https://reproduciblebiomodels.org/).

## Questions and comments
Please contact the [BioSimulators Team](mailto:info@biosimulators.org) with any questions or comments.
