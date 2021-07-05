import csv, json, os, sys
import pandas as pd
import numpy as np
import osmnx as ox
import networkx as nx
import scipy

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
        south = combined_csv['lat'].min()-0.05
        west = combined_csv['lon'].min()-0.05
        north = combined_csv['lat'].max()+0.05
        east = combined_csv['lon'].max()+0.05
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
        with open(origins_json) as o_file:
            origins_file = json.load(o_file)
        with open(destinations_json) as d_file:
            destinations_file = json.load(d_file)
        for i in range(len(combined_csv['uno'])):
            # progressbar
            progress = (i+1)/len(combined_csv['uno'])
            block = int(round(10*progress))
            progress_text = "\rCalculating: [{0}] {1:.2f}% {2}".format( "#"*block + "-"*(10-block), progress*100, 'completed')
            sys.stdout.write(progress_text)
            sys.stdout.flush()
            matrix[i].sort()
            e_dist_pts = []
            if len(destinations_file.keys()) < req_nearby_pts:
                range_pts = matrix[i][:]
            else:
                range_pts = matrix[i][:req_nearby_pts]
            for point in range_pts:
                e_dist_loc=combined_csv['uno'][np.where(matrix[i] == point)[0][0]]
                if e_dist_loc not in origins_file.keys():
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
    
    def route_dist(self, graph_path, origins_json, destinations_json):
        print('\nloading graph...')
        graph = ox.io.load_graphml(graph_path)
        with open(origins_json) as o_file:
            origins_json_file = json.load(o_file)
        with open(destinations_json) as d_file:
            destinations_json_file = json.load(d_file)
        print('\ncalculating route distances...\n')
        for origin in origins_json_file.keys():
            origin_lat = float(origins_json_file[origin]['lat'])
            origin_lon = float(origins_json_file[origin]['lon'])
            origin_node = ox.distance.nearest_nodes(graph, origin_lon, origin_lat, return_dist=False)
            length_dict = {}
            for dest in origins_json_file[origin]['e_dist_pts']:
                dest_lat = float(destinations_json_file[dest]['lat'])
                dest_lon = float(destinations_json_file[dest]['lon'])
                dest_node = ox.distance.nearest_nodes(graph, dest_lon, dest_lat, return_dist=False)
                length = nx.shortest_path_length(G=graph, source=origin_node, target=dest_node, weight='length')
                length_dict[dest]=length
            origins_json_file[origin]['r_dist']=length_dict
        with open(origins_json, "w") as outfile:
            json.dump(origins_json_file, outfile, indent=4)
        count=1
        for origin in destinations_json_file.keys():
            # progressbar
            progress = count/len(destinations_json_file.keys())
            block = int(round(10*progress))
            progress_text = "\rCalculating: [{0}] {1:.2f}% {2}".format( "#"*block + "-"*(10-block), progress*100, 'completed')
            sys.stdout.write(progress_text)
            sys.stdout.flush()
            count+=1
            origin_lat = float(destinations_json_file[origin]['lat'])
            origin_lon = float(destinations_json_file[origin]['lon'])
            origin_node = ox.distance.nearest_nodes(graph, origin_lon, origin_lat, return_dist=False)
            length_dict = {}
            for dest in destinations_json_file[origin]['e_dist_pts']:
                dest_lat = float(destinations_json_file[dest]['lat'])
                dest_lon = float(destinations_json_file[dest]['lon'])
                dest_node = ox.distance.nearest_nodes(graph, dest_lon, dest_lat, return_dist=False)
                length = nx.shortest_path_length(G=graph, source=origin_node, target=dest_node, weight='length')
                length_dict[dest]=length
            destinations_json_file[origin]['r_dist']=length_dict
        with open(destinations_json,'w') as outfile:
            json.dump(destinations_json_file, outfile,indent=4)
        print('\n[checked] route distances.\n')

origins_csv = os.path.join('.', 'data', 'origins.csv')
destinations_csv = os.path.join('.', 'data', 'destinations.csv')
combined_csv = pd.concat([pd.read_csv(origins_csv),pd.read_csv(destinations_csv)],ignore_index=True,copy=False)
origins_json = os.path.join('.', 'database', 'origins.json')
destinations_json = os.path.join('.', 'database', 'destinations.json')
extent_json = os.path.join('.', 'database', 'extent.json')
graph_path = os.path.join('.', 'database', 'graph.graphml')
req_nearby_pts = 20

def main():
    conv = preparation()
    conv.generate_json(origins_csv, origins_json)
    conv.generate_json(destinations_csv, destinations_json)
    conv.generate_graph(combined_csv, extent_json, graph_path)
    conv.distance_matrix(combined_csv, origins_json, destinations_json, req_nearby_pts)
    conv.route_dist(graph_path, origins_json, destinations_json)

if __name__ == '__main__':
    main()