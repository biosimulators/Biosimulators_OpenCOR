# VERSION
ARG VERSION=0.0.4
ARG SIMULATOR_VERSION="2021-07-09"

# Base OS
FROM opencor/opencor:$SIMULATOR_VERSION

# metadata
LABEL \
    org.opencontainers.image.title="OpenCOR" \
    org.opencontainers.image.version="${SIMULATOR_VERSION}" \
    org.opencontainers.image.description="Modelling environment which can be used to organise, edit, simulate and analyse CellML files" \
    org.opencontainers.image.url="https://opencor.ws/" \
    org.opencontainers.image.documentation="https://opencor.ws/user/index.html" \
    org.opencontainers.image.source="https://github.com/biosimulators/Biosimulators_OpenCOR" \
    org.opencontainers.image.authors="BioSimulators Team <info@biosimulators.org>" \
    org.opencontainers.image.vendor="BioSimulators Team" \
    org.opencontainers.image.licenses="GPL-3.0-only" \
    \
    base_image="ubuntu:20.04" \
    version="${VERSION}" \
    software="opencor" \
    software.version="${SIMULATOR_VERSION}" \
    about.summary="Modelling environment which can be used to organise, edit, simulate and analyse CellML files" \
    about.home="https://opencor.ws/" \
    about.documentation="https://opencor.ws/user/index.html" \
    about.license_file="https://raw.githubusercontent.com/opencor/opencor/master/LICENSE.txt" \
    about.license="SPDX:GPL-3.0-only" \
    about.tags="systems biology,dynamical modeling,CellML,SED-ML,COMBINE,OMEX,BioSimulators" \
    maintainer="BioSimulators Team <info@biosimulators.org>"

# Add Python to system path
ENV PYTHON="OpenCOR -c PythonShell" \
    PIP="${OPENCORDIR}/python/bin/python -m pip"

# Copy code for command-line interface into image and install it
COPY . /tmp/Biosimulators_OpenCOR
RUN $PIP install /tmp/Biosimulators_OpenCOR \
    && rm -rf /tmp/Biosimulators_OpenCOR
ENV VERBOSE=0 \
    MPLBACKEND=PDF

# Entrypoint
# - The working directory must be set to something other than the default because the default includes a Python file with the same
#   name as the opencor Python module, which will cause the Python interpreter to fail to find the OpenCOR module
# - ugo+w permissions to `${OPENCORDIR}/python/bin` are needed because the OpenCOR Python pluging dynamically generates these files
RUN mkdir ${HOMEDIR}/Biosimulators_OpenCOR \
    && chmod -R ugo+w ${OPENCORDIR}/python/bin
WORKDIR ${HOMEDIR}/Biosimulators_OpenCOR
ENTRYPOINT ["pythonshell", "-m", "biosimulators_opencor"]
CMD []
