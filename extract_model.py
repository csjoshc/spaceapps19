import datetime as dt 
import numpy as np

import matplotlib.pyplot as plt
import os
import pandas as pd
import xarray as xr
from sklearn import linear_model

# This file extracts data from .nc files in the data subdirectory (when this file was run, only .nc files were present)
# It can process a batch of files and concatenate them in a n dimensional array by coordinates using xarray package
# The array is flattened to pandas, and filtered into datasets for each latitude/longitude point for modeling 
# output csv contains modeling info for all lat-long coordinate pairs based on data from 1992 - 2010

os.chdir('/home/csjc/Documents/test/data')
# ds = xr.open_mfdataset(['oosu_cioss_weekly_msla_geovel_1992_v1.nc'])
# print(ds['sea_surface_height_above_sea_level'])

# print(ds['sea_surface_height_above_sea_level'].sel(longitude=slice(228, 250)))
for root, dirs, files in os.walk(".", topdown=False):
    ds = xr.open_mfdataset(files, combine='by_coords')
    #print(ds)
    df = ds['zos'].to_dataframe().sort_values('time').dropna().reset_index()
    print(df.info())

    # Convert longitude in 0-359 degrees to -180 to 180 degrees (as used in google)
    to_convert = df['lon'] > 180
    df.loc[to_convert, 'lon'] = df['lon'][to_convert] - 360

    # Filter for California coast
    # lat_filter = (df['lat'] > 30) & (df['lat'] < 40)
    # lon_filter = (df['lon'] > - 130) & (df['lon'] < -110)

    # # print(lat_filter.mean())
    # # print(lon_filter.mean())

    # df = df[lat_filter & lon_filter]
    # print(df)
    # print(df.columns.get_values().tolist())

    # concatenate the coordinates as a tuple, for easier filtering later
    # then, create a list of distinct points to generate models for each
    df['coords'] = list(zip(df.lat, df.lon))
    positionlist = df.coords.unique()

    # create output dataframe for storing results
    yearlist = [2025, 2030, 2035, 2040, 2050, 2075, 2100]
    yearnames = [str(x) for x in yearlist]
    output = pd.DataFrame({'Point' : positionlist})
    output = output.reindex(columns = ['Point', 'Coeff', 'Intercept', 'R2'] + yearnames)
    output = output.set_index('Point')
    mydata = {}
    #pointlens = []

    #test = df.loc[:,['time', 'zos']][df.coords == (37.5, -124.5)]
    
    # prepare yearlist92 - an array of days since 1992 start for the future projection targets in yearlist
    yearlist92 = (pd.to_datetime(yearlist, format = '%Y') - 
        df['time'].values[0]).days.values.reshape(-1, 1)
    print(yearlist92)
    
    ## This iterates through each point and runs linear regression on the time series data specifc for that point
    ## Then, the results of modeling, and the predictions, are stored in the output dataframe

    for point in positionlist:
        tempdf = df.loc[:,['time', 'zos']][df.coords == point]
        X = (tempdf['time'] -  tempdf['time'].values[0]).dt.days.values.reshape(-1, 1)
        y = tempdf['zos'].values
        lin_model = linear_model.LinearRegression().fit(X, y)
        output.loc[point, 'Coeff'] = lin_model.coef_
        output.loc[point, 'Intercept'] = lin_model.intercept_
        output.loc[point, 'R2'] = lin_model.score(X, y)


        results = lin_model.predict(yearlist92)
        output.loc[point, '2025':'2100'] = results.T
        #mydata[point] = tempdf
        #pointlens.append(len(tempdf))
        print("Finished processing " , point)
        print(output.loc[[point]])
        
    #print(mydata)
    #print(pointlens)
    
    print(output)
    output.to_csv(r'output.csv')