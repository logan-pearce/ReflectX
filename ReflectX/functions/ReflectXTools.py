################## SNR as a function of time from ReflectX models:

import numpy as np
import astropy.constants as const
import astropy.units as u
import pandas as pd
import pickle

def GetPhotonsPerSec(wavelength, flux, filt, distance, radius, primary_mirror_diameter,
                    return_ergs_flux_times_filter = False, Omega = None):
    ''' Given a spectrum with wavelengths in um and flux in ergs cm^-1 s^-1 cm^-2, convolve 
    with a filter transmission curve and return photon flux in photons/sec. 
    Following eqns in Chp 7 of my thesis
    
    Args:
        wavelength [arr]: wavelength array in um
        flux [arr]: flux array in ergs cm^-1 s^-1 cm^-2 from the surface of the object (NOT corrected for distance)
        filt [myastrotools filter object]: filter
        distance [astropy unit object]: distance to star with astropy unit
        radius [astropy unit object]: radius of star or planet with astropy unit
        primary_mirror_diameter [astropy unit object]: primary mirror diameter with astropy unit
        return_ergs_flux [bool]: if True, return photons/sec and the flux in ergs cm^-1 s^-1 cm^-2
                                convolved with the filter
    Returns
        astropy units object: flux in photons/sec
        
    '''
    import astropy.constants as const
    # energy in ergs:
    energy_in_ergs_per_photon_per_wavelength = const.h.cgs * const.c.cgs / wavelength # Eqn 7.14
    # Flux in photons/cm s cm^2: number of photons per area per sec per lambda:
    nphotons_per_wavelength = flux / energy_in_ergs_per_photon_per_wavelength # Eqn 7.15
    
    # Combine flux with filter curve:
    w = filt.wavelength*filt.wavelength_unit.to(u.um)
    t = filt.transmission
    # make interpolation function:
    ind = np.where((wavelength > min(w)) & (wavelength < max(w)))[0]
    # of spectrum wavelength and Flux in photons/cm s cm^2:
    from scipy.interpolate import interp1d
    f = interp1d(wavelength[ind], nphotons_per_wavelength[ind], fill_value="extrapolate")
    # interpolate the filter flux onto the spectrum wavelength grid:
    flux_on_filter_wavelength_grid = f(w)

    # multiply flux time filter transmission
    filter_times_flux = flux_on_filter_wavelength_grid * t # F_l x R(l) in eqn 7.16
    
    # Now sum:
    dl = (np.mean([w[j+1] - w[j] for j in range(len(w)-1)]) * u.um).to(u.cm)

    total_flux_in_filter = np.sum(filter_times_flux * dl.value) # Eqn 7.16
    
    
    area_of_primary = np.pi * ((0.5*primary_mirror_diameter).to(u.cm))**2

    #Total flux in photons/sec:
    total_flux_in_photons_sec = total_flux_in_filter * area_of_primary.value # Eqn 7.17
    
    if return_ergs_flux_times_filter:
        f = interp1d(wavelength[ind], flux[ind], fill_value="extrapolate")
        # interpolate the filter flux onto the spectrum wavelength grid:
        flux_ergs_on_filter_wavelength_grid = f(w)
        filter_times_flux_ergs = flux_ergs_on_filter_wavelength_grid * t
        
        return total_flux_in_photons_sec * (1/u.s), filter_times_flux_ergs, w
    return total_flux_in_photons_sec * (1/u.s)

def GetGuideStarMagForIasTableLookup(actual_star_magnitude):
    # Tables are available for these guide star mags:
    available_mags = np.array(['0', '2.5', '5', '7', '9', '10', '11',
                        '11.5', '12', '12.5', '13','13.5', '14', '14.5', '15'])
    available_mags = np.array([float(m) for m in available_mags])
    # find the one closest to actual guidestar mag:
    idx = (np.abs(available_mags - actual_star_magnitude)).argmin()
    table_guidestarmag = str(available_mags[idx]).replace('.0','')
    return table_guidestarmag

