from Classes.SimpleGraph import SimpleGraph
from flask import Flask, jsonify, request
from geotext import GeoText
import geonamescache
import pandas as pd
import unidecode
import requests
import spacy
import os


def get_stations(search=None):
    df = pd.read_csv(".{}data{}list_train_stations_brut.csv".format(
        os.sep, os.sep),
                     sep=";",
                     encoding='UTF-8')
    df.pop("id")
    df = df.apply(lambda x: pd.Series(x.dropna().values))
    df["station"] = df["station"].str.lower()
    df["station"] = df["station"].str.normalize('NFKD').str.encode(
        'ascii', errors='ignore').str.decode('utf-8')

    if search != None:
        df = df[df["station"].str.contains(unidecode.unidecode(
            search.lower()))]

    return df["station"].tolist()


def get_all_cities():
    gc = geonamescache.GeonamesCache()
    list_cities = gc.get_cities()
    all_cities = []

    for city in list_cities:
        all_cities.append(list_cities[city]['name'].lower())

        for alternate in list_cities[city]['alternatenames']:
            dash = alternate.split('-')
            dash = ' '.join(dash).lower()
            all_cities.append(dash)

    return all_cities


def search_cities(quote):
    all_cities = get_all_cities()
    s = ' '.join(quote.split('-'))
    doc = nlp(s)

    cities = []

    for ent in doc.ents:
        location = ent.text.split('-')
        location = "-".join(location).lower()

        if location in all_cities:
            cities.append(location)
        else:
            gt = GeoText(location)

            if len(gt.cities) > 0:
                cities.append(location)
            elif len(cities) < 2:
                r = requests.get(
                    "https://geocoding-api.open-meteo.com/v1/search?name={}&language=fr"
                    .format(location)).json()
                df = pd.DataFrame(r['results'])
                df["name"] = df["name"].str.lower()
                df = df[df["name"].str.contains(location)]

                if len(df['name']) > 0:
                    cities.append(location)

    return cities


def shortest_path(start, end):
    graph = SimpleGraph()
    start = unidecode.unidecode(start)
    end = unidecode.unidecode(end)
    path, error, info = graph.getPath(start, end)

    return path, error, info


def multi_shortest_path(start, end):
    start = unidecode.unidecode(start).lower()
    end = unidecode.unidecode(end).lower()
    all_start = get_stations(start)
    all_end = get_stations(end)

    paths = []
    errs = []
    infos = []

    for s in all_start:
        for e in all_end:
            graph = SimpleGraph()
            path, err, info = graph.getPath(s, e)
            if not err and not info:
                paths.append({'path': path, 'start': s, 'end': e})
            else:
                errs.append({'error': err, 'start': s, 'end': e})
                infos.append({'info': info, 'start': s, 'end': e})

    return paths, errs, infos


app = Flask(__name__)
nlp = spacy.load('fr_core_news_md')


@app.route('/', methods=['GET', 'POST'])
def welcome():

    return jsonify(routes=[{
        "/get_cities": {
            "POST": {
                "description": "Extract cities from a text query",
                "body": {
                    "text": "Je veux aller de station1 à station2."
                },
                "return": {
                    "cities": ["station1", "station2"]
                }
            }
        }
    }, {
        "/path": {
            "POST": {
                "description": "Get the shortest path between two stations",
                "body": {
                    "start": "Starting Station",
                    "end": "Arriving Station"
                },
                "return": {
                    "path": [
                        "Starting Station", "Connecting Station",
                        "Arriving Station"
                    ]
                }
            }
        }
    }, {
        "/stations": {
            "GET": {
                "description": "Get All Train Stations",
                "return": {
                    "stations": ["station1", "station2", "station3", "..."]
                }
            },
            "POST": {
                "description": "Search Stations",
                "body": {
                    "query": "Station"
                },
                "return": {
                    "stations": ["station1", "station2"]
                }
            }
        }
    }])


@app.route('/stations', methods=['GET', 'POST'])
def stations():
    query = None

    if request.method == 'POST':
        query = request.json['query']

    stations = get_stations(query)

    if len(stations) == 0:

        return jsonify(stations=stations,
                       error="Invalid query",
                       info="No stations found")

    return jsonify(stations=stations)


@app.route('/path', methods=['POST'])
def path():
    start = request.json['start']
    end = request.json['end']
    p, e, i = shortest_path(start, end)

    if len(e) > 0 or len(i) > 0:

        return jsonify(path=p, error=e, info=i)

    return jsonify(path=p)


@app.route('/multi_path', methods=['POST'])
def multi_path():
    start = request.json['start']
    end = request.json['end']

    p, e, i = multi_shortest_path(start, end)

    if len(p) == 0:

        return jsonify(path=p, error=e, info=i)

    return jsonify(path=p)


@app.route('/get_cities', methods=['POST'])
def get_cities():
    text = request.json['text']
    cities = search_cities(text)

    if len(cities) < 2:

        return jsonify(cities=cities,
                       error="Invalid query",
                       info="Less than 2 cities found")

    return jsonify(cities=cities)


@app.route('/query_to_path', methods=['POST'])
def query_to_path():
    query = request.json['query']
    cities = search_cities(query)

    if len(cities) < 2:

        return jsonify(cities=cities,
                       error="Invalid query",
                       info="Less then 2 cities found")

    start = cities[0]
    end = cities[1]

    p, e, i = multi_shortest_path(start, end)

    if len(p) == 0:

        return jsonify(path=p, error=e, info=i)

    return jsonify(path=p)


if __name__ == '__main__':
    app.run()