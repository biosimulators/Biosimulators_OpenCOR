libCellML cannot be imported in the OpenCOR Docker image

    Attempting to import libCellML into the OpenCOR Docker image produces the linking error below.
    ```sh
    docker run -it --rm \
        --entrypoint bash \
        opencor/opencor:2021-05-19 \
        -c "/home/opencor/OpenCOR/python/bin/python -m pip install libcellml; /home/opencor/OpenCOR/python/bin/python -c \"import libcellml\""
    ```

    ```sh    
    Collecting libcellml
      Downloading libcellml-0.2.0.dev21-cp37-cp37m-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (2.8 MB)
         |████████████████████████████████| 2.8 MB 30.6 MB/s 
    Installing collected packages: libcellml
    Successfully installed libcellml-0.2.0.dev21
    WARNING: You are using pip version 20.3.1; however, version 21.1.2 is available.
    You should consider upgrading via the '/home/opencor/OpenCOR/python/bin/python -m pip install --upgrade pip' command.
    Traceback (most recent call last):
      File "<string>", line 1, in <module>
      File "/home/opencor/OpenCOR/python/lib/python3.7/site-packages/libcellml/__init__.py", line 12, in <module>
        from libcellml.analyser import Analyser
      File "/home/opencor/OpenCOR/python/lib/python3.7/site-packages/libcellml/analyser.py", line 13, in <module>
        from . import _analyser
    ImportError: libpython3.7m.so.1.0: cannot open shared object file: No such file or directory
    ```

    The same error occurs when trying to import libCellML into OpenCOR's Python shell
    ```sh
    docker run -it --rm \
        --entrypoint bash \
        opencor/opencor:2021-05-19 \
        -c "/home/opencor/OpenCOR/python/bin/python -m pip install libcellml; OpenCOR -c PythonShell -c \"import libcellml\""
    ```


OpenCOR can't be used with IPython

    IPython cannot be imported into the OpenCOR docker image.
    
    ```sh    
    docker run -it --rm \
        --entrypoint bash \
        opencor/opencor:2021-05-19 \
        -c "/home/opencor/OpenCOR/python/bin/python -m pip install ipython; /home/opencor/OpenCOR/python/bin/ipython"
    ```

    ```sh
    Requirement already satisfied: ipython in ./OpenCOR/python/lib/python3.7/site-packages (7.8.0)
    Requirement already satisfied: setuptools>=18.5 in ./OpenCOR/python/lib/python3.7/site-packages (from ipython) (51.0.0)
    Requirement already satisfied: jedi>=0.10 in ./OpenCOR/python/lib/python3.7/site-packages (from ipython) (0.17.2)
    Requirement already satisfied: decorator in ./OpenCOR/python/lib/python3.7/site-packages (from ipython) (4.4.2)
    Requirement already satisfied: pickleshare in ./OpenCOR/python/lib/python3.7/site-packages (from ipython) (0.7.5)
    Requirement already satisfied: traitlets>=4.2 in ./OpenCOR/python/lib/python3.7/site-packages (from ipython) (4.3.2)
    Requirement already satisfied: prompt_toolkit<2.1.0,>=2.0.0 in ./OpenCOR/python/lib/python3.7/site-packages (from ipython) (2.0.10)
    Requirement already satisfied: pygments in ./OpenCOR/python/lib/python3.7/site-packages (from ipython) (2.7.3)
    Requirement already satisfied: backcall in ./OpenCOR/python/lib/python3.7/site-packages (from ipython) (0.2.0)
    Requirement already satisfied: pexpect in ./OpenCOR/python/lib/python3.7/site-packages (from ipython) (4.8.0)
    Requirement already satisfied: pexpect in ./OpenCOR/python/lib/python3.7/site-packages (from ipython) (4.8.0)
    Requirement already satisfied: parso<0.8.0,>=0.7.0 in ./OpenCOR/python/lib/python3.7/site-packages (from jedi>=0.10->ipython) (0.7.1)
    Requirement already satisfied: ptyprocess>=0.5 in ./OpenCOR/python/lib/python3.7/site-packages (from pexpect->ipython) (0.6.0)
    Requirement already satisfied: six>=1.9.0 in ./OpenCOR/python/lib/python3.7/site-packages (from prompt_toolkit<2.1.0,>=2.0.0->ipython) (1.15.0)
    Requirement already satisfied: wcwidth in ./OpenCOR/python/lib/python3.7/site-packages (from prompt_toolkit<2.1.0,>=2.0.0->ipython) (0.2.5)
    Requirement already satisfied: ipython_genutils in ./OpenCOR/python/lib/python3.7/site-packages (from traitlets>=4.2->ipython) (0.2.0)
    Requirement already satisfied: six>=1.9.0 in ./OpenCOR/python/lib/python3.7/site-packages (from prompt_toolkit<2.1.0,>=2.0.0->ipython) (1.15.0)
    Requirement already satisfied: decorator in ./OpenCOR/python/lib/python3.7/site-packages (from ipython) (4.4.2)
    WARNING: You are using pip version 20.3.1; however, version 21.1.2 is available.
    You should consider upgrading via the '/home/opencor/OpenCOR/python/bin/python -m pip install --upgrade pip' command.
    bash: /home/opencor/OpenCOR/python/bin/ipython: /home/alan/OpenCOR/build/python/bin/python3: bad interpreter: No such file or directory
    ```

    The following succeeds, but executes an IPython shell that functions poorly.
    ```sh
    docker run -it --rm \
        --entrypoint bash \
        opencor/opencor:2021-05-19 \
        -c "OpenCOR -c PythonShell -m IPython"
    ```