def Get_LOD_in_mas(central_wavelength, D):
    ''' Return lambda/D in mas mas for a filter and primary diameter
    Args:
        central_wavelength (flt, astropy units object): wavelength of filter
        D (flt, astropy units object): primary diameter
    Returns:
        flt: lambda over D in mas
    '''
    central_wavelength = central_wavelength.to(u.um)
    D = D.to(u.m)
    lod = 0.206*central_wavelength.value/D.value
    lod = lod*u.arcsec.to(u.mas)
    return lod

def GetIasFromTable(guidestarmag, wfc, sep, pa, 
                   path_to_maps = '/Users/loganpearce/Dropbox/astro_packages/myastrotools/myastrotools/GMagAO-X-noise/'):
    ''' For a given guide star magnitude and wfc, look up the value of the atmospheric speckle
        contribution I_as (Males et al. 2021 eqn 6) at a given separation and position angle
        
    Args:
        guidestarmag (flt or str): Guide star magnitude. Must be: ['0', '2.5', '5', '7', '9', '10', '11',
                        '11.5', '12', '12.5', '13','13.5', '14', '14.5', '15']
        wfc (str): wavefront control set up.  Either linear predictive control "lp" or simple integrator "si"
        sep (flt): separation in lambda/D
        pa (flt): position angle in degrees
    
    Returns:
        flt: value of I_as at that location
    '''
    IasMap = fits.getdata(path_to_maps+f'varmap_{guidestarmag}_{wfc}.fits')
    center = [0.5*(IasMap.shape[0]-1),0.5*(IasMap.shape[1]-1)]
    dx = sep * np.cos(np.radians(pa + 90))
    dy = sep * np.sin(np.radians(pa + 90))
    if int(np.round(center[0]+dx, decimals=0)) < 0:
        return np.nan
    try:
        return IasMap[int(np.round(center[0]+dx, decimals=0)),int(np.round(center[1]+dy,decimals=0))]
    except IndexError:
        return np.nan

def GetIas(guidestarmag, wfc, sep, pa, wavelength, 
           path_to_maps = '/Users/loganpearce/Dropbox/astro_packages/myastrotools/myastrotools/GMagAO-X-noise/'):
    '''For a given guide star magnitude, wfc, and planet-star contrast, get the SNR
        in the speckle-limited regime (Eqn 10 of Males et al. 2021)
        at a given separation and position angle.
        
    Args:
        guidestarmag (flt or str): Guide star magnitude. Must be: ['0', '2.5', '5', '7', '9', '10', '11',
                        '11.5', '12', '12.5', '13','13.5', '14', '14.5', '15']
        wfc (str): wavefront control set up.  Either linear predictive control "lp" or simple integrator "si"
        sep (flt): separation in lambda/D
        pa (flt): position angle in degrees
        Cp (flt): planet-star contrast
        deltat (flt): observation time in sec
        wavelength (astropy units object):  central wavelength of filter band
        tau_as (flt): lifetime of atmospheric speckles in sec. Default = 0.02, ave tau_as for 24.5 m telescope
                from Males et al. 2021 Fig 10
    
    Returns:
        flt: value of I_as at that location
    '''
    from astropy.io import fits
    ## Load map:
    # IasMap = fits.getdata(path_to_maps+f'contrast_{guidestarmag}_{wfc}.fits')
    IasMap = fits.getdata(path_to_maps+f'varmap_{guidestarmag}_{wfc}.fits')
    
    # Look up Ias from table
    Ias = GetIasFromTable(guidestarmag, wfc, sep, pa, path_to_maps = path_to_maps)
    # Correct for differnce in wavelength between lookup table and filter wavelength:
    wavelength = wavelength.to(u.um)
    Ias = Ias * (((0.8*u.um/wavelength))**2).value
    if np.isnan(Ias):
        raise Exception('Sep/PA is outside noise map boundaries')
    else:
        return Ias
    
