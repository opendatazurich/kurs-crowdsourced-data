import xml.etree.ElementTree as ET
import requests
import folium


def get_layers_from_wfs(wfs_base_url):
    r = requests.get(wfs_base_url, params={
        'service': 'WFS',
        'version': '1.0.0',
        'request': 'GetCapabilities'
    })
    # XML parsen und die Layer-Informationen extrahieren
    root = ET.fromstring(r.content)
    namespaces = {
        'wfs': 'http://www.opengis.net/wfs'
    }
    layers = {}
    for feature_type in root.findall('wfs:FeatureTypeList/wfs:FeatureType', namespaces):
        layers[feature_type.find('wfs:Name', namespaces).text] = {
            'srs': feature_type.find('wfs:SRS', namespaces).text,
        }
    return layers

def overpass_query(q, endpoint='http://overpass.osm.ch/api/interpreter'):
    r = requests.get(endpoint, params={'data': q})
    r.raise_for_status()
    return osm2geojson.json2geojson(r.json())

def style_layer(geojson, layer, **kwargs):
    # load GEOJSON, but don't add it to anything
    gj = folium.features.GeoJson(geojson)

    # iterate over GEOJSON features, pull out point coordinates, make Markers and add to layer
    for feature in gj.data['features']:
        if not feature or not feature['geometry']:
            continue
        if feature['geometry']['type'] == 'Point':
            tool_tip_text = '<pre>\n'
            properties = feature['properties']
            if properties.get('tags'):
                properties.update(properties['tags'])
                del properties['tags']
            for p in properties:
                tool_tip_text = tool_tip_text + str(p) + ': ' + str(feature['properties'][p]) + '\n'
            tool_tip_text = tool_tip_text + '\n</pre>'
            tool_tip = folium.Tooltip(tool_tip_text)
            folium.Marker(location=list(reversed(feature['geometry']['coordinates'])),
                          icon=folium.Icon(**kwargs),
                          tooltip=tool_tip
                          ).add_to(layer)