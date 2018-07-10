

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

#Creating a TOOLs vector to dinamically control the included tooltips
TOOLS='pan,wheel_zoom,box_select,lasso_select,reset'


base_map = plt.figure(tools=TOOLS, x_range=x_range, y_range=y_range)
base_map.axis.visible = False
base_map.select(bk.models.BoxSelectTool).select_every_mousemove = False
base_map.select(bk.models.LassoSelectTool).select_every_mousemove = False

url = 'http://a.basemaps.cartocdn.com/light_all/{Z}/{X}/{Y}.png'
attribution = "Tiles by Carto, under CC BY 3.0. Data by OSM, under ODbL"

base_map.add_tile(bk.models.WMTSTileSource(url=url, attribution=attribution))
#base_map.sizing_mode = 'scale_both'

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
filename = 'KL_Tageswerte_Beschreibung_Stationen.txt'
fileorigin = open(filename, 'r', encoding = 'cp1250')
num_of_stations = 100
partial_read_in = False
Stations = {}

for lineid, line in enumerate(fileorigin):
    if lineid>2:
        line_vec = list(filter(None,line.split(' ')))
        Stations[line_vec[0]] = Station(line_vec[0],line_vec[1], line_vec[2], line_vec[3],
                                line_vec[4], line_vec[5], line_vec[6:-2], ''.join(line_vec[-2:-1]))
fileorigin.close()

stationnames = []
stat_lats = []
stat_lons = []
stationregions =[]
for k, v in Stations.items():
    stationnames.append(' '.join(v.name))
    stat_lats.append(float(v.geobr))
    stat_lons.append(float(v.geola))
    stationregions.append(v.land)

# Create pandas dataframe with related information and get region names
df_stations= coor_to_web_mercator(stationnames,np.array(stat_lons),np.array(stat_lats))
df_stations["region"] = stationregions
df_stations['region'] = [r.replace('\n', '') for r in df_stations['region']]

# Add dot plot on top of the base map to represent stations (initially empty)
psource = bk.models.ColumnDataSource(data=dict(name=[], x=[], y=[]))
#full_tabsource = bk.models.ColumnDataSource(data=dict(name=stationnames, x=stat_lats, y=stat_lons))
tabsource = bk.models.ColumnDataSource(data=dict(name=[], x=[], y=[]))
statcircles = base_map.circle('x', 'y', source=psource, color='red', size=6)
stat_hover = bk.models.HoverTool()
stat_hover.tooltips = [('Station name', '@name')]
base_map.add_tools(stat_hover)

taptool = bk.models.TapTool()
base_map.add_tools(taptool)

#Creating a button for info vis in new table


button_labels = ["Temperature", "Humidity", "Rain", "Unicorns"]
button_group = bk.models.widgets.RadioButtonGroup(labels=button_labels, active=0)
#Creating the main plot for visualization
mainplot = plt.figure(title="main plot",#plot_height=400, plot_width=400, title="main plot",
                tools="crosshair,pan,reset,save,wheel_zoom")
mainplot_2 = plt.figure(title="main plot 2",
                tools="crosshair,pan,reset,save,wheel_zoom")
mainplot.scatter('x', 'y', source=tabsource, name = 'line1')

# Create the dropdown menu for different regions

region_names = df_stations["region"][1:].value_counts().index.tolist()


stat_menu = bk.models.widgets.Select(title="Stations -- Select a region", value="None",options=['All']+region_names+['None'], width = 200)
stat_menu_2 = bk.models.widgets.Select(title="Something else -- Select ...", value="None",options=['All']+region_names+['None'], width = 200)
# Create sliders
slider_start = bk.models.widgets.Slider(start=1900, end=2018, value=1, step=1, title="Start year of historical data:", width = 200)
slider_end = bk.models.widgets.Slider(start=1900, end=2018, value=1, step=1, title="End year of historical data:", width=200)


city_names = ['Berlin','Hamburg','Munich','Cologne','Frankfurt am Main']

