#!/usr/bin/env python
# coding: utf-8

# In[1]:


# Written for nrel-pysam 3.0.2
import PySAM
import PySAM.Pvsamv1 as PV
import PySAM.Grid as Grid
import PySAM.Utilityrate5 as UtilityRate
import PySAM.Cashloan as Cashloan
import pathlib
import json
import os
import pandas as pd

sam_input_folder = 'JSONS2'


# In[2]:


print(PySAM.__version__)


# In[3]:


file_names = ["pvsamv1", "grid", "utilityrate5", "cashloan"]

pv = PV.new()  # also tried PVWattsSingleOwner
grid = Grid.from_existing(pv)
so = Cashloan.from_existing(grid, 'FlatPlatePVCommercial')
ur = UtilityRate.from_existing(pv)


# In[4]:


for count, module in enumerate([pv, grid, ur, so]):
    filetitle= 'AgriPV_SAM_' + file_names[count] + ".json"
    with open(os.path.join(sam_input_folder,filetitle), 'r') as file:
        data = json.load(file)
        for k, v in data.items():
            if k == 'number_inputs':
                continue
            try:
                module.value(k, v)
            except :
                # there is an error is setting the value for ppa_escalation
                print(module, k, v)


# ##### Sanity checks

# In[5]:


pv.SolarResource.solar_resource_file


# In[6]:


weatherfile = str(pathlib.Path().resolve().parent / 'SolarResourceFiles' / 'WF_SAM_00.csv')


# In[7]:


weatherfile = r'C:/Users/sayala/Documents/GitHub/Studies/pySAMtutorial/SolarResourceFiles/WF_SAM_00.csv'
weatherfile


# In[8]:


pv.SolarResource.solar_resource_file = weatherfile


# In[9]:


pv.SolarResource.use_wf_albedo


# In[10]:


pv.SolarResource.irrad_mode


# In[11]:


pv.SolarResource.albedo


# In[12]:


grid.SystemOutput.gen = [0] * 8760  # p_out   # let's set all the values to 0
pv.execute()
grid.execute()
ur.execute()
so.execute()


# In[ ]:


#system_capacity = #Normalization


# In[18]:


results = pv.Outputs.export()

#Sanity checks
dni = list(results['dn'])
dhi = list(results['df'])
alb = list(results['alb'])

#
power = list(results['subarray1_dc_gross'])
celltemp = list(results['subarray1_celltemp'])
poa= list(results['subarray1_poa_eff'])
rear = list(results['subarray1_poa_rear'])


# ## Explore output variables:

# In[22]:


import pprint


# In[23]:


results.keys()


# # Variables to explore SAM models
# 
# * sky_model = 0 for Isotropic, 1 for HDKR, 2 for Perez
# * irrad_mod = 0 DNI + GHI, 1 DNI + GHI, 2 GHI + DHI, 3 POA Ref cell, 4 POA pyr
# 
# use_wf_albedo
# use_spatial_albedos
