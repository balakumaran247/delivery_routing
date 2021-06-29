import csv, json, os
import pandas as pd
import numpy as np
import osmnx as ox
import networkx as nx

class preparation:
    '''
    Converts the input csv files to json files
    origins.csv and destinations.csv from data directory
    '''

    def generate_json(self, csvFilePath, jsonFilePath):
        data = {}
        with open(csvFilePath, encoding='utf-8') as csvf:
            csvReader = csv.DictReader(csvf)
            for rows in csvReader:
                key = rows['\ufeffuno']
                data[key] = rows
        with open(jsonFilePath, 'w', encoding='utf-8') as jsonf:
            jsonf.write(json.dumps(data, indent=4))
    
    def create_graph(self, north, south, east, west, graph_path, extent_json):
        extent_dict = {
                'n': north,
                's': south,
                'e' : east,
                'w' : west,
            }
        with open(extent_json, "w") as outfile:
            json.dump(extent_dict, outfile, indent=4)
        print('\ngenerating the graph...\n')
        graph = ox.graph_from_bbox(north, south, east, west, network_type='drive', simplify=False)
        print('projecting the graph...\n')
        graph_proj = ox.project_graph(graph)
        print('generating the graphml file...\n')
        ox.io.save_graphml(graph_proj, filepath=graph_path, gephi=False, encoding='utf-8')
        del graph, graph_proj

    def generate_graph(self, combined_csv, extent_json, graph_path):
        south = combined_csv['lat'].min()-0.05
        west = combined_csv['lon'].min()-0.05
        north = combined_csv['lat'].max()+0.05
        east = combined_csv['lon'].max()+0.05
        if not os.path.isfile(extent_json) or not os.path.isfile(graph_path):
            self.create_graph(north, south, east, west, graph_path, extent_json)
        else:
            with open(extent_json) as f:
                e = json.load(f)
            if north!=e['n'] or south!=e['s'] or east!=e['e'] or west!=e['w']:
                self.create_graph(north, south, east, west, graph_path, extent_json)
        print('[checked] osm graph\n')


origins_csv = os.path.join('.', 'data', 'origins.csv')
destinations_csv = os.path.join('.', 'data', 'destinations.csv')
combined_csv = pd.concat([origins_csv,destinations_csv],ignore_index=True,copy=False)
origins_json = os.path.join('.', 'database', 'origins.json')
destinations_json = os.path.join('.', 'database', 'destinations.json')
extent_json = os.path.join('.', 'database', 'extent.json')
graph_path = os.path.join('.', 'database', 'graph.graphml')

def main():
    conv = preparation()
    conv.generate_json(origins_csv, origins_json)
    conv.generate_json(destinations_csv, destinations_json)
    print('\ncorresponding json files are generated.\n')
    conv.generate_graph(combined_csv, extent_json, graph_path)

if __name__ == '__main__':
    main()