stat_menu= bk.models.widgets.Select(title="Stations -- Select a city", value="None",options=city_names+['None'])
columns = [
        bk.models.widgets.TableColumn(field="name", title="Station name"),
        bk.models.widgets.TableColumn(field="x", title="x"),
        bk.models.widgets.TableColumn(field="y", title="y")
    ]
stat_table = bk.models.widgets.DataTable(source=tabsource, columns=columns, width=400, height=280)

def show_info(attr,old,new):
    #x = statcircles.data_source['x']
    #y = statcircles.data_source['y']
    source = bk.models.ColumnDataSource(data=dict(x = tabsource.data['x'], y = tabsource.data['y']))
    #source)

# Define functions for selecting the region from menu and updating the dot plot
def select_stations():
    name = stat_menu.value

    if name == 'Frankfurt am Main':
        name = "Frankfurt/Main"
    elif name == 'Munich':
        name = 'M' + chr(252) + 'nchen'
    elif name == 'Cologne':
        name = 'K'+ chr(246) + 'ln'

    if name == 'All':
        df = df_stations
    elif name == 'None':
        df = pd.DataFrame(columns=['name','x','y'])
    else:
        df = df_stations.loc[df_stations['name'].str.contains(name,regex=False)]
    return df

def update_stations(attr,old,new):
    df = select_stations()
    psource.data = dict(
        x=df['x'].tolist(),
        y=df['y'].tolist(),
        name = df['name'].tolist()
)
    tabsource.data.update(psource.data)

def update_when_selected(attr, old, new):
    inds = np.array(new['1d']['indices'])
    #For now I just print the coordinates of selected stations
    #in prompt, later in a table widget
    #Something is not good with this, I don't know hot to get the proper data


    if type(psource.data['x'])==list:
        ref_stlns = psource.data['x']
        ref_stlts = psource.data['y']
        refnames = psource.data['name']
    else:
        ref_stlns = psource.data['x'].tolist()
        ref_stlts = psource.data['y'].tolist()
        refnames = psource.data['name'].tolist()
    stnames = []
    stlns = []
    stlts = []
    for i in inds:
        #print(refnames[i])
        stlns.append(ref_stlns[i])
        stlts.append(ref_stlts[i])
        stnames.append(refnames[i])
        #print(stlns[i],' ',stlts[i])
    tabsource.data.update(dict(name=stnames,x=stlns,y=stlts))


# Update dot plots on map
#show_button.on_click(show_info)
stat_menu.on_change('value',update_stations)
statcircles.data_source.on_change('selected', update_when_selected)
#statcircles.data_source.on_change('selected', show_info)
# -----------------------------------------------------------------------------------------------------
# END OF STATIONS PART
# -----------------------------------------------------------------------------------------------------

# Save layout (map, widgets, description text etc.) and add to current document for successful update of page


#layout = bk.layouts.layout(desc, [stat_menu, stat_table, base_map])
#child_1 = [bk.layouts.widgetbox([desc,stat_menu,stat_table], sizing_mode='stretch_both'),bk.layouts.Spacer(height = 10),button_group,mainplot]

#layout = bk.layouts.layout([[child_1,bk.layouts.Spacer(width = 10),base_map]],sizing_mode='stretch_both')
spacer_1 = bk.layouts.Spacer(width=10, height=100)
spacer_2 = bk.layouts.Spacer(width=10, height=100)
spacer_3 = bk.layouts.Spacer(width=10, height=100)

MODE = 'scale_width' #"scale_width", "scale_height", "scale_both"
row_desc = bk.layouts.row([desc], sizing_mode=MODE)
widgets = bk.layouts.column([stat_menu,stat_menu_2,slider_start, slider_end, button_group], sizing_mode=MODE)
row_show = bk.layouts.row([widgets, base_map, mainplot, mainplot_2],sizing_mode=MODE)
layout = bk.layouts.column([row_desc, row_show], sizing_mode = MODE)

bk.io.curdoc().add_root(layout)