def ComputeSignalSNR(Ip, Is, Ic, Ias, Iqs, tau_as, tau_qs, deltat, strehl, QE, flux_in_core,
                           RN = None, Isky = None, Idc = None, texp = None):
    ''' Get S/N for a planet signal when speckle noise dominated. Using eqns in Chap 7 of
    my thesis.

    Args:
        Ip [flt]: planet signal in photons/sec
        Istar [flt]: star signal in photons/sec
        Ic [flt]: fractional contribution of intensity from residual dirraction from coronagraph
        Ias [flt]: contribution from atm speckles
        Iqs [flt]: fraction from quasistatic speckles
        tau_as [flt]: average lifetime of atm speckles
        tau_qs [flt]: average liftetim of qs speckles
        deltat [flt]: observation time in seconds
        RN [flt]: read noise
        Isky [flt]: sky intensity in photons/sec
        Idc [flt]: dark current in photons/sec
        texp [flt]: time for single exposure in sec (required only for RN term)

    Returns:
        flt: signal to noise ratio
    '''
    # When using the contrast Ias maps, Strelh applies to the numerator but not denom
    # (Males, priv. comm.)
    signal = Ip * deltat * strehl * QE * flux_in_core # Eqn 7.20
    
    Istar = Is * QE * flux_in_core
    photon_noise = Ic + Ias + Iqs
    atm_speckles = Istar * ( tau_as * (Ias**2 + 2*(Ic*Ias + Ias*Iqs)) )
    qs_speckles = Istar * ( tau_qs * (Iqs**2 + 2*Ic*Iqs) )
    
    Ipstar = Ip *  strehl * QE * flux_in_core
    
    sigma_sq_h = Istar * deltat * (photon_noise + atm_speckles + qs_speckles) + signal # Eqn 7.19
    
    if RN is not None:
        skyanddetector = Isky*deltat + Idc*deltat + (RN * deltat/texp)**2
        noise = np.sqrt(sigma_sq_h + skyanddetector)
    else:
        noise = np.sqrt(sigma_sq_h)
        
    return signal / noise



