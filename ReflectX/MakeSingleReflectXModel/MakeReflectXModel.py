import picaso.justdoit as jdi
import numpy as np
import astropy.units as u
import astropy.constants as c
import matplotlib.pyplot as plt
import pandas as pd
import os
import argparse
# Make plot look nice:
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['savefig.format'] = 'png'
plt.rcParams['font.family'] = 'serif'
plt.rcParams['axes.titlesize'] = 20.0
plt.rcParams['axes.labelsize'] = 20.0
plt.rcParams['xtick.labelsize'] = 18.0
plt.rcParams['ytick.labelsize'] = 18.0
plt.rcParams['xtick.top'] = True
plt.rcParams['ytick.right'] = True
plt.rcParams['xtick.minor.visible'] = True
plt.rcParams['ytick.minor.visible'] = True
plt.rcParams['ytick.direction'] = 'in'
plt.rcParams['xtick.direction'] = 'in'
plt.rcParams['xtick.major.size'] = 6
plt.rcParams['ytick.major.size'] = 6
plt.rcParams['xtick.minor.size'] = 3
plt.rcParams['ytick.minor.size'] = 6


def UnpackConfig(configfile):
    from configparser import ConfigParser
    # Read in file and parse:
    config = ConfigParser()
    config.read(configfile)
    # Retrieve model parameters:
    modeldict = dict(config['MODEL.CONFIG'])
    # Retrieve star parameters:
    stardict = dict(config['STAR.PARAMS'])
    # Retrieve phase parameters:
    phasedict = dict(config['PHASE.PARAMS'])
    
    #### Retreive Gas Giant planet params:
    if modeldict['modeltype'] == 'GasGiant':
        planetdict = dict(config['GAS.GIANT.PLANET.PARAMS'])
        climatedict = dict(config['CLIMATE.CALCULATION.PARAMS'])
        if planetdict['separation.unit'] == 'au':
            planetdict['separation.unit'] = u.au
        elif planetdict['separation.unit'] == 'km':
            planetdict['separation.unit'] = u.km
        else:
            print('Please enter star-planet separation in au or km')
        planetdict.update({'climatedict':climatedict})
        climatedict = dict(config['CLIMATE.CALCULATION.PARAMS'])
        planetdict.update({'climatedict':climatedict})
        clouddict = dict(config['GAS.GIANT.CLOUD.CONFIG'])
        planetdict.update({'clouddict':clouddict})

    ### Retrieve Terrestrial planet params:
    if modeldict['modeltype'] == 'Terrestrial':
        planetdict = dict(config['TERRESTRIAL.PLANET.PARAMS'])
        atmdict = dict(config['ATMOSPHERE.GASES.AND.CONCENTRATIONS'])
        clouddict = dict(config['GREY.CLOUD.SLAB.CONFIG'])
        newclouddict = {
            'g0' : [float(clouddict['g0'].split(',')[i].replace('[','').replace(']','')) 
     for i in range(int(clouddict['ncloud.levels']))],
            'w0' : [float(clouddict['w0'].split(',')[i].replace('[','').replace(']','')) 
     for i in range(int(clouddict['ncloud.levels']))],
            'opd' : [float(clouddict['opd'].split(',')[i].replace('[','').replace(']','')) 
     for i in range(int(clouddict['ncloud.levels']))],
            'p' : [float(clouddict['p'].split(',')[i].replace('[','').replace(']','')) 
     for i in range(int(clouddict['ncloud.levels']))],
            'dp' : [float(clouddict['dp'].split(',')[i].replace('[','').replace(']','')) 
     for i in range(int(clouddict['ncloud.levels']))],   
        }
        newatmdict = {}
        for key in atmdict.keys():
            newkey = key.upper()
            newatmdict.update({newkey : float(atmdict[key])})
        planetdict.update({'atmdict':newatmdict})
        planetdict.update({'clouddict':newclouddict})

    ### Turn unit strings into astropy units:
    # Gravity:
    if planetdict['gravity'] != 'None':
        if planetdict['gravity.unit'] == 'm/(s**2)':
            pass
        else:
            print('Please enter gravity in m/(s**2)')
    # planet radius:
    if planetdict['radius.unit'] == 'Rsun':
        planetdict['radius.unit'] = u.Rsun
    elif planetdict['radius.unit'] == 'km':
        planetdict['radius.unit'] = u.km
    elif planetdict['radius.unit'] == 'Rjup':
        planetdict['radius.unit'] = u.Rjup
    elif planetdict['radius.unit'] == 'Rearth':
        planetdict['radius.unit'] = u.Rearth
    else:
        print('Please enter planet radius in Rsun, Rjup, Rearth, or km')
    # star radius:
    if stardict['radius.unit'] == 'Rsun':
        stardict['radius.unit'] = u.Rsun
    elif stardict['radius.unit'] == 'km':
        stardict['radius.unit'] = u.km
    else:
        print('Please enter star radius in Rsun or km')
    # planet mass:
    if planetdict['mass'] != 'None':
        if planetdict['mass.unit'] == 'Msun':
            planetdict['mass.unit'] = u.Msun
        elif planetdict['mass.unit'] == 'Mjup':
            planetdict['mass.unit'] = u.Mjup
        elif planetdict['mass.unit'] == 'Mearth':
            planetdict['mass.unit'] = u.Mearth
        elif planetdict['mass.unit'] == 'kg':
            planetdict['mass.unit'] = u.kg
        else:
            print('Please enter planet mass in Msun, Mjup, Mearth, or kg')
    
            
    # unpack wavelength range:
    wavelengthrange = modeldict['wavelength.range']
    wavelengthrange = [float(wavelengthrange.split(',')[0].replace('[','')),
                   float(wavelengthrange.split(',')[1].replace(']',''))]
    modeldict['wavelength.range'] = wavelengthrange
            
    return modeldict,phasedict,planetdict,stardict
    
