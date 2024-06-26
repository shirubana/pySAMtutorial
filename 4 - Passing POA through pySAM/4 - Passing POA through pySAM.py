#!/usr/bin/env python
# coding: utf-8

# # 4 - Passing POA through pySAM
# 
# 
# Needs a weatherfile with a "POA" column input; do not include DNI DHI or GHI on the weatherfile.
# 
# Using open-source modules from row 4 as baseline. LONGi Green Energy Technology Co._Ltd. LR6-72PH-370M

# In[1]:


import PySAM
import PySAM.Pvsamv1 as PV
import PySAM.Grid as Grid
import PySAM.Utilityrate5 as UtilityRate
import PySAM.Cashloan as Cashloan
import pathlib, os
import json
import pvlib
import pandas as pd


# In[2]:


import sys, platform
print("Working on a ", platform.system(), platform.release())
print("Python version ", sys.version)
print("Pandas version ", pd.__version__)
print("Pvlib version: ", pvlib.__version__)
print("PySAM version: ", PySAM.__version__)


# In[3]:


sif4 = 'Row4Json'
sif4 = 'Newjson'

jsonnames = ['Row4PrismBifi']

file_names = ["pvsamv1", "grid", "utilityrate5", "cashloan"]

pv4 = PV.new()  # also tried PVWattsSingleOwner
grid4 = Grid.from_existing(pv4)
ur4 = UtilityRate.from_existing(pv4)
so4 = Cashloan.from_existing(grid4, 'FlatPlatePVCommercial')


# In[10]:


for count, module in enumerate([pv4, grid4, ur4, so4]):
    filetitle= 'Row4LongiBifi' + '_' + file_names[count] + ".json"
    with open(os.path.join(sif4,filetitle), 'r') as file:
        data = json.load(file)
        for k, v in data.items():
            if k == 'number_inputs':
                continue
            try:
                if sys.version.split(' ')[0] == '3.11.7': 
                    # Check needed for python 3.10.7 and perhaps other releases above 3.10.4.
                    # This prevents the failure "UnicodeDecodeError: 'utf-8' codec can't decode byte... 
                    # This bug will be fixed on a newer version of pysam (currently not working on 5.1.0)
                    if 'adjust_' in k:  # This check is needed for Python 3.10.7 and some others. Not needed for 3.7.4
                        print(k)
                        k = k.split('adjust_')[1]
                module.value(k, v)
            except AttributeError:
                # there is an error is setting the value for ppa_escalation
                print(module, k, v)


# ##### Sanity checks

# In[11]:


pv4.SolarResource.solar_resource_file
pv4.SolarResource.use_wf_albedo
pv4.SolarResource.irrad_mode
pv4.SolarResource.albedo


# # LOOP THROUGH COMBOS

# In[ ]:


# For unknown reasons, pySAM does not calculate this number and you have to obtain it from the GUI.
system_capacity4 = 73.982   


# In[ ]:


# TODO: TRACKER ANGLES: Load tracker angles here into an array the same length as the weatherfile (8760). 
trackerangles = # 


# In[ ]:


sims = ['WF_SAM_P00.csv'] # Weather file(s) with "POA" column input.
ResultsFolder = r'Results'


# In[ ]:


dfAll = pd.DataFrame()

for ii in range(0, len(sims)): # # loop here over all the weather files or sims.
    print("***** \n** Sim", ii)

    weatherfile = sims[ii]
    savefilevar = os.path.join(ResultsFolder,'Results_pySAM_'+sims[ii]+'.csv')

    wftimestamp = pd.read_csv(weatherfile, skiprows=2)
    datelist = list(pd.to_datetime(wftimestamp.iloc[:,0:4]))
    months = list(wftimestamp.iloc[:,1])
    years = list(wftimestamp.iloc[:,0])
    days = list(wftimestamp.iloc[:,2])
    hours = list(wftimestamp.iloc[:,3])
    minutes = list(wftimestamp.iloc[:,4])
    
    pv4.SolarResource.solar_resource_file = weatherfile
    
    pv4.SolarResource.irrad_mode = 3 # [0/1/2/3/4] Beam+Diff,Global+Beam, Global+Diff, POA Ref cell, POA Pyranometer
    pv4.SolarResource.sky_model= 2 #  [0/1/2] Isotropic,HDKR,Perez

    # So that irrad_mod for POA works shading has to be inactivated.
    if pv4.SolarResource.irrad_mode >= 3:
        pv4.Shading.subarray1_shade_mode = 0
    else:
        pv4.Shading.subarray1_shade_mode = 1.0

    # Using custom tracker angles
    pv4.SystemDesign.subarray1_use_custom_rot_angles = 1
    pv4.SystemDesign.subarray1_custom_rot_angles_array = trackerangles # MUST BE same length as weatherfile.

    grid4.SystemOutput.gen = [0] * len(datelist)  # p_out   # let's set all the values to 0
    pv4.execute()
    grid4.execute()
    ur4.execute()
    so4.execute()

    # SAVE RESULTS|
    results = pv4.Outputs.export()
    power4 = list(results['subarray1_dc_gross']) # normalizing by the system_capacity
    celltemp4 = list(results['subarray1_celltemp'])
    rear4 = list(results['subarray1_poa_rear'])
    front4 = list(results['subarray1_poa_front'])
    custom_angles = list(results["subarray1_axisrot"])

    dni = list(results['dn'])
    dhi = list(results['df'])
    alb = list(results['alb'])
    
    simtyp = [ii] * len(datelist)

    res = pd.DataFrame(list(zip(simtyp, power4, celltemp4, rear4, front4,
                              dni, dhi, alb)),
           columns = ['Sim', 'Power4' , 'CellTemp4', 'Rear4', 'Front4',
                     'DNI', 'DHI', 'Alb'])

    res = res[0:len(datelist)]
    res['index'] = res.index
    res['Power4']= res['Power4']/system_capacity4 # normalizing by the system_capacity
    res['datetimes'] = datelist
    res['Year'] = years
    res['Month'] = months
    res['Hour'] = hours
    res['Minutes'] = minutes
    #    res.index = timestamps
    res.to_pickle('Sim_'+str(ii)+'.pkl')
    res.to_csv(savefilevar, float_format='%g')
    dfAll = pd.concat([dfAll, res], ignore_index=True, axis=0)


# In[ ]:


dfAll.to_pickle('Results_pysam.pkl')

