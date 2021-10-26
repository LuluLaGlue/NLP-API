from queue import PriorityQueue
from Classes.Queue import Queue
from typing import List
import pandas as pd
import json
import os


class SimpleGraph:
    def __init__(self):
        self.edges: Dict[Location, Dict[string, float]] = {}
        timetables = pd.read_csv('data{}timetables.csv'.format(os.sep),
                                 sep='\t',
                                 encoding='UTF-8')
        timetables["trajet"] = timetables["trajet"].str.lower()

        for index, row in timetables.iterrows():
            stopName = row['trajet'].split(' - ')
            time = row['duree']

            if stopName[0] in self.edges:
                self.edges[stopName[0]].update({stopName[1]: time})
            else:
                self.edges[stopName[0]] = {stopName[1]: time}

            if not stopName[1] in self.edges:
                self.edges[stopName[1]] = {}

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

            for n in self.neighbors(current):
                actualCost = self.vertex[n]['min']
                newCost = self.vertex[current]['min'] + self.edges[current][n]

                if newCost < actualCost:
                    self.vertex[n]['min'] = min(actualCost, newCost)
                    self.vertex[n]['from'] = current

                unvisited.put((self.vertex[n]['min'], n))

            visited.append(current)

    def getPath(self, start, end):
        start = start.lower()
        end = end.lower()

        try:
            self.initVertex(start)
            self.updateVertex(start)
        except KeyError:

            return 1

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

            return result
        except KeyError:

            return 2