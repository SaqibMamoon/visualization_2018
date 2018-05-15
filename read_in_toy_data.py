import numpy as np
import folium
import webbrowser
import os
from folium.plugins import MarkerCluster
from folium.plugins import FastMarkerCluster

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
    print(Stations[line_vec[0]].name)
print("number of stations loaded: ",len(Stations))
fileorigin.close()

#Create Map
germany_middle = [51, 10.5]
map_1 = folium.Map(location=germany_middle, 
    zoom_start=6.4)

#create callback string for leaflet - FastMarkerCluster
callback = """\
    function (row) {
        var icon, marker;
        icon = L.AwesomeMarkers.icon({
            icon: "map-marker", markerColor: "red"});
        marker = L.marker(new L.LatLng(row[0], row[1]));
        marker.setIcon(icon);
        marker.bindPopup('dwd weather station').openPopup
        marker.on('click', onClick);
        function onClick(e) {
            var popup = e.target.getPopup();
            popup.setContent("This is a weather station at " + e.latlng.toString())
        }
        return marker;
    };"""

#getting data from stations dictionary
stationnames = []
lats = []
lons = []
for k, v in Stations.items():
    stationnames.append(v.name)
    lats.append(float(v.geobr))
    lons.append(float(v.geola))

FastMarkerCluster(
    data=list(zip(lats, lons)),
    callback=callback#[personalized_callback(name) for name in stationnames]
).add_to(map_1)

#save map and open in browser
map_1.save('./map.html')
webbrowser.open('./map.html')
