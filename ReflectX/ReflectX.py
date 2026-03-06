import numpy as np
import astropy.constants as const
import astropy.units as u
import pandas as pd
import pickle
import scipy
import xarray as xr
import h5netcdf
import scipy


def LoadModel(path, Teff, Planet, CtoO, teq = None, phase = None, clouds = None):
    """
    Args:
        path (str): Path to location of `ReflectX` folder containing models
        Teff (int): Star effective temperature, must be 3000, 3500, 4000, 5000, or 7000
        Planet (str): Specify planet (see docs for details of each planet type); must be Neptune, SuperNeptune, Saturn, Jupiter, or SuperJupiter
        CtoO (float): Planet C/O ratio; must be 0.5, 1.0, or 1.5
        teq (int): Planet equilibrium temperature; must be 75, 100, 150, 180, 200, 250, 300, or 500
        phase (int): Planet viewing phase in degrees; must be 0, 45, 90, 120, or 140
        clouds (dict): Dictionary of cloud properties, must contain keys `fsed` and `kzz`; fsed must be 0.1, 0.5, 1, 3, 6, 0r 10; kzz must be 1e9 or 1e11

    Returns:
        dict or XArray: entire model set as a dictionary or single spectrum as an XArray
    """
    loaded = {}
    CtoO = str(CtoO).replace('.','')
    filename = path + '/Teff'+str(Teff)+'/'+Planet+'/CtoO'+CtoO+'/model.nc'
    with h5netcdf.File(filename, "r+") as f:
        def recurse(group, prefix=""):
            for name, subgrp in group.groups.items():
                full_path = f"{prefix}/{name}".strip("/")
                # If the subgroup contains variables, open it as an xarray dataset
                if subgrp.variables:
                    ds = xr.open_dataset(
                        filename,
                        engine="h5netcdf",
                        group=full_path,
                    )
                    loaded[full_path] = ds
                # Recurse deeper
                recurse(subgrp, full_path)
        recurse(f)
    if teq == None:
        return loaded
    else:
        key = 'teq'+str(teq)+'/phase'+str(phase)
        if clouds == None:
            key += '/cloudfree'
        else:
            if type(clouds['kzz']) == float:
                kzz = '{:.0e}'.format(clouds['kzz'])
            elif type(clouds['kzz']) == str:
                kzz = clouds['kzz']
            key += '/fsed'+str(clouds['fsed']).replace('.','')+'/kzz'+kzz
        return loaded[key]

def CreateGrid(min_wavelength, max_wavelength, constant_R):
    """
    Simple function to create a wavelength grid defined with a constant R.
    Adapted from PICASO create_grid function
    https://github.com/natashabatalha/picaso/blob/defc72955ad468496a814c1300e0f57244a75cd6/picaso/opacity_factory.py#L667C1-L694C27

    Args:
        min_wavelength (float): min value of wavelength range
        max_wavelength (float): max value of wavelength range
        constant_R (int): R value, ex: 10000

    Returns:
        arr: new wavelength grid at specified R value
    """
    spacing = (2.*constant_R+1.)/(2.*constant_R-1.)
    
    npts = np.log(max_wavelength/min_wavelength)/np.log(spacing)
    
    wsize = int(np.ceil(npts))+1
    newwl = np.zeros(wsize)
    newwl[0] = min_wavelength
    
    for j in range(1,wsize):
        newwl[j] = newwl[j-1]*spacing
    
    return newwl
    
def MeanRegrid(x, y, newx=None, R=None):
    """
    Rebin the spectrum. Adapted from PICASO mean_regrid function
    https://github.com/natashabatalha/picaso/blob/defc72955ad468496a814c1300e0f57244a75cd6/picaso/justplotit.py#L31C1-L63C19
    
    Args:
        x (arr): wavelength array to be rebinned
        y (arr): flux values to map to new wavelength grid
        newx (arr): new wavelength array to map flux onto, required if R = None
        R (int): desired R to construct new wavelength array to map flux onto, required if newx = None

    Returns:
        tuple containing

        - newx (arr): new wavelength array
        - newy (float): new flux array mapped onto new wavelength at desired R
    """
    from scipy.stats import binned_statistic
    if (isinstance(newx, type(None)) & (not isinstance(R, type(None)))) :
        newx = CreateGrid(min(x), max(x), R)
    elif (not isinstance(newx, type(None)) & (isinstance(R, type(None)))) :  
        d = np.diff(newx)
        binedges = np.array([newx[0]-d[0]/2] + list(newx[0:-1]+d/2.0) + [newx[-1]+d[-1]/2])
        newx = binedges
    else: 
        raise Exception('Please either enter a newx or a R') 
    newy, edges, binnum = binned_statistic(x,y,bins=newx)
    newx = (edges[0:-1]+edges[1:])/2.0

    return newx, newy

