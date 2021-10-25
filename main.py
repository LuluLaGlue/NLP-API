from flask import Flask, jsonify, request
import geonamescache
from geotext import GeoText
import spacy
import pandas as pd
import os


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
    nlp = spacy.load('fr_core_news_md')
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


@app.route('/', methods=['GET', 'POST'])
def welcome():
    return (jsonify(values="Welcome"))


@app.route('/stations', methods=['GET', 'POST'])
def stations():
    search = None
    if request.method == 'POST':
        search = request.json['query']
    stations = get_stations(search)

    return jsonify(stations=stations)


@app.route('/get_cities', methods=['POST'])
def get_cities():
    string = request.json['text']
    cities = search_cities(string)

    return jsonify(cities=cities)


if __name__ == '__main__':
    app.run()