def MakePTProfile(Teq, Pressure):
    return (0.75 * Teq**4 * (Pressure + 2/3))**(1/4)

def MakeTerrestrialAtmDF(atmdict, pressure, temperature):
    atm = pd.DataFrame({'pressure':pressure,
                        'temperature':temperature,
                        })
    for key in atmdict.keys():
        atm = pd.concat([atm,pd.DataFrame({key:np.zeros(len(pressure))+float(atmdict[key])})], axis=1)
    return atm

def ComputeSMA(Teq, StarTeff, StarRad, Ab = 0.3, fprime = 1/4):
    ''' Given a star's Teff and Rad, compute the separation that gives the 
        specified equil temp.

    Args:
        Teq (flt): planet's equilibrium temperature
        StarTeff (flt): Star's effective temperature
        StarRad (astropy units object): Star's radius, must be an astropy units object
        Ab (flt): Bond albedo, default = 0.3
        fprime (flt): function for describing hemisphere heat distribution, default = 1/4
    Returns
        astropy units object: Planet-Star separation, an astropy units object
    '''
    import astropy.units as u
    StarRad = StarRad.to(u.km)
    sma = (StarTeff / Teq)**2 * ((fprime * (1 - Ab))**(1/2)) * StarRad
    return sma.to(u.au)

def GetPlanetFlux(PlanetWNO,PlanetFPFS,StarWNO,StarFlux, return_resampled_star_flux = False):
    from scipy.interpolate import interp1d
    func = interp1d(StarWNO,StarFlux,fill_value="extrapolate")
    ResampledStarFlux = func(PlanetWNO)
    if return_resampled_star_flux:
        return ResampledStarFlux*PlanetFPFS, PlanetWNO, ResampledStarFlux
    return ResampledStarFlux*PlanetFPFS