def LoadFilters():
    '''
    Load XArray of filter transmission profiles
    '''
    import os
    file = os.path.join(os.path.dirname(__file__),"filters.nc")
    filt = xr.open_dataset(file, engine="h5netcdf")
    return filt

def ScaleModelToStar(model, distance):
    """
    Scale star and planet flux arrays from surface to flux arriving at Earth

    Args:
        model (XArray): model XArray
        distance (float): distance to star in parsecs

    Returns:
        XArray: XArray of model with star and planet flux scaled to flux arriving at Earth
    """
    omega = ((float(model.attrs['star.radius'])*u.Rsun / (distance*u.pc)).decompose())**2
    data_vars=dict(starflux = (["wavelength"], 
                                      model['starflux'].data * omega,
                                      {'units': 'erg/cm**2/s/cm/'}),
                   albedo = (["wavelength"], model['albedo'].data,{'units': ''}),
                  fpfs = (["wavelength"], model['fpfs'].data,{'units': 'erg/cm**2/s/cm/'}),
                  planetflux = (["wavelength"], model['starflux'].data * omega * model['fpfs'].data,{'units': 'erg/cm**2/s/cm/'})
                  )
    coords=dict(
                wavelength=(["wavelength"], model.wavelength.values,{'units': 'micron'})
            )
    scaled_model = xr.Dataset(
                data_vars=data_vars,
                coords=coords,
            )
    return scaled_model

def GetFluxInFilter(wavelength, flux, filterwavelength, filtertransmission):
    ''' Compute the average flux in a filter by multiplying the spectrum by the filter transmission curve
    and dividing by the filter transmission curve
    
    Args:
        wavelength (arr): wavelength array
        flux (arr): flux array
        filterwavelength (arr): filter wavelength array
        filtertransmission (arr): filter transmission curve

    Returns:
        float: weighted average flux in filter
    '''
    # resample if necessary:  
    if wavelength.shape[0] != filtertransmission.shape[0]:
        from scipy.interpolate import interp1d
        filterwavelength = np.pad(filterwavelength,(1,1),constant_values=(2.01,0.2))
        filtertransmission = np.pad(filtertransmission,(1,1), constant_values=(0,0))
        func = interp1d(filterwavelength,filtertransmission)
        filtertransmission = func(wavelength)
        
    dl = [wavelength[i] - wavelength[i-1] for i in range(1,len(wavelength))]
    dl.append(dl[-1])
    filter_weighted_average = np.sum(flux * filtertransmission * wavelength * dl) / np.sum(filtertransmission * wavelength * dl)
    return filter_weighted_average


def VegaToAB(filt):
    ''' The SDSS system uses AB mags not Vega mags.  To convert Vega mags to AB mag, add this  
    value to the Vega mag to convert to AB. These factors = AB - Vega
    From https://www.astronomy.ohio-state.edu/martini.10/usefuldata.html
    '''
    Dict = {
        'U':0.79,
        'B':-0.09,
        'V':0.02,
        'R':0.21,
        'I':0.45,
        'J':0.91,
        'H':1.39,
        'Ks':1.85,
        'u':0.91,
        'g':-0.08,
        'r':0.16,
        'i':0.37,
        'z':0.54,
        'Y':0.634
    }
    return Dict[filt]

def GetMagInFilter(wavelength, flux, filtername = None, filterwavelength = None, filtertransmission = None):
    ''' For a given stellar spectrum in a specific filter, return the Vega magnitude of the star in 
    that filter.
    
    Args:
        spectrum_wavelength [arr]: spectrum wavelength
        spectrum_flux [arr]: spectrum flux
        filter_lamda0 [astropy unit object]: central wavelength of filter. Must include astropy unit
                Ex: 1.2*u.um
        spectrum_wavelength_unit [astropy unit]: astropy unit for wavelengths. Ex: u.um

    Returns:
        flt: ratio of spectrum to Vega flux in that filter in magnitudes, with correction to AB mags for SDSS filters.
    
    '''
    filters = LoadFilters()
    specflux = GetFluxInFilter(wavelength, flux, filtername = filtername, filterwavelength = filterwavelength, 
                               filtertransmission = filtertransmission)
    vegaflux = GetFluxInFilter(filters.vegawave[::-1], filters.vega[::-1], filtername = filtername, filterwavelength = filterwavelength, 
                               filtertransmission = filtertransmission)
    # return ratio of spectrum to vega in magnitudes:
    if 'SDSS' in filtername:
        factor = VegaToAB(filtername.replace('SDSS',''))
        return -2.5*np.log10(specflux/vegaflux) + factor
    else:
        return -2.5*np.log10(specflux/vegaflux)



