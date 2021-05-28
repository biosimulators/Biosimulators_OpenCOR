# Base OS
FROM opencor/opencor

ARG VERSION=0.0.1
ARG SIMULATOR_VERSION="0.6"

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
ENV PATH=/home/opencor/OpenCOR/python/bin:$PATH

# Install pip
RUN curl https://bootstrap.pypa.io/get-pip.py | python

# Copy code for command-line interface into image and install it
COPY . /root/Biosimulators_OpenCOR
RUN pip install /root/Biosimulators_OpenCOR \
    && rm -rf /root/Biosimulators_OpenCOR
ENV VERBOSE=0 \
    MPLBACKEND=PDF

# Entrypoint
ENTRYPOINT ["biosimulators-opencor"]
CMD []
