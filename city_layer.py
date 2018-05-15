import numpy as np
import folium
import webbrowser
import os
import geopandas as gpd


germany_middle = [51, 10.5]
map1 = folium.Map(location=germany_middle,
    zoom_start=6.4)

df1 = gpd.read_file('cities.geojson')

map1.choropleth(geo_data=df1)

map1.save('./map_cities_layer.html')
webbrowser.open('./map_cities_layer.html')

map2 = folium.Map(location=germany_middle,
    zoom_start=6.4)

df2 = gpd.read_file('regions.geojson')

map2.choropleth(geo_data=df2)

map2.save('./map_regions_layer.html')
webbrowser.open('./map_regions_layer.html')


