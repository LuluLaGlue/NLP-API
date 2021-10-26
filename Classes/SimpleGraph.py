from queue import PriorityQueue
from Classes.Queue import Queue
from typing import List
import pandas as pd
import json
import os


class SimpleGraph:
    def __init__(self):
        self.edges: Dict[Location, Dict[string, float]] = {}
        df = pd.read_csv('data{}timetables.csv'.format(os.sep),
                         sep='\t',
                         encoding='UTF-8')

        df["trajet"] = df["trajet"].str.lower()
        # Remove accents
        df["trajet"] = df["trajet"].str.normalize('NFKD').str.encode(
            'ascii', errors='ignore').str.decode('utf-8')

        for i, row in df.iterrows():
            train_start = row['trajet'].split(' - ')[0]
            train_end = row['trajet'].split(' - ')[1]
            time = row['duree']

            if train_start in self.edges:
                self.edges[train_start].update({train_end: time})
            else:
                self.edges[train_start] = {train_end: time}

            if not train_end in self.edges:
                self.edges[train_end] = {}

    def print(self):
        print(
            json.dumps(self.vertex,
                       sort_keys=True,
                       indent=4,
                       ensure_ascii=True))

    def neighbors(self, id) -> List:

        return self.edges[id]

    def initVertex(self, start):
        inf = float('inf')
        self.vertex: Dict[string, Dict[float, string]] = {}

        for row in self.edges:
            self.vertex[row] = {'min': inf, 'from': ''}

        self.vertex[start]['min'] = 0

    def updateVertex(self, start):
        visited = []
        unvisited = PriorityQueue()
        unvisited.put((0, start))

        while not unvisited.empty():
            current = unvisited.get()[1]

            for neighbor in self.neighbors(current):
                current_cost = self.vertex[neighbor]['min']
                new_cost = self.vertex[current]['min'] + self.edges[current][
                    neighbor]

                if new_cost < current_cost:
                    self.vertex[neighbor]['min'] = min(current_cost, new_cost)
                    self.vertex[neighbor]['from'] = current

                unvisited.put((self.vertex[neighbor]['min'], neighbor))

            visited.append(current)

    def getPath(self, start, end):
        start = start.lower()
        end = end.lower()

        try:
            self.initVertex(start)
            self.updateVertex(start)
        except KeyError:

            return "Invalid Start Station"

        try:
            q = Queue()
            q.put(end)

            current = end
            result = []

            while current != start:
                current = self.vertex[current]['from']
                q.put(current)

            while not q.empty():
                t = q.get()
                result.append(t)

            result.reverse()
            return result

        except KeyError:

            return "No path found"