Using ReflectX Models to Estimate Siganl-to-Noise (S/N)
=======================================================

Signal
^^^^^^

Following the method of Males et al. 2021, we need to determine the signal arriving at the detector in units of :math:`photons \; s^{-1} (\lambda/D)^{-1}`. PICASO and other models return the flux from the surface of the object, the planet in this case.  So we need to scale the flux to that arriving at the observer:

   :math:`F = I \Omega`

where :math:`F` = flux at Earth, :math:`I` = model intensity, and

    :math:`\Omega = \frac{R_p^2}{D^2}`

where :math:`R_p` = planet radius and :math:`D` = distance, both in the same unit. Next convert :math:`ergs cm^{-1} s^{-1} cm^{-2}` to :math:`photons s^{-1}`. Energy per photon per wavelength is:

    :math:`E\,[ergs] = \frac{hc}{\lambda[cm]}`

and number of photons per wavelength:

    :math:`n_{\gamma}\left[\frac{\gamma}{cm\,s\,cm^2}\right] = \frac{F_{\lambda}(\lambda)\left[\frac{ergs}{cm\,s\,cm^2}\right]}{E\,[ergs]}`

Then the total flux in the filter is the sum over all wavelengths of the flux times the filter transmission curve:

    :math:`\mathrm{Total \; flux} \;[\gamma \;s^{-1} cm^{-2}] = \sum(F_\lambda(\lambda)\; [\gamma \;cm^{-1} s^{-1} cm^{-2}] \times R(\lambda) \times \delta\lambda \;[cm] )`

where :math:`R(\lambda)` is the filter transmission curve as a function of wavelength, and :math:`\delta\lambda` is the interval the spectrum is sampled in. Finally now multiply by the telescope collecting area:

    :math:`\mathrm{Total \; flux} \;[\gamma \;s^{-1}] = \mathrm{Total \; flux} \;[\gamma \;s^{-1} cm^{-2}] \times \pi r^2`

where :math:`r` is the radius of the primary mirror. This gives total filter flux in photons per second.  

