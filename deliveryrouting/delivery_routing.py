import numpy as np
import random, operator, os, json, sys
import folium
import pandas as pd
import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
from deliveryrouting.generate_input import progressbar

class Fitness:
    def __init__(self, route, origins_file, destinations_file):
        self.route = route
        self.origins_file = origins_file
        self.destinations_file = destinations_file
        self.distance = 0
        self.fitness= 0.0
    
    def routeDistance(self):
        if self.distance ==0:
            pathDistance = 0
            for i in range(0, len(self.route)):
                fromCity = self.route[i]
                toCity = None
                if i + 1 < len(self.route):
                    toCity = self.route[i + 1]
                else:
                    toCity = self.route[0]
                if fromCity in self.origins_file.keys():
                    if toCity not in self.origins_file[fromCity]['r_dist'].keys():
                        pathDistance += np.inf
                    else:
                        pathDistance += self.origins_file[fromCity]['r_dist'][toCity]
                else:
                    if toCity not in self.destinations_file[fromCity]['r_dist'].keys():
                        pathDistance += np.inf
                    else:
                        pathDistance += self.destinations_file[fromCity]['r_dist'][toCity]
            self.distance = pathDistance
        return self.distance
    
    def routeFitness(self):
        if self.fitness == 0:
            self.fitness = 1 / float(self.routeDistance())
        return self.fitness

class delivery_routing:
    '''
    Computes the optimized route.
    '''

    def __init__(self, origins_file, destinations_file, pop_size, elite_size, mutation_rate, generations):
        self.origins_file = origins_file
        self.destinations_file = destinations_file
        self.pop_size = pop_size
        self.elite_size = elite_size
        self.mutation_rate = mutation_rate
        self.generations = generations

    def create_route(self, city_list):
        route = random.sample(city_list, len(city_list))
        return route
    
    def initial_population(self, city_list):
        population = []
        for i in range(0, self.pop_size):
            population.append(self.create_route(city_list))
        return population
    
    def rank_routes(self, population):
        fitness_results = {}
        for i in range(0,len(population)):
            fitness_results[i] = Fitness(population[i], self.origins_file, self.destinations_file).routeFitness()
        return sorted(fitness_results.items(), key = operator.itemgetter(1), reverse = True)
    
    def selection(self, pop_ranked):
        selection_results = []
        df = pd.DataFrame(np.array(pop_ranked), columns=["Index","Fitness"])
        df['cum_sum'] = df.Fitness.cumsum()
        df['cum_perc'] = 100*df.cum_sum/df.Fitness.sum()
        for i in range(0, self.elite_size):
            selection_results.append(pop_ranked[i][0])
        for i in range(0, len(pop_ranked) - self.elite_size):
            pick = 100*random.random()
            for i in range(0, len(pop_ranked)):
                if pick <= df.iat[i,3]:
                    selection_results.append(pop_ranked[i][0])
                    break
        return selection_results

    def mating_pool(self, population, selection_results):
        matingpool = []
        for i in range(0, len(selection_results)):
            index = selection_results[i]
            matingpool.append(population[index])
        return matingpool
    
    def breed(self, parent1, parent2):
        child = []
        childP1 = []
        childP2 = []
        geneA = int(random.random() * len(parent1))
        geneB = int(random.random() * len(parent1))
        startGene = min(geneA, geneB)
        endGene = max(geneA, geneB)
        for i in range(startGene, endGene):
            childP1.append(parent1[i])
        childP2 = [item for item in parent2 if item not in childP1]
        child = childP1 + childP2
        return child

    def breed_population(self, matingpool):
        children = []
        length = len(matingpool) - self.elite_size
        pool = random.sample(matingpool, len(matingpool))
        for i in range(0,self.elite_size):
            children.append(matingpool[i])
        for i in range(0, length):
            child = self.breed(pool[i], pool[len(matingpool)-i-1])
            children.append(child)
        return children
    
    def mutate(self, individual):
        for swapped in range(len(individual)):
            if(random.random() < self.mutation_rate):
                swapWith = int(random.random() * len(individual))
                
                city1 = individual[swapped]
                city2 = individual[swapWith]
                
                individual[swapped] = city2
                individual[swapWith] = city1
        return individual
    
    def mutate_population(self, population):
        mutated_pop = []
        for ind in range(0, len(population)):
            mutated_ind = self.mutate(population[ind])
            mutated_pop.append(mutated_ind)
        return mutated_pop
    
    def next_generation(self, current_gen):
        pop_ranked = self.rank_routes(current_gen)
        selectionResults = self.selection(pop_ranked)
        matingpool = self.mating_pool(current_gen, selectionResults)
        children = self.breed_population(matingpool)
        next_generation = self.mutate_population(children)
        return next_generation
    
    def genetic_algorithm(self, population):
        pop = self.initial_population(population)
        for i in range(0, self.generations):
            @progressbar
            def progress_func():
                progress = i/self.generations
                text = 'calculating best route'
                return progress, text
            pop = self.next_generation(pop)
        best_route_index = self.rank_routes(pop)[0][0]
        best_route = pop[best_route_index]
        for o_key in self.origins_file.keys():
            pivot = best_route.index(o_key)
            list1 = best_route[pivot:]
            list2 = best_route[:pivot]
            ordered_best_route = list1+list2
        return ordered_best_route

