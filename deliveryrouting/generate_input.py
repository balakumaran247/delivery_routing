import csv, json, os, sys
import pandas as pd
import numpy as np
import osmnx as ox
import networkx as nx
import scipy

def progressbar(func):
    progress, text = func()
    block = int(round(10*progress))
    progress_text = "\r{0}: [{1}] {2:.2f}% {3}".format(text, "#"*block + "-"*(10-block), progress*100, 'completed')
    sys.stdout.write(progress_text)
    sys.stdout.flush()

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
        #print('projecting the graph...\n')
        #graph_proj = ox.project_graph(graph)
        print('generating the graphml file...\n')
        ox.io.save_graphml(graph, filepath=graph_path, gephi=False, encoding='utf-8')
        del graph#, graph_proj

    def generate_graph(self, combined_csv, extent_json, graph_path):
        print('\nCalculating extent\n')
        south = combined_csv['lat'].min()-0.5
        west = combined_csv['lon'].min()-0.5
        north = combined_csv['lat'].max()+0.5
        east = combined_csv['lon'].max()+0.5
        print('checking...\n')
        if not os.path.isfile(extent_json) or not os.path.isfile(graph_path):
            self.create_graph(north, south, east, west, graph_path, extent_json)
        else:
            with open(extent_json) as f:
                e = json.load(f)
            if north!=e['n'] or south!=e['s'] or east!=e['e'] or west!=e['w']:
                self.create_graph(north, south, east, west, graph_path, extent_json)
        print('[checked] osm graph\n')
    
    def distance_matrix(self, combined_csv, origins_json, destinations_json, req_nearby_pts):
        points = combined_csv[['lat','lon']].to_numpy()
        matrix = scipy.spatial.distance_matrix(points, points)
        matrix[matrix==0.0]=np.inf
        check_matrix=matrix.copy()
        with open(origins_json) as o_file:
            origins_file = json.load(o_file)
        with open(destinations_json) as d_file:
            destinations_file = json.load(d_file)
        for i in range(len(combined_csv['uno'])):
            @progressbar
            def progress_func():
                progress = (i+1)/len(combined_csv['uno'])
                text = 'calculating'
                return progress, text
            matrix[i].sort()
            e_dist_pts = []
            if len(destinations_file.keys()) < req_nearby_pts:
                range_pts = matrix[i][:]
            else:
                range_pts = matrix[i][:req_nearby_pts]
            for point in range_pts:
                e_dist_loc=combined_csv['uno'][np.where(check_matrix[i] == point)[0][0]]
                e_dist_pts.append(e_dist_loc)
            current_loc = combined_csv['uno'][i]
            if current_loc in origins_file.keys():
                origins_file[current_loc]['e_dist_pts'] = e_dist_pts
            if current_loc in destinations_file.keys():
                destinations_file[current_loc]['e_dist_pts'] = e_dist_pts
        with open(origins_json, "w") as outfile:
            json.dump(origins_file, outfile, indent=4)
        with open(destinations_json, "w") as outfile:
            json.dump(destinations_file, outfile, indent=4)
    
    def nearest_node(self, graph, origins_json, destinations_json, nearest_node_json):
        with open(origins_json) as o_file:
            origins_json_file = json.load(o_file)
        with open(destinations_json) as d_file:
            destinations_json_file = json.load(d_file)
        nearest_node_dict = {}
        print('\ncalculating nearby node...\n')
        count = 0
        for item in [i for i in origins_json_file.keys()]+[j for j in destinations_json_file.keys()]:
            @progressbar
            def progress_func():
                progress = count/len(destinations_json_file.keys())
                text = 'calculating'
                return progress, text
            count+=1
            if item in origins_json_file.keys():
                item_lat = float(origins_json_file[item]['lat'])
                item_lon = float(origins_json_file[item]['lon'])
            else:
                item_lat = float(destinations_json_file[item]['lat'])
                item_lon = float(destinations_json_file[item]['lon'])
            item_node = ox.distance.nearest_nodes(graph, item_lon, item_lat, return_dist=False)
            nearest_node_dict[item]=item_node
        with open(nearest_node_json, "w") as outfile:
            json.dump(nearest_node_dict, outfile, indent=4)

    def route_dist(self, graph, origins_json, destinations_json, nearest_node_json):
        with open(origins_json) as o_file:
            origins_json_file = json.load(o_file)
        with open(destinations_json) as d_file:
            destinations_json_file = json.load(d_file)
        with open(nearest_node_json) as n_file:
            nearest_node_file = json.load(n_file)
        print('\ncalculating route distances...\n')
        for origin in origins_json_file.keys():
            origin_node = nearest_node_file[origin]
            length_dict = {}
            for dest in origins_json_file[origin]['e_dist_pts']:
                dest_node = nearest_node_file[dest]
                length = nx.shortest_path_length(G=graph, source=origin_node, target=dest_node, weight='length')
                length_dict[dest]=length
            origins_json_file[origin]['r_dist']=length_dict
        with open(origins_json, "w") as outfile:
            json.dump(origins_json_file, outfile, indent=4)
        count=1
        for origin in destinations_json_file.keys():
            @progressbar
            def progress_func():
                progress = count/len(destinations_json_file.keys())
                text = 'calculating'
                return progress, text
            count+=1
            origin_node = nearest_node_file[origin]
            length_dict = {}
            for dest in destinations_json_file[origin]['e_dist_pts']:
                dest_node = nearest_node_file[dest]
                length = nx.shortest_path_length(G=graph, source=origin_node, target=dest_node, weight='length')
                length_dict[dest]=length
            destinations_json_file[origin]['r_dist']=length_dict
        with open(destinations_json,'w') as outfile:
            json.dump(destinations_json_file, outfile,indent=4)
        print('\n[checked] route distances.')


def main():
    origins_csv = os.path.join('.', 'data', 'origins.csv')
    destinations_csv = os.path.join('.', 'data', 'destinations.csv')
    combined_csv = pd.concat([pd.read_csv(origins_csv),pd.read_csv(destinations_csv)],ignore_index=True,copy=False)
    origins_json = os.path.join('.', 'database', 'origins.json')
    destinations_json = os.path.join('.', 'database', 'destinations.json')
    extent_json = os.path.join('.', 'database', 'extent.json')
    graph_path = os.path.join('.', 'database', 'graph.graphml')
    nearest_node_json = os.path.join('.', 'database', 'nearest_node.json')
    
    req_nearby_pts = 20
    
    conv = preparation()
    conv.generate_json(origins_csv, origins_json)
    conv.generate_json(destinations_csv, destinations_json)
    conv.generate_graph(combined_csv, extent_json, graph_path)
    conv.distance_matrix(combined_csv, origins_json, destinations_json, req_nearby_pts)
    print('\nloading graph...\n')
    graph = ox.io.load_graphml(graph_path)
    conv.nearest_node(graph, origins_json, destinations_json, nearest_node_json)
    conv.route_dist(graph, origins_json, destinations_json, nearest_node_json)

if __name__ == '__main__':
    main()