def GetSNR(wavelength, planet_contrast, 
           star_flux,
           primary_mirror_diameter, 
           planet_radius, star_radius, 
           distance, sep, wfc,
           filters, observationtime,
           Ic = 1e-20,
           Iqs = 1e-20,
           tau_as = 0.02, # sec, from Fig 10 in Males+ 2021
           tau_qs = 0.05,
           RN = None, Isky = None, Idc = None, texp = None, pa = None,
           MagAOX = False,
           path_to_maps = '/Users/loganpearce/Dropbox/astro_packages/myastrotools/myastrotools/GMagAO-X-noise/'
          ):
    
    '''Compute S/N as a function of time for a ReflectX model in specific filters.
    
    Args:
        wavelength (arr): array of wavelengths for planet and star spectrum
        planet_contrast (arr): array of planet flux values on wavelength grid
        star_flux (arr): array of star flux on wavelength grid
        primary_mirror_diameter (astropy unit object): mirrior diameter. Ex: 25.4*u.m
        planet_radius (astropy unit object): planet radius
        star_radius (astropy unit object): star radius
        distance (astropy unit object): distance to star
        sep (astropy unit object): planet-star separation
        wfc (str): wavefront control. Either 'lp' or 'si'
        filters (filter object): list of filter objects to compute snr for
        observationtime (arr): array of exposure times
    
    '''
    
    ## 1. Compute star's observed flux from model intensity and compute star's magnitude:
    star_flux = star_flux * ComputeOmega(distance, star_radius)
    star_mag = []
    for i in range(len(filters)):
        filt = filters[i]
        star_mag.append(GetStarMagnitude(star_wavelength, star_flux, filt))
        
    ## 2. Get planet flux from model contrast and distance-corrected star flux:
    planet_flux = star_flux * planet_contrast
    
    ## 3. Compute planet and star signal in photons/sec/lambda/D in each filter:
    planet_signal = []
    for filt in filters:
        planet_signal.append(GetPhotonsPerSec(wavelength, planet_flux, filt, distance, 
                                              planet_radius, primary_mirror_diameter).value)
    planet_signal = np.array(planet_signal)
    
    star_signal = []
    for filt in filters:
        star_signal.append(GetPhotonsPerSec(wavelength, star_flux, filt, distance, 
                                            star_radius, primary_mirror_diameter).value)
    star_signal = np.array(star_signal)
    
    ## 4. Get atmospheric speckle intensity I_as at planet location using maps from Males et al. 2021:
    # Find relevant table:
    star_gsm_for_Ias_tables = []
    for i,filt in enumerate(filters):
        star_gsm_for_Ias_tables.append(GetGuideStarMagForIasTableLookup(star_mag[i]))
    # Get location of planet signal:
    sep_au = sep.to(u.au)
    sep_mas = (sep_au.value/distance.value)*u.arcsec.to(u.mas)
    lods_in_mas = [Get_LOD_in_mas(f.central_wavelength*f.wavelength_unit, primary_mirror_diameter) 
                   for f in filters]
    sep_lods = [sep_mas/lod for lod in lods_in_mas]
    if pa is not None:
        pass
    else:
        pa = 90 # deg
    # Lookup Ias:
    Ias = []
    for i in range(len(filters)):
        wavelength = filters[i].central_wavelength*filters[i].wavelength_unit
        Ias.append(GetIas(star_gsm_for_Ias_tables[i], wfc, sep_lods[i], pa, wavelength))
    Ias = np.array(Ias)
    
    ## 5. Compute throughput:
    # 5a. Get QE (encompasses telescope and instrument throughput):
    if not MagAOX:
        QE = [0.1]*len(filters)
    else:
        QE = [0.13, 0.12, 0.06, 0.04, 0.1, 0.1]
    # 5b. Get Strehl ratio:
    strehl_table = pd.read_table(path_to_maps+f'strehl_{wfc}.txt', 
                                 delim_whitespace=True, names=['mag','strehl'])
    from scipy.interpolate import interp1d
    strehl_table2 = strehl_table.drop([4])
    strehl_table2 = strehl_table2.reset_index(drop=True)
    available_mags = np.array([float(m) for m in strehl_table2['mag']])
    func = interp1d(available_mags, strehl_table2['strehl'])
    strehls = []
    for i in range(len(filters)):
        strehl = func(star_mag[i])
        # scale for wavelength from strehl at 800 nm to filter central wavelength:
        wavelength = filters[i].central_wavelength*filters[i].wavelength_unit
        wavelength = wavelength.to(u.um)
        strehl = strehl * (((0.8*u.um/wavelength))**2).value
        strehls.append(strehl)
    # 5c. Amount of star flux in Airy core:
    star_flux_in_Airy_core_multiple = np.pi/4
    
    ## 6. Compute signal to noise ratios
    if type(observationtime) == np.ndarray:
        # For an array of times:
        all_snrs = []
        for i in range(len(filters)):
            snrs = []
            for t in observationtime:
                snrs.append(ComputeSignalSNR(planet_signal[i], star_signal[i], 
                                             Ic, Ias[i], Iqs, tau_as, tau_qs, t,
                                             strehls[i], QE[i], star_flux_in_Airy_core_multiple,
                                   RN = None, Isky = None, Idc = None, texp = None))
            all_snrs.append(snrs)
        return all_snrs, planet_signal, star_signal
    else:
        # for a single time:
        snrs = []
        for i in range(len(filters)):
            snrs.append(ComputeSignalSNR(planet_signal[i], star_signal[i], Ic, Ias[i], Iqs, tau_as, tau_qs, 
                                observationtime, strehl[i], QE[i], star_flux_in_Airy_core_multiple,
                                RN = RN, Isky = Isky, Idc = Idc, texp = texp))
        return snrs


    