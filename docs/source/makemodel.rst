Make a single model on Kaiju
=====

The MagAO-X lab computer Kaiju is set up to run a single model via a command line interface.

Config file
----------------
ReflectX Command Line Tool takes in a config file that sets up the model parameters. 

Example config files can be found at ``/srv/nas/users/loganpearce/config-gasgiant.ini`` and ``/srv/nas/users/loganpearce/config-terrestrial.ini``.  Both files contain parameters for terrestrial or gas giant models but have each been configured for one of the model types.  If ``model.type`` is set to 'Terrestrial', then gas giant parameters will be ignored, and vice versa.

Sections
~~~~~~~~
| The first three sections are common to both planet types.
| ``MODEL.CONFIG``: Model configurations
| ``modeltype``: Select 'Terrestrial' or 'GasGiant'. For the main grid, I used Terrestrial for anything less than about 10 Mearth.
| ``opacity.db``: Path to the opacity database to use.  Don't change this. 
| ``wavelength.range``: [min,max] of wavelength range for spectra in microns.  The ReflectX grid used [0.4, 2]
| ``output.directory``: Path to where you want to save the model.
| ``directory.filename``: Name the output directory for your model.

| ``STAR.PARAMS``: Parameters for the star in the system
| ``teff``: Effective Temperature
| ``radius``: Star radius
| ``radius.unit``: Unit of above radius. Either `Rsun` or or `km` 
| ``logg``: log gravity
| ``metallicity``: star metallicity in solar units.
| ``star.model.database``: Select which stellar model database to use, either 'phoenix' or 'ck04models'. Phoenix is recommended.

| ``PHASE.PARAMS``: Parameters for phase angle
| ``phase``: angle in degrees.  Angles larger than about 140 deg will return little to no flux.
| ``ntangle``, ``ngangle``: For non-zero phase angles, select the number of vertical and horizonal computational points to use. More points =  longer compute time. Recommend don't change these.

Terrestrial models
^^^^^^^^^^^^^^^^^^

| ``TERRESTRIAL.PLANET.PARAMS``:
| ``teq``: For the terrestrial models, the equilibrium temp set what clouds will condense, so we use the T_eq to set the clouds and the star-planet separation.
| ``custom.pt.profile.dataframe``: option to input your own PT profile. Not operational yet. 
| You must either set gravity or Mass/Radius. If setting gravity, a radius is also required to generate the planet spectrum If gravity is set to None, a mass is required.
| ``gravity``: gravity, required if mass = `none`
| ``gravity.unit`` must be `m/(s**2)`
| ``radius``: Planet radius, required for all models
| ``radius.unit``: must be Rearth, Rjup, or km
| ``mass``:Mass (required if gravity = None)
| ``mass.unit`` Must be Mjup or Mearth
| ``surface.albedo``: reflectivity of planet surface. Generally about 0.2. See terrestrial grid page for planet-type specific albedos
| ``custom.atmosphere.config``: Option to input a custom atmosphere database, not currently operational
| ``thermal``: Option to add thermal emission to model. Not currently operational
| ``ATMOSPHERE.GASES.AND.CONCENTRATIONS``: Set which chemical species in the atmosphere and at what concentrations. Conc must add to 1.  Add or subtract any desired species recognized by picaso/virga. Only needed for terrestrial planets.  Follow picaso/virga docs for recognized gas strings.
| ``GREY.CLOUD.SLAB.CONFIG``: Settings for cloud configuration.  See picaso documentation. Only needed for terrestrial planets
| ``ncloud.levels``: Number of cloud levels. The following parameters must be a list of settings for each layer.
| ``g0``: cloud asymmetry factor, between 0-1
| ``w0``: single scattering albedo, between 0-1
| ``opd``: Total optical depth (tau) of each layer
| ``p``: altitude of each layer in log10(pressure), Ex: 2 = 100 bars, -1 = 0.1 bars
| ``dp``: height of each layer in log10(delta P) above given pressure layer. Ex: p = [2], dp = [3] would be a sinlge cloud layer starting at 100 bars and extending up to 0.1 bars. p=[2, -1], dp = [1, 1] would be two cloud layers, one at 100 bars extending up to 10 bars, and a second layer starting at 0.1 bars and extending up to 0.01 bars.

Gas Giant models
^^^^^^^^^^^^^^^^^^