def VirgaRecommendHack(pressure, temperature, mh, mmw, 
                       plot=False, return_plot=False, 
                       legend='inside',**plot_kwargs):
    
    from virga.justdoit import available, condensation_t
    from virga.pvaps import NH3
    from virga.justplotit import plot_format
    
    all_gases = available()
    cond_ts = []
    recommend = []
    line_widths = []
    for gas_name in all_gases: #case sensitive names
        if gas_name == 'NH3':
            pass
        else:
            #grab p,t from eddysed
            cond_p,t = condensation_t(gas_name, mh, mmw)
            cond_ts +=[t]

            interp_cond_t = np.interp(pressure,cond_p,t)

            diff_curve = interp_cond_t - temperature

            if ((len(diff_curve[diff_curve>0]) > 0) & (len(diff_curve[diff_curve<0]) > 0)):
                recommend += [gas_name]
                line_widths +=[5]
            else: 
                line_widths +=[1] 
    # NH3:
    temp = np.linspace(10,400,1000)
    pvapNH3 = NH3(temp)
    interp_cond_t = np.interp(pressure,pvapNH3,temp)
    diff_curve = interp_cond_t - temperature
    if ((len(diff_curve[diff_curve>0]) > 0) & (len(diff_curve[diff_curve<0]) > 0)):
        recommend += ['NH3']
        line_widths +=[5]
    else: 
        line_widths +=[1]  
    return recommend

def ConvertPlanetMHtoCKStr(m):
    prefixsign = np.sign(m)
    if prefixsign == -1:
        prefix = '-'
    else:
        prefix = '+'
    m = int(np.abs(m))
    if m / 100 >= 1.0:
        m = prefix+str(m)
    elif m == 0:
        m = '+000'
    else:
        m = prefix+'0'+str(m)
    return m

def ConvertLogPlanetMHtoCKStr(m):
    prefixsign = np.sign(m)
    if prefixsign == -1:
        prefix = '-'
    else:
        prefix = '+'
    m = m * 100
    if m >= 100:
        m = prefix+str(m).replace('.0','')
    elif m == 0:
        m = '+000'
    else:
        m = prefix+'0'+str(m).replace('.0','')
    return m

def ConvertCtoOtoStr(c):
    if c >= 1:
        cc = str(c*100).replace('.0','')
    else:
        cc = '0'+str(c*100).replace('.0','')
    return cc

def ComputeTeq(StarTeff, StarRad, sep, Ab = 0.3, fprime = 1/4):
    ''' Given a star's Teff and Rad, compute the equil temp at the given separation.
    from Seager 2016 Exoplanet Atmospheres eqn 3.9
    https://books.google.com/books?id=XpaYJD7IE20C

    Args:
        StarTeff (flt): Star's effective temperature
        StarRad (astropy units object): Star's radius, must be an astropy units object
        sep (astropy units object): Planet-Star separation, must be an astropy units object
        Ab (flt): Bond albedo, default = 0.3
        fprime (flt): function for describing hemisphere heat distribution, default = 1/4
    Returns
        flt: equilibrium temperature
    '''
    StarRad = StarRad.to(u.km)
    sep = sep.to(u.km)
    return (StarTeff * np.sqrt(StarRad/sep) * ((fprime * (1 - Ab))**(1/4))).value