def exclusion():
    x = input('Exclude Locations:')
    excluded_list = [j.strip() for j in x.split(',')]
    return excluded_list

def route_formatted(best_route_list):
    best_route_string = ''
    for item in best_route_list:
        if best_route_list.index(item) != len(best_route_list)-1:
            best_route_string += str(item) + ' -> '
        else:
            best_route_string += str(item)
    return best_route_string

def interactive_mapping(graph_path, origins_file, destinations_file, best_route_list, nearest_node_file):
    print('\nloading graph...\n')
    graph = ox.io.load_graphml(graph_path)
    print('\nGenerating Interactive Map...\n')
    o_lat = [origins_file[key]['lat'] for key in origins_file.keys()][0]
    o_lon = [origins_file[key]['lon'] for key in origins_file.keys()][0]
    o_pop = [key for key in origins_file.keys()][0]
    m = folium.Map(location= [o_lat, o_lon],tiles= 'OpenStreetMap', zoom_start=10)
    folium.Marker(location=[o_lat, o_lon],popup=o_pop).add_to(m)
    
    for key in destinations_file.keys():
        d_lat = destinations_file[key]['lat']
        d_lon = destinations_file[key]['lon']
        folium.CircleMarker(location=[d_lat, d_lon], radius=5, color='red', fill_color='red', fill_opacity=1, popup=key).add_to(m)
    for i in range(0, len(best_route_list)):
        fromCity = best_route_list[i]
        toCity = None
        if i + 1 < len(best_route_list):
            toCity = best_route_list[i + 1]
        else:
            toCity = best_route_list[0]
        o_n = nearest_node_file[fromCity]
        d_n = nearest_node_file[toCity]
        route = nx.shortest_path(G=graph, source=o_n, target=d_n, weight='length')
        ox.folium.plot_route_folium(graph, route, route_map=m)
    return m
    

def main():
    excluded_list = exclusion()
    origins_json = os.path.join('.', 'database', 'origins.json')
    destinations_json = os.path.join('.', 'database', 'destinations.json')
    nearest_node_json = os.path.join('.', 'database', 'nearest_node.json')
    graph_path = os.path.join('.', 'database', 'graph.graphml')

    with open(origins_json) as o_file:
        origins_file= json.load(o_file)
    with open(destinations_json) as d_file:
        destinations_file= json.load(d_file)
    with open(nearest_node_json) as n_file:
        nearest_node_file= json.load(n_file)
    
    city_list = []
    for i in origins_file.keys():
        city_list.append(i)
    for j in destinations_file.keys():
        if j not in excluded_list:
            city_list.append(j)
    
    pop_size = 200
    elite_size=40
    mutation_rate=0.01
    generations=1000

    routing = delivery_routing(origins_file, destinations_file, pop_size, elite_size, mutation_rate, generations)
    best_route_list = routing.genetic_algorithm(city_list)
    best_route = route_formatted(best_route_list)
    interactive_map = interactive_mapping(graph_path, origins_file, destinations_file, best_route_list, nearest_node_file)
    return best_route, interactive_map

if __name__ == '__main__':
    main()