Simulations with output start time != initial time cause segmentation faults
  
    The attached SED-ML file (with output start time change to 10) causes a segmentation fault. It would be helpful to see an informative error message rather than a segmentation fault.

    ```sh
    docker run -it --rm \
        --mount type=bind,source=/home/jonrkarr/Documents,target=/home/opencor/workdir \
        opencor/opencor:2021-05-19 \
        /home/opencor/workdir/lorenz-unsupported-output-start-time.sedml
    ```

    ```
    Segmentation fault (core dumped)
    ```

Loading SED-ML files with unsupported algorithms cause segmentation faults
  
    The attached SED-ML file (with KISAO:0000019 replaced with KISAO:0000029 for SSA) causes a segmentation fault. It would be helpful to see an informative error message rather than a segmentation fault.

    ```sh
    docker run -it --rm \
        --mount type=bind,source=/home/jonrkarr/Documents,target=/home/opencor/workdir \
        opencor/opencor:2021-05-19 \
        /home/opencor/workdir/unsupported-algorithm-causes-seg-fault.sedml
    ```

    ```
    Segmentation fault (core dumped)
    ```

Loading SED-ML files with unsupported algorithm parameters cause segmentation faults
  
    The attached SED-ML file (with additional parameter KISAO:0000219 -- maximum Adams order) causes a segmentation fault. It would be helpful to see an informative error message rather than a segmentation fault.

    ```sh
    docker run -it --rm \
        --mount type=bind,source=/home/jonrkarr/Documents,target=/home/opencor/workdir \
        opencor/opencor:2021-05-19 \
        /home/opencor/workdir/lorenz-unsupported-algorithm-parameter-causes-seg-fault.sedml
    ```

    ```
    Segmentation fault (core dumped)
    ```

Loading SED-ML files with invalid algorithm parameter does not fail
  
    The attached SED-ML file (with KISAO:0000475 = undefined) should be invalid. However, OpenCOR opens the simulation without any errors or warnings.

    ```sh
    docker run -it --rm \
        --mount type=bind,source=/home/jonrkarr/Documents,target=/home/opencor/workdir \
        opencor/opencor:2021-05-19 \
        /home/opencor/workdir/lorenz-does-not-fail-on-invalid-parameter-value.sedml
    ```

OpenCOR unexpected appears to cache SED-ML files
    OpenCOR appears to have a strange behavior where repeated calls to `open_simulation` return the same result, rather than reading the current state of the requested file.

    In the first example, reading a SED-ML file with CVODE and then a different file with SSA fails with a segmentation fault. 

    In the second example, reading the file with CVODE, then editing the file to use CVODE, and then re-opening the file does not cause a segmentation fault. It seems that the second apparently successful opening of the file with SSA is incorrect. I believe the intended behavior is for OpenCOR to raise an exception.

    ```sh
    docker run -it --rm \
        --mount type=bind,source=/home/jonrkarr/Documents,target=/home/opencor/workdir \
        --entrypoint bash \
        --workdir /home/opencor/workdir \
        opencor/opencor:2021-05-19 \
        -c "OpenCOR -c PythonShell"
    ```

    Opening a simulation with SSA fails with a segmentation fault
    ```python
    import opencor
    import shutil

    filename = 'lorenz.sedml'
    copy_filename = 'lorentz-temp.sedml'
    shutil.copyfile(filename, copy_filename)

    # open simulation
    opencor.open_simulation(filename)

    # replace CVODE with SSA
    with open(copy_filename, 'r') as file:
        content = file.read()
    content = content.replace('KISAO:0000019', 'KISAO:0000029')
    with open(copy_filename, 'w') as file:
        file.write(content)

    # open simulation again
    # OpenCOR should fail with a segementation fault, but it doesn't
    opencor.open_simulation(copy_filename)
    ```

    Opening a simulation with SSA succeeds
    ```python
    import opencor
    import shutil

    filename = 'lorenz.sedml'
    copy_filename = 'lorentz-temp.sedml'
    shutil.copyfile(filename, copy_filename)

    # open simulation
    opencor.open_simulation(copy_filename)

    # replace CVODE with SSA
    with open(copy_filename, 'r') as file:
        content = file.read()
    content = content.replace('KISAO:0000019', 'KISAO:0000029')
    with open(copy_filename, 'w') as file:
        file.write(content)

    # open simulation again
    # OpenCOR should fail with a segementation fault, but it doesn't
    opencor.open_simulation(copy_filename)
    ```