def BuildTerrestrialPlanet(configfile,modeldict,phasedict,planetdict,stardict):
    print('Connecting to opacity db')
    opa_mon = jdi.opannection(filename_db = modeldict['opacity.db'], 
                                 wave_range=modeldict['wavelength.range'])
    print('Building terrestrial model')
    ######## Make PT Profile:
    Pressure = 10**np.linspace(-6,2, 60)
    Temperature = MakePTProfile(float(planetdict['teq']), Pressure)
    #if initiate_opacity_db:
    #    print('initializing opacity database')
    #    ######## Initialize opacity:
    #    opa_mon = jdi.opannection(filename_db = modeldict['opacity.db'], wave_range=modeldict['wavelength.range'])
    
    ######## Make Picaso model:
    # Initialize model:
    pl = jdi.inputs(calculation= "planet", climate=False)
    # Set gravity:
    if planetdict['gravity'] != 'None':
        gravity = float(planetdict['gravity']) * jdi.u.Unit(planetdict['gravity.unit'])
        Rplanet = float(planetdict['radius'])*planetdict['radius.unit']
        Mplanet = (gravity * (Rplanet.to(u.m))**2/ c.G).to(u.Mearth)
        pl.gravity(radius=float(planetdict['radius']), radius_unit=planetdict['radius.unit'],
                  mass = Mplanet.value, mass_unit=u.Mearth)
    else:
        pl.gravity(radius=float(planetdict['radius']), radius_unit=planetdict['radius.unit'], 
            mass = float(planetdict['mass']), mass_unit=planetdict['mass.unit'])
        Mplanet = float(planetdict['mass']*planetdict['mass.unit'])
        Rplanet = (float(planetdict['radius'])*planetdict['radius.unit'])
        gravity = c.G * (Mplanet) / ((Rplanet)**2)
        gravity = gravity.to(u.m/(u.s**2))
                         
    # Set surface albedo:
    pl.surface_reflect(float(planetdict['surface.albedo']),opa_mon.wno)
    # Set phase:
    phase = int(phasedict['phase'])
    # If full phase:
    if phase == 0:
        # Use symmetry to speed up calculation.
        num_tangle = 1
    else:
        num_tangle = int(phasedict['numtangle'])
    pl.phase_angle(phase=phase*np.pi/180, num_tangle=num_tangle, num_gangle=int(phasedict['ngangle']))
    # Set atm:
    atm = MakeTerrestrialAtmDF(planetdict['atmdict'], Pressure, Temperature)
    pl.atmosphere(df=atm)
    # Get separation:
    sep = ComputeSMA(float(planetdict['teq']), float(stardict['teff']), 
                     float(stardict['radius'])*stardict['radius.unit'], 
                     Ab = 0.3, fprime = 1/4).value
    # Star:
    pl.star(opa_mon,temp=float(stardict['teff']), metal=np.log10(float(stardict['metallicity'])), 
            logg=float(stardict['logg']), radius = float(stardict['radius']), 
            radius_unit=stardict['radius.unit'],
            semi_major=sep, semi_major_unit = u.au,
            database=stardict['star.model.database'])
    
    # Store output spectra:
    columns = ['wavelength [um]']
    out = pd.DataFrame(columns=columns)
    dominantgas = max(planetdict['atmdict'], key=planetdict['atmdict'].get)
    clouds = VirgaRecommendHack(Pressure, Temperature, 1, 2.2)
    comments = '# ReflectX Terrestrial Planet Reflected Light PICASO model spectra \n'
    comments += '# for a world with '+dominantgas+' dominant atm and '+str(clouds)+' clouds \n'
    comments += '# and r='+str(Rplanet)+', m='+str(np.round(Mplanet,decimals=2))+', and grav='+str(gravity)+'\n'
    comments += '# with '+str(stardict['teff'])+'K/'+str(stardict['radius'])+'Rsun/logg'+str(stardict['logg'])+' star at '+str(np.round(sep,decimals=1))+' au \n'
    comments += '# Spectra are R=60,000; to get a different gridding use picaso.justdoit.mean_regrid \n'
    comments += '# Columns delinate the radius and mass of the planet and cloudy vs no clouds; columns labeled \n'
    comments += '# "fpfs" are the planet/star flux ratio spectrum, columns labeled "PlanetFlux" are the planet spectrum only\n'
    comments += '# All flux in units of ergs cm$^{-2}$ s$^{-1}$ cm$^{-1}$ \n \n'
    os.system('mkdir '+modeldict['output.directory']+modeldict['directory.filename'])
    outputfilename = modeldict['output.directory']+modeldict['directory.filename']+'/ReflectX_spectra.csv'
    outfile = open(outputfilename,'w')
    outfile.close()
    outfile = open(outputfilename,'a')
    outfile.write(comments)
    
    ### Generate cloud-free spectra:
    print('computing cloud-free spectra')
    noclouds_spec = pl.spectrum(opa_mon, calculation='reflected')
    wno, alb, fpfs = noclouds_spec['wavenumber'], noclouds_spec['albedo'], \
                                                noclouds_spec['fpfs_reflected']
    StarWNO,StarFlux = pl.inputs['star']['wno'],pl.inputs['star']['flux']
    PlanetFlux, StarWNO, ResampledStarFlux = GetPlanetFlux(wno, fpfs, StarWNO, StarFlux, return_resampled_star_flux = True)
    out['wavelength [um]'] = 1e4/wno
    out['StarFlux'] = ResampledStarFlux
    out['cloud-free-albedo'] = alb
    out['cloud-free-fpfs'] = fpfs
    out['cloud-free-PlanetFlux'] = PlanetFlux

    ### Add clouds and generate cloudy spectra:
    print('computing cloudy spectra')
    pl.clouds(g0=planetdict['clouddict']['g0'], 
              w0=planetdict['clouddict']['w0'], 
              opd=planetdict['clouddict']['opd'], 
              p = planetdict['clouddict']['p'], 
              dp=planetdict['clouddict']['dp'])
    
    cloudy_spec = pl.spectrum(opa_mon, calculation='reflected')
    wno, alb, fpfs = cloudy_spec['wavenumber'], cloudy_spec['albedo'], \
                                                cloudy_spec['fpfs_reflected']
    StarWNO,StarFlux = pl.inputs['star']['wno'],pl.inputs['star']['flux']
    PlanetFlux = GetPlanetFlux(wno, fpfs, StarWNO, StarFlux)
    out['cloudy-albedo'] = alb
    out['cloudy-fpfs'] = fpfs
    out['cloudy-PlanetFlux'] = PlanetFlux
    
    # Write to file:
    out.to_csv(outfile, index=False)
    outfile.close()
    import pickle
    pickle.dump(pl,open(modeldict['output.directory']+modeldict['directory.filename']+'/model.pkl','wb'))
    
    # clouds figure:
    from virga.pvaps import NH3
    from virga.justdoit import available, condensation_t
    all_gases = available()
    temp = np.linspace(10,400,1000)
    pvapNH3 = NH3(temp)
    gases = np.delete(all_gases,11)
    cond_ts = []
    for gas_name in gases: #case sensitive names
        #grab p,t from eddysed
        cond_p,t = condensation_t(gas_name, 1, 2.2)
        cond_ts +=[t]
    import matplotlib
    cmap = matplotlib.colormaps.get_cmap('plasma')
    colors = cmap(np.linspace(0,1,len(gases)+2))
    fig = plt.figure(figsize=(8,6))
    
    for i in range(1,len(gases)):
        plt.plot(cond_ts[i],cond_p, color=colors[i], label=gases[i])
    plt.plot(temp,pvapNH3, color=colors[-1], label='NH3')
    plt.plot(Temperature,Pressure,ls='-.',lw=2,color='black')
    plt.gca().set_yscale('log')
    plt.gca().invert_yaxis()
    plt.ylim(1e2,1e-6)
    plt.xlabel('Temperature [K]')
    plt.ylabel('Pressure [bars]')
    plt.legend(loc=(1.01,0))
    plt.tight_layout()
    plt.savefig(modeldict['output.directory']+modeldict['directory.filename']+'/PTprofile.png')
    os.system('cp '+configfile+' '+modeldict['output.directory']+modeldict['directory.filename'])
    print('Done. Spectra and model written to '+outputfilename)

