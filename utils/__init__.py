import xml.etree.ElementTree as ET
import requests
import folium
import osm2geojson
from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd


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


def wikidata_query(q, endpoint='https://query.wikidata.org/sparql'):
    agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'
    sparql = SPARQLWrapper(endpoint, agent=agent)
    sparql.setQuery(q)
    sparql.setReturnFormat(JSON)
    results = sparql.queryAndConvert()
    return results['results']['bindings']


def wikidata_item(item, endpoint='https://www.wikidata.org/w/api.php'):
    res = requests.get(endpoint, params={
        'action': 'wbgetentities',
        'ids': item,
        'format': 'json',
    })
    return res.json()['entities'][item]

def images_from_commons_category(category, image_size=1000):
    res = requests.get('https://commons.wikimedia.org/w/api.php', params={
        'action': 'query',
        'list': 'categorymembers',
        'cmtype': 'file',
        'cmtitle': category,
        'format': 'json',
    })
    image_titles = [t['title'] for t in res.json()['query']['categorymembers']]
    urls = []
    for title in image_titles:
        urls.append(commons_image(title, image_size))
    return urls

def commons_image(title, image_size=1000):
    res = requests.get('https://commons.wikimedia.org/w/api.php', params={
        'action': 'query',
        'prop': 'pageimages',
        'pithumbsize': image_size,
        'titles': title,
        'format': 'json',
    })
    image_url = next(iter(res.json()['query']['pages'].values()))['thumbnail']['source']
    return image_url

def img_html(url):
     return '<img src="{}" style="display:inline;margin:1px;width:200px"/>'.format(url)

def flatten_dict(d, sep='.'):
    return pd.json_normalize(d, sep=sep).to_dict(orient='records')