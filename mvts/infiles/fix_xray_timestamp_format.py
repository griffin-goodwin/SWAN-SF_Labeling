#!/usr/bin/env python
# coding: utf-8

# In[24]:


import pandas as pd
xray_series = pd.read_csv('integrated_data.txt', skiprows=1, header=None)
xray_series.columns = ['Timestamp', 'B_AVG']
xray_series.set_index('Timestamp', inplace=True)
xray_series.index = pd.to_datetime(xray_series.index, infer_datetime_format=True)
xray_series.to_csv('fixed_all_xrs_Jun19.csv')