def BuildGasGiantPlanet(configfile,modeldict,phasedict,planetdict,stardict, initiate_opacity_db = False):
    print('Connecting to opacity db')
    opa_mon = jdi.opannection(filename_db = modeldict['opacity.db'], 
                                 wave_range=modeldict['wavelength.range'])
    
    print('Building gas giant model')
        
    ######## Make Picaso model:
    # Initialize model:
    pl = jdi.inputs(calculation= "planet", climate = True)
    
    # Use t_int as initial effective temp:
    pl.effective_temp(float(planetdict['tint']) )
    
    # Set gravity:
    if planetdict['gravity'] != 'none':
        gravity = float(planetdict['gravity']) * jdi.u.Unit(planetdict['gravity.unit'])
        Rplanet = float(planetdict['radius'])*planetdict['radius.unit']
        Mplanet = (gravity * (Rplanet.to(u.m))**2/ c.G).to(u.Mearth)
        pl.gravity(radius=float(planetdict['radius']), radius_unit=planetdict['radius.unit'],
                  mass = Mplanet.value, mass_unit=u.Mearth)
    else:
        pl.gravity(radius=float(planetdict['radius']), radius_unit=planetdict['radius.unit'], 
            mass = float(planetdict['mass']), mass_unit=planetdict['mass.unit'])
        Mplanet = float(planetdict['mass'])*planetdict['mass.unit']
        Rplanet = (float(planetdict['radius'])*planetdict['radius.unit'])
        gravity = c.G * (Mplanet) / ((Rplanet)**2)
        gravity = gravity.to(u.m/(u.s**2))
        
