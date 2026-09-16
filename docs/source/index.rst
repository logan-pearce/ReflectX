
.. image:: images/logo-sol.png
  :width: 500
  :align: center

ReflectX
========

**ReflectX** is a suite of planet reflected light spectra generated from `PICASO <https://natashabatalha.github.io/picaso/>`_ and `VIRGA <https://natashabatalha.github.io/virga/>`_ for detecting and characterizing directly imaged exoplanets in reflected light using `MagAO-X <https://xwcl.science/>`_, ELTs (ELT-PCS, `ELT-ANDES <https://ui.adsabs.harvard.edu/abs/2024SPIE13096E..13M/abstract>`_ and `GMagAO-X <https://magao-x.org/gmagao-x/>`_), and HWO.

Currently ReflectX version 1 offers a grid of equilibrium gas giant models spanning star and planet parameters, see the Gas Giant Grid page for more.  If you want a bespoke model of a specific planet, please email Logan Pearce lapearce@umich.edu and we're happy to collaborate!

.. important::

  .. Download Gas Giant models `here <https://zenodo.org/records/18315998>`_


.. note::

   This project is under active development.

Contents
--------

.. toctree::
   :maxdepth: 2

   installation
   gasgiantgrid
   GJ876bc-models
   notebooks/Tutorial
   autoapi/index
   

Changelog
---------
**1.0.4 (2026-09-16)**

* Added MKO Y filter

**1.0.3 (2026-09-11)**

* Addition of a few new function for loading custom models

**1.0.2 (2026-09-09)**

* Addition of a few new functions and updated docs to correspond with submission of the model grid paper

**1.0.1 (2026-03-07)**

* Minor bug fix

**1.0.0 (2026-03-07)**

* Initial release of gas giant model set
