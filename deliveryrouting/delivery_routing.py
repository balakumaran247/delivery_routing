import numpy as np
import random, operator, os, json, sys
import pandas as pd
import matplotlib.pyplot as plt

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
            # progressbar
            progress = i/self.generations
            block = int(round(10*progress))
            progress_text = "\rCalculating best route: [{0}] {1:.2f}% {2}".format( "#"*block + "-"*(10-block), progress*100, 'completed')
            sys.stdout.write(progress_text)
            sys.stdout.flush()
            pop = self.next_generation(pop)
        best_route_index = self.rank_routes(pop)[0][0]
        best_route = pop[best_route_index]
        for o_key in self.origins_file.keys():
            pivot = best_route.index(o_key)
            list1 = best_route[pivot:]
            list2 = best_route[:pivot]
            ordered_best_route = list1+list2
        return ordered_best_route

def route_formatted(best_route_list):
    best_route_string = ''
    for item in best_route_list:
        if best_route_list.index(item) != len(best_route_list)-1:
            best_route_string += str(item) + ' -> '
        else:
            best_route_string += str(item)
    return best_route_string

def main():
    origins_json = os.path.join('.', 'database', 'origins.json')
    destinations_json = os.path.join('.', 'database', 'destinations.json')
    with open(origins_json) as o_file:
        origins_file= json.load(o_file)
    with open(destinations_json) as d_file:
        destinations_file= json.load(d_file)
    city_list = []
    for i in origins_file.keys():
        city_list.append(i)
    for j in destinations_file.keys():
        city_list.append(j)
    
    pop_size = 200
    elite_size=10
    mutation_rate=0.1
    generations=1000

    routing = delivery_routing(origins_file, destinations_file, pop_size, elite_size, mutation_rate, generations)
    best_route_list = routing.genetic_algorithm(city_list)
    best_route = route_formatted(best_route_list)
    print('\n',best_route)

if __name__ == '__main__':
    main()