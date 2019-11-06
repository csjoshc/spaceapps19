import matplotlib.pyplot as plt
import os
import pandas as pd
import numpy as np



output = pd.read_csv("data/output.csv")

# If output discarded the standalone lat, long columns, get them back from the tuple
output['yearcoeff_mm'] = output.Coeff * 1000 * 365 
print(output.Point.dtype)
output[['Lat', 'Long']] = output.Point.str.strip('()').str.split(',', expand= True).astype('float')
#output.to_csv(r'data/output.csv')

# Create subset of data for california coast
lat_filter = (output['Lat'] > 30) & (output['Lat'] < 40)
lon_filter = (output['Long'] > - 130) & (output['Long'] < -110)
california = output[lat_filter & lon_filter]
california.to_csv(r'data/california.csv')

# boxplot excluding areas outside 3 standard deviations
bot, top = output.yearcoeff_mm.quantile(.005), output.yearcoeff_mm.quantile(.995)
print(top, bot)
fig, axes = plt.subplots()
plt.ylim((bot, top))
output.boxplot('yearcoeff_mm')
plt.show()

# describe output (basic stats)
print(output.describe())

# Split data into rising vs falling water datasets for plotting black-red plot
decreaselevel = output[output.yearcoeff_mm <= 0]
increaselevel = output[output.yearcoeff_mm > 0]
decreaselevel.to_csv(r'data/decreaselevel.csv')

# basemap code based on https://jakevdp.github.io/PythonDataScienceHandbook/04.13-geographic-data-with-basemap.html
from mpl_toolkits.basemap import Basemap
from itertools import chain
def draw_map(m, scale=0.2):

    # draw a shaded-relief image
    m.shadedrelief(scale=scale)
    
    # lats and longs are returned as a dictionary
    lats = m.drawparallels(np.linspace(-90, 90, 13))
    lons = m.drawmeridians(np.linspace(-180, 180, 13))

    # keys contain the plt.Line2D instances
    lat_lines = chain(*(tup[1][0] for tup in lats.items()))
    lon_lines = chain(*(tup[1][0] for tup in lons.items()))
    all_lines = chain(lat_lines, lon_lines)
    
    # cycle through these lines and set the desired style
    for line in all_lines:
        line.set(linestyle='-', alpha=0.3, color='w')

# Plot black-red binary image
m = Basemap(projection='cyl', resolution=None,
            llcrnrlat=-90, urcrnrlat=90,
            llcrnrlon=-180, urcrnrlon=180, )

x_low, y_low = m(decreaselevel.Long, decreaselevel.Lat)
x_high, y_high = m(increaselevel.Long, increaselevel.Lat)

fig = plt.figure(figsize=(12, 9), edgecolor='w')
draw_map(m)

plt.plot(x_low, y_low, 'ok', markersize = 1)
plt.plot(x_high, y_high, 'or', markersize = 1)

plt.show()

# Plot gradient with no outliers (no data beyond +- 3 standard deviations)
no_out = (output['yearcoeff_mm'] > bot) & (output['yearcoeff_mm'] < top)
no_out = output[no_out]

fig = plt.figure(figsize=(12, 9), edgecolor='w')
m = Basemap(projection='cyl', resolution=None,
            llcrnrlat=-90, urcrnrlat=90,
            llcrnrlon=-180, urcrnrlon=180, )
draw_map(m)
x, y = m(no_out.Long, no_out.Lat)
m.scatter(x, y, s = 1, c = no_out.yearcoeff_mm, cmap = 'coolwarm', alpha = 0.5)
plt.colorbar(label=r'Yearly change (mm)')
plt.clim(-10, 10)
plt.show()

