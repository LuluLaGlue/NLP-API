from flask import Flask, jsonify, request
from geotext import GeoText
from Classes.SimpleGraph import SimpleGraph
import pandas as pd
import geonamescache
import spacy
import os


def shortest_path(start, end):
    graph = SimpleGraph()

    return graph.getPath(start, end)


def get_stations(search=None):
    df = pd.read_csv(".{}data{}list_train_stations_brut.csv".format(
        os.sep, os.sep),
                     sep=";")
    df.pop("id")
    df = df.apply(lambda x: pd.Series(x.dropna().values))

    if search == None:
        return df["station"].tolist()

    df["station"] = df["station"].str.lower()
    df = df[df["station"].str.contains(search.lower())]

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


def search_cities(string):
    all_cities = get_all_cities()
    doc = nlp(string)

    cities = []

    for ent in doc.ents:
        location = ent.text.split('-')
        location = " ".join(location).lower()
        if location in all_cities:
            cities.append(location)
        else:
            gt = GeoText(location)
            if len(gt.cities) > 0:
                cities.append(location)

    return cities


app = Flask(__name__)
nlp = spacy.load('fr_core_news_md')


@app.route('/', methods=['GET', 'POST'])
def welcome():

    return jsonify(values="Welcome")


@app.route('/stations', methods=['GET', 'POST'])
def stations():
    search = None
    if request.method == 'POST':
        search = request.json['query']
    try:
        stations = get_stations(search)
    except:

        return jsonify(error=True, stations=None)

    return jsonify(error=False, stations=stations)


@app.route('/path', methods=['POST'])
def path():
    start = request.json['start']
    end = request.json['end']
    try:
        path = shortest_path(start, end)
    except:

        return jsonify(error=True, path=None)

    return jsonify(error=False, path=path)


@app.route('/get_cities', methods=['POST'])
def get_cities():
    string = request.json['text']
    try:
        cities = search_cities(string)
    except:

        return jsonify(error=True, cities=None)

    return jsonify(error=False, cities=cities)


if __name__ == '__main__':
    app.run()