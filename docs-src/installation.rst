Installation instructions
=========================

BioSimulators-OpenCOR is available as a command-line program and as a command-line program encapsulated into a Docker image.

Python Package and command-line program
---------------------------------------

1. Install the requirements for OpenCOR::

    apt-get install -y \
        curl \
        libpulse-mainloop-glib0 \
        libx11-6 \
        libxext6 \
        libxslt1.1 \
        sqlite3

2. Install `OpenCOR <https://opencor.ws/downloads/index.html>`_::

    url=https://opencor.ws/downloads/snapshots/2021-05-19/OpenCOR-2021-05-19-Linux.tar.gz
    curl $url | tar -xz --directory=/opt/

3. Add OpenCOR to your system path::

    export PATH=/opt/OpenCOR-2021-05-19-Linux:$PATH

4. Install pip for this version of Python::

    curl https://bootstrap.pypa.io/get-pip.py | OpenCOR -c PythonShell

5. Use pip to install this package::

    /opt/OpenCOR-2021-05-19-Linux/python/bin/python -m pip install biosimulators-opencor


Docker image with a command-line entrypoint
-------------------------------------------

After installing `Docker <https://docs.docker.com/get-docker/>`_, run the following command to install the Docker image for BioSimulators-OpenCOR:

.. code-block:: text

    docker pull ghcr.io/biosimulators/opencor
