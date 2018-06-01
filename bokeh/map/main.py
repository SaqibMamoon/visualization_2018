import geopandas as gpd
import os
import pandas as pd
import numpy as np
import bokeh as bk
import bokeh.plotting as plt
from os.path import dirname, join


# Read the html file for the description 
desc = bk.models.Div(text=open(join(dirname(__file__), "title.html")).read(), width=800)


# Define the function to convert coordinates into appropriate format for bokeh
def coor_to_web_mercator(name, lon,lat):
    """Converts decimal longitude/latitude to Web Mercator format"""
    df = pd.DataFrame(columns = ['name','x','y'])
    k = 6378137
    df['name'] = name
    df["x"] = lon * (k * np.pi/180.0)
    df["y"] = np.log(np.tan((90 + lat) * np.pi/360.0)) * k
    return df


# Create the base map with Germany in focus
germany_lon = np.array([6.98815, 13.98853])
germany_lat = np.array([48.40724,53.9079])

df_ger = coor_to_web_mercator(['ger_border','ger_border'],germany_lon, germany_lat)

x_range,y_range = ((df_ger['x'][0],df_ger['x'][1]), (df_ger['y'][0],df_ger['y'][1]))

base_map = plt.figure(tools='pan, wheel_zoom', x_range=x_range, y_range=y_range)
base_map.axis.visible = False

url = 'http://a.basemaps.cartocdn.com/light_all/{Z}/{X}/{Y}.png'
attribution = "Tiles by Carto, under CC BY 3.0. Data by OSM, under ODbL"

base_map.add_tile(bk.models.WMTSTileSource(url=url, attribution=attribution))
base_map.sizing_mode = 'scale_both'

# ----------------------------------------------------------------------------------------------------
#  STATIONS PART
# ----------------------------------------------------------------------------------------------------

# Collect station coordinates from file
class Station:
    def __init__(self, id, von, bis, height, geobr, geola, name, land):
        self.id = id
        self.von = von
        self.bis = bis
        self.height = height
        self.geobr = geobr
        self.geola = geola
        self.name = name
        self.land = land
    def get_GPS(self):
        return np.array([self.geobr, self.geola]).astype('float')

#read in toy data (all stations in germany)
filename = 'KL_Tageswerte_Beschreibung_Stationen0.txt'
fileorigin = open(filename, 'r')
num_of_stations = 100
partial_read_in = False
Stations = {}

for lineid, line in enumerate(fileorigin):
    line_vec = list(filter(None,line.split(' ')))
    Stations[line_vec[0]] = Station(line_vec[0],line_vec[1], line_vec[2], line_vec[3],
                            line_vec[4], line_vec[5], line_vec[6:-1], line_vec[-1])
fileorigin.close()

stationnames = []
stat_lats = []
stat_lons = []
stationregions =[]
for k, v in Stations.items():
    stationnames.append(v.name)
    stat_lats.append(float(v.geobr))
    stat_lons.append(float(v.geola))
    stationregions.append(v.land)

# Create pandas dataframe with related information and get region names
df_stations= coor_to_web_mercator(stationnames,np.array(stat_lons),np.array(stat_lats))
df_stations["region"] = stationregions
df_stations['region'] = [r.replace('\n', '') for r in df_stations['region']]
region_names = df_stations["region"][1:].value_counts().index.tolist()


# Add dot plot on top of the base map to represent stations (initially empty)
psource = bk.models.ColumnDataSource(data=dict(name=[], x=[], y=[]))
base_map.circle('x', 'y', source=psource, color='red', size=6)
stat_hover = bk.models.HoverTool()
stat_hover.tooltips = [('Name of station:', '@name')]
base_map.add_tools(stat_hover)

# Create the dropdown menu for different regions
stat_menu= bk.models.widgets.Select(title="Stations -- Select a region", value="None",options=['All']+region_names+['None'])

# Define functions for selecting the region from menu and updating the dot plot
def select_stations():
    name= stat_menu.value
    if name == 'All':
        df =df_stations
    elif name == 'None':
        df = pd.DataFrame(columns=['name','x','y'])
    else:
        df = df_stations.loc[df_stations['region'] == name]
    return df

def update_stations(attr,old,new): 
    df = select_stations()
    psource.data = dict(
        x=df['x'],
        y=df['y'],
        name = df['name']
)
# Update dot plots on map  
stat_menu.on_change('value',update_stations) 

# -----------------------------------------------------------------------------------------------------
# END OF STATIONS PART
# -----------------------------------------------------------------------------------------------------

# Save layout (map, widgets, description text etc.) and add to current document for successful update of page
layout = bk.layouts.layout(desc, [stat_menu, base_map])
bk.io.curdoc().add_root(layout)