Noise in the atmospheric speckle limited regime
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
To estimate the noise of an observation we use the method of Males et al. 2021. The intensity of a planet with contrast :math:`C` to the host star is:

    :math:`I_p (t) = C \times I_*``

where :math:`I` is the planet and star intensity in units of :math:`photons \; s^{-1} (\lambda/D)^{-1}`, where :math:`\lambda/D` is the fundamental spatial scale for diffraction limited imaging. The noise in a single resolution element located at the planet's separation and position angle from the star :math:`(\overrightarrow{r_p})` can be written as:


    :math:`\sigma^2 = \underbrace{I_{s,*} \Delta t}_\text{Star Poisson noise} \left[\underbrace{I_c + I_{as} + I_{qs}}_\text{Star halo at planet location}  + \underbrace{I_{s,*}[\tau_{as}(I_{as}^2 + 2[I_c I_{as} + I_{as} I_{qs}])}_\text{Atm speckles}+ \underbrace{\tau_{qs}(I_{qs}^2 + 2I_c I_{qs})]}_\text{Quasistatic speckles} \right]\;\;`
    :math:`+ \underbrace{I_{p,*} \Delta t}_\text{Planet Poisson noise} + \underbrace{I_{\rm{sky}}\Delta t N_{\rm{pix}}(\lambda)}_\text{Sky background poisson noise} + \underbrace{\left(RN \frac{\Delta t}{t_{\rm{exp}}}\right)^2}_\text{Read noise} \;\; + \underbrace{I_{dc}\Delta t N_{\rm{pix}}(\lambda)}_\text{dark current}`

where:
    * :math:`I_{s,*}/I_{p,*}` is the peak intensity in an aperture of size :math:`\lambda$/D` centered on the Airy core without a coronagraph in photons/sec/($\lambda$/D), incorporating telescope and instrument throughput, with :math:`I_* = I \times T \times \pi/4 \times \rm{Strehl\;Ratio}`, where :math:`I` is the star/planet's intensity in a given filter, :math:`T` is the telescope and instrument throughput, and :math:`\pi/4` is the amount of starlight contained in the Airy core in an aperture of size $\lambda/D$,
    * :math:`I_c` is the fractional contribution of intensity from residual diffraction from coronagraph,
    * :math:`I_{as}` is the contribution from atmospheric speckles,
    * :math:`I_{qs}` is contribution from speckles caused by instrument imperfections ("quasi-static" speckles),
    * :math:`\tau_{as}` is the average lifetime of atmospheric speckles, 
    * :math:`\tau_{qs}` is the average lifetime of quasi-static speckles, 
    * :math:`I_{sky}` is the average sky background count rate,
    * :math:`RN` is the read noise,
    * :math:`I_{dc}` is the dark current count rate, 
    * :math:`\Delta t` is the observation time,
    * :math:`t_{exp}` is the exposure time of a single frame. 
    * :math:`N_{pix}` is the number of pixels within the area of a circle of a 1 $\lambda$/D radius, 
    * with :math:`A_{\rm{\lambda/D}} \rm{[mas]} = \pi r^2, r = 0.5\lambda/D,\; \lambda/D \rm{[mas]} = 0.2063 \frac{\lambda [\mu m]}{D [\rm{m}]} \times 10^{-3}` and :math:`A_{pix} =` pixel side length :math:`[mas^2]`, then :math:`N_{pix} = A_{\rm{\lambda/D}} \rm{[mas]} / A_{pix} \rm{[mas]}`.

This is Males et al. 2021 Eqn 7 plus the typical noise terms. We assume that we have a perfectly functioning coronagraph and instrument such that :math:`I_{qs}` and :math:`I_{c}` terms are negligible compared to the atmospheric speckle terms, thus we are in the speckle-noise limited regime.  Additionally, for the purposes of these calculations I will assume that the sky, read noise, and dark current are all negligible compared to the speckles.  So this equation reduces to:

    :math:`\sigma^2 = I_* \Delta t \left[I_{as}  + {I_{s,*}\tau_{as}I_{as}^2}\right]\;\; + I_{p,*} \Delta t`

and companion :math:`S/N` becomes:

    :math:`S/N \approx \frac{I_{p,*} \Delta t}{\sqrt{I_{s,*} \Delta t \left[I_{as}  + {I_{s,*}\tau_{as}I_{as}^2}\right]\;\; + I_{p,*} \Delta t}}`

and the time to a desired :math:`S/N` is:

    :math:`\Delta t = \left(\frac{S/N}{I_p}\right)^2 \left[I_{s,*} \left(I_{as} + {I_{s,*}\tau_{as}I_{as}^2}\right) + I_{p,*} \right]`

Males et al. gives model maps for :math:`I_{as}` as a function of guide star magnitude and wavefront control (WFC; either simple integrator (SI) or linear predictive control (LP, Males et al. 2018)). Males et al. 2021 Figure 10 gives the average atmospheric speckle lifetime :math:`\tau_{as}` as a function of several parameters. For an LP WFC on a 24.5~m (GMT sized) mirror on a 5th magnitude star :math:`\tau_{as} \sim 0.02` s; for an 8th magnitude star its :math:`\sim 0.03` s. For SP WFC it's significantly longer, :math:`\sim 0.07` s for a 24.5~m mirror on a 5th magnitude star.


In code: 


.. code-block:: python
    from ReflectXTools import GetSNR
    directory = 'path_to_spectrum_files/'
    c = pd.read_csv(directory+'ReflectX-spectra-phase90-cto-1.0.csv')
    directory = 'path_to_model_files//'
    pc = pickle.load(open(directory+'phase90-cto-1.0-model.pkl','rb'))

    wavelength = np.array(c['wavelength [um]'])
    planet_contrast = np.array(c['cloudy-fpfs-kzz1e+09-fsed0.03'])
    planet_radius = 0.97*u.Rjup
    sep = pc.inputs['star']['semi_major']*u.cm

    primary_mirror_diameter = 25.4*u.m
    wfc = 'lp'
    observationtime = np.logspace(-2,5,1000)
    path_to_maps = 'path_to_noise_maps/'

    snrc, planet_signal, star_signal = GetSNR(wavelength, planet_contrast, 
            star_flux,
            primary_mirror_diameter, 
            planet_radius, star_radius, 
            distance, sep, wfc,
            filters, observationtime,
            path_to_maps = path_to_maps)