Installation
============

ReflectX python functions are installable via `PyPi <https://pypi.org/project/ReflectX/1.0.0/>`_ and pip

.. code-block:: bash
	
	$ pip install ReflectX

Currently required python>=3.9 and numpy, scipy, astropy, xarray, h5py, and h5netcdf.

Recommend creating a new conda environment:

.. code-block:: bash
	
    $ conda create python=3.12 -n ReflectX-env
    $ conda activate ReflectX-env
    $ conda install pip
	$ pip install ReflectX

or to install the development version you can clone the git repo and install a local editable copy:

.. code-block:: bash
	
    $ conda create python=3.12 -n ReflectX-env
    $ conda activate ReflectX-env
    $ conda install pip
	$ git clone https://github.com/logan-pearce/ReflectX.git
    $ cd ReflectX
    $ pip install -e .

Issues? Create a github issue or email lapearce@umich.edu