#     # Set phase:
    phase = int(phasedict['phase'])
    # If full phase:
    if phase == 0:
        # Use symmetry to speed up calculation.
        num_tangle = 1
    else:
        num_tangle = int(phasedict['numtangle'])
    pl.phase_angle(phase=phase*np.pi/180, num_tangle=num_tangle, num_gangle=int(phasedict['ngangle']))
    
    # Set up climate run:
    PlanetCO = ConvertCtoOtoStr(float(planetdict['ctoo']))
    PlanetMHStr = ConvertLogPlanetMHtoCKStr(float(planetdict['log.metallicity']))
    if planetdict['tiovo'] == 'no':
        ck_db_name = planetdict['path.to.correlated.k-coefficient.files'] + f'sonora_2020_feh{PlanetMHStr}_co_{PlanetCO}_noTiOVO.data.196'
    elif planetdict['tiovo'] == 'yes':
        ck_db_name = planetdict['path.to.correlated.k-coefficient.files'] + f'sonora_2020_feh{PlanetMHStr}_co_{PlanetCO}.data.196'
    opacity_ck = jdi.opannection(ck_db=ck_db_name, wave_range = modeldict['wavelength.range'])
    
    # Star:
    pl.star(opacity_ck, temp=float(stardict['teff']), metal=np.log10(float(stardict['metallicity'])), 
            logg=float(stardict['logg']), radius = float(stardict['radius']), 
            radius_unit=stardict['radius.unit'],
            semi_major=float(planetdict['separation']), semi_major_unit = planetdict['separation.unit'],
            database=stardict['star.model.database'])
    
    # Compute Teq:
    Teq = ComputeTeq(float(stardict['teff']), float(stardict['radius'])*u.Rsun, 
                     float(planetdict['separation'])*planetdict['separation.unit'], 
                     Ab = 0.3, fprime = 1./4.)
    
    # Use Guillot PT as initial PT guess:
    climatedict = planetdict['climatedict']
    pt = pl.guillot_pt(Teq, nlevel=int(climatedict['nlevel']), T_int = int(planetdict['tint']), 
                    p_bottom=int(climatedict['bottom.pressure']), p_top=int(climatedict['top.pressure']))
    
    # Input climate params:
    # initial guess of convective zones
    nstr = np.array([0,int(climatedict['nstr_upper']),int(climatedict['nstr_deep']),0,0,0])
    temp_guess = pt['temperature'].values 
    press_guess = pt['pressure'].values
    pl.inputs_climate(temp_guess= temp_guess, pressure= press_guess, 
                  nstr = nstr, nofczns = int(climatedict['nofczns']), rfacv = float(climatedict['rfacv']))
    
    
    print('starting climate run')
    # Compute climate:
    noclouds = pl.climate(opacity_ck, save_all_profiles=True, with_spec=True)
    # Set atm to climate run results:
    pl.atmosphere(df=noclouds['ptchem_df'])
    
    # Store output spectra:
    columns = ['wavelength [um]']
    out = pd.DataFrame(columns=columns)
    clouds = VirgaRecommendHack(noclouds['pressure'], noclouds['temperature'], 1, 2.2)
    if 'SiO2' in clouds:
        clouds.remove('SiO2')
        
    comments = '# ReflectX Gas Giant Planet Reflected Light PICASO model spectra \n'
    comments += '# for a world with r='+str(Rplanet)+', m='+str(np.round(Mplanet,decimals=2))+', and grav='+str(gravity)+'\n'
    comments += '# and '+str(clouds)+' clouds \n'
    comments += '# with '+str(stardict['teff'])+'K/'+str(stardict['radius'])+'Rsun/logg'+str(stardict['logg'])+\
                ' star at '+str(np.round(float(planetdict['separation']),decimals=1))+' au \n'
    comments += '# Spectra are R=60,000; to get a different gridding use picaso.justdoit.mean_regrid \n'
    comments += '# Columns delinate the radius and mass of the planet and cloudy vs no clouds; columns labeled \n'
    comments += '# "fpfs" are the planet/star flux ratio spectrum, columns labeled "PlanetFlux" are the planet spectrum only\n'
    comments += '# All flux in units of ergs cm$^{-2}$ s$^{-1}$ cm$^{-1}$ \n'
    os.system('mkdir '+modeldict['output.directory']+modeldict['directory.filename'])
    outputfilename = modeldict['output.directory']+modeldict['directory.filename']+'/ReflectX_spectra.csv'
    outfile = open(outputfilename,'w')
    outfile.close()
    outfile = open(outputfilename,'a')
    outfile.write(comments)
    
    ### Generate cloud-free spectra:
    print('computing cloud-free spectra')

    # make a new spectrum object with different opacity db:
    spec = jdi.inputs(calculation= "planet", climate = True)
    spec.effective_temp(float(planetdict['tint']) )
    if planetdict['gravity'] != 'none':
        gravity = float(planetdict['gravity']) * jdi.u.Unit(planetdict['gravity.unit'])
        Rplanet = float(planetdict['radius'])*planetdict['radius.unit']
        Mplanet = (gravity * (Rplanet.to(u.m))**2/ c.G).to(u.Mearth)
        spec.gravity(radius=float(planetdict['radius']), radius_unit=planetdict['radius.unit'],
                  mass = Mplanet.value, mass_unit=u.Mearth)
    else:
        spec.gravity(radius=float(planetdict['radius']), radius_unit=planetdict['radius.unit'], 
            mass = float(planetdict['mass']), mass_unit=planetdict['mass.unit'])
        Mplanet = float(planetdict['mass'])*planetdict['mass.unit']
        Rplanet = (float(planetdict['radius'])*planetdict['radius.unit'])
        gravity = c.G * (Mplanet) / ((Rplanet)**2)
        gravity = gravity.to(u.m/(u.s**2))
    phase = int(phasedict['phase'])
    # If full phase:
    if phase == 0:
        # Use symmetry to speed up calculation.
        num_tangle = 1
    else:
        num_tangle = int(phasedict['numtangle'])
    spec.phase_angle(phase=phase*np.pi/180, num_tangle=num_tangle, num_gangle=int(phasedict['ngangle']))
    spec.star(opa_mon, temp=float(stardict['teff']), metal=np.log10(float(stardict['metallicity'])), 
            logg=float(stardict['logg']), radius = float(stardict['radius']), 
            radius_unit=stardict['radius.unit'],
            semi_major=float(planetdict['separation']), semi_major_unit = planetdict['separation.unit'],
            database=stardict['star.model.database'])
    Teq = ComputeTeq(float(stardict['teff']), float(stardict['radius'])*u.Rsun, 
                     float(planetdict['separation'])*planetdict['separation.unit'], 
                     Ab = 0.3, fprime = 1./4.)
    spec.atmosphere(df=noclouds['ptchem_df'])

    noclouds_spec = spec.spectrum(opa_mon, calculation='reflected')
    wno, alb, fpfs = noclouds_spec['wavenumber'], noclouds_spec['albedo'], \
                                                noclouds_spec['fpfs_reflected']
    StarWNO,StarFlux = pl.inputs['star']['wno'],pl.inputs['star']['flux']
    PlanetFlux, StarWNO, ResampledStarFlux = GetPlanetFlux(wno, fpfs, StarWNO, StarFlux, return_resampled_star_flux = True)
    out['wavelength [um]'] = 1e4/wno
    out['StarFlux'] = ResampledStarFlux
    out['cloud-free-albedo'] = alb
    out['cloud-free-fpfs'] = fpfs
    out['cloud-free-PlanetFlux'] = PlanetFlux
    
    ### Cloudy spectra:
    # Add kzz to the atmosphere dataframe:
    clouddict = planetdict['clouddict']
    atm = noclouds['ptchem_df']
    atm['kz'] = [float(clouddict['kzz'])]*atm.shape[0]
    spec.atmosphere(df=atm)
    metallicity_TEMP = 0
    clouds_added = spec.virga(clouds, clouddict['meiff.directory'], 
                            fsed= float(clouddict['fsed']), mh=10**(metallicity_TEMP),
                            mmw = float(clouddict['mmw']), full_output=True)
    
    ### generate cloudy spectra:
    print('computing cloudy spectra')
    cloudy_spec = spec.spectrum(opa_mon, calculation='reflected')
    wno2, alb2, fpfs2 = cloudy_spec['wavenumber'], cloudy_spec['albedo'], \
                                                cloudy_spec['fpfs_reflected']
    StarWNO,StarFlux = spec.inputs['star']['wno'],spec.inputs['star']['flux']
    PlanetFlux2 = GetPlanetFlux(wno2, fpfs2, StarWNO, StarFlux)
    out['cloudy-albedo'] = alb2
    out['cloudy-fpfs'] = fpfs2
    out['cloudy-PlanetFlux'] = PlanetFlux2

    # Write to file:
    out.to_csv(outfile, index=False)
    
    outfile.close()
    import pickle
    pickle.dump(spec,open(modeldict['output.directory']+modeldict['directory.filename']+'/model.pkl','wb'))
    
    # clouds figure:
    from virga.pvaps import NH3
    from virga.justdoit import available, condensation_t
    all_gases = available()
    temp = np.linspace(10,400,1000)
    pvapNH3 = NH3(temp)
    gases = np.delete(all_gases,11)
    cond_ts = []
    for gas_name in gases: #case sensitive names
        #grab p,t from eddysed
        cond_p,t = condensation_t(gas_name, 1, 2.2)
        cond_ts +=[t]
    import matplotlib
    cmap = matplotlib.colormaps.get_cmap('plasma')
    colors = cmap(np.linspace(0,1,len(gases)+2))
    fig = plt.figure()
    for i in range(1,len(gases)):
        plt.plot(cond_ts[i],cond_p, color=colors[i], label=gases[i])
    plt.plot(temp,pvapNH3, color=colors[-1], label='NH3')
    plt.plot(atm['temperature'],atm['pressure'],ls='-.',lw=2,color='black')
    plt.gca().set_yscale('log')
    plt.gca().invert_yaxis()
    plt.ylim(1e2,1e-6)
    plt.legend(loc=(1.01,0))
    plt.tight_layout()
    plt.xlabel('Temperature [K]')
    plt.ylabel('Pressure [bars]')
    plt.savefig(modeldict['output.directory']+modeldict['directory.filename']+'/PTprofile.png')
    os.system('cp '+configfile+' '+modeldict['output.directory']+modeldict['directory.filename'])
    print('Done. Spectra and model written to '+outputfilename)
    

parser = argparse.ArgumentParser(
                    prog='MakeReflectXModel',
                    description='Make a single picaso reflected light model')
parser.add_argument('configfile')
args = parser.parse_args()
configfile = args.configfile

modeldict,phasedict,planetdict,stardict = UnpackConfig(configfile)
if modeldict['modeltype'] == 'GasGiant':
    BuildGasGiantPlanet(configfile,modeldict,phasedict,planetdict,stardict)
elif modeldict['modeltype'] == 'Terrestrial':
    BuildTerrestrialPlanet(configfile,modeldict,phasedict,planetdict,stardict)