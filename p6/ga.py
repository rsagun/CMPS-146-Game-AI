import copy
import heapq
import metrics
import multiprocessing.pool as mpool
import os
import random
import shutil
import time
import math
import random

width = 200
height = 16

options = [
    "-",  # an empty space
    "X",  # a solid wall
    "?",  # a question mark block with a coin
    "M",  # a question mark block with a mushroom
    "B",  # a breakable block
    "o",  # a coin
    "|",  # a pipe segment
    "T",  # a pipe top
    "E",  # an enemy
    #"f",  # a flag, do not generate
    #"v",  # a flagpole, do not generate
    #"m"  # mario's start position, do not generate
]

# The level as a grid of tiles


class Individual_Grid(object):
    __slots__ = ["genome", "_fitness"]

    def __init__(self, genome):
        self.genome = copy.deepcopy(genome)
        self._fitness = None

    # Update this individual's estimate of its fitness.
    # This can be expensive so we do it once and then cache the result.
    def calculate_fitness(self):
        measurements = metrics.metrics(self.to_level())
        # Print out the possible measurements or look at the implementation of metrics.py for other keys:
        # print(measurements.keys())
        
        # Default fitness function: Just some arbitrary combination of a few criteria.  Is it good?  Who knows?
        # STUDENT Modify this, and possibly add more metrics.  You can replace this with whatever code you like.
        coefficients = dict(
            meaningfulJumpVariance=0.5,
            negativeSpace=0.6,
            pathPercentage=0.5,
            emptyPercentage=0.6,
            linearity=-0.5,
            solvability=2.0
        )
        self._fitness = sum(map(lambda m: coefficients[m] * measurements[m],
                                coefficients))
        return self

    # Return the cached fitness value or calculate it as needed.
    def fitness(self):
        if self._fitness is None:
            self.calculate_fitness()
        return self._fitness

    # Mutate a genome into a new genome.  Note that this is a _genome_, not an individual!
    def mutate(self, genome):
        # STUDENT implement a mutation operator, also consider not mutating this individual
        # STUDENT also consider weighting the different tile types so it's not uniformly random
        # STUDENT consider putting more constraints on this to prevent pipes in the air, etc

        # Weights for different blocks in mutation
        # Creates an exploration factor similar to the one in MCTS
        mutation_rate = 0.15
        empty_space = 0.30
        solid_wall = 0.1
        question_coin = 0.1
        question_mush = 0.1
        break_block = 0.05
        coin_float = 0.1
        top_pipe = 0.05
        vert_pipe = 0.05

        # Start mutation process
        left = 1
        right = width - 1
        for y in range(height):
            # Add constraint for pipes in air
            if y < 4:
                top_pipe = 0
                vert_pipe = 0
                mutation_rate = 0
            else:
                mutation_rate = 0.1
            for x in range(left, right):
                r = random.random()
                if mutation_rate > r:
                    r = random.random()
                    if r < vert_pipe:
                        genome[y+1][x] = 'X'
                        genome[y][x] = '|'
                        genome[y-1][x] = 'T'
                    elif r < top_pipe:
                        genome[y+2][x] = 'X'
                        genome[y][x] = 'T'
                        genome[y+1][x] = '|'
                    elif r < coin_float:
                        genome[y][x] = 'o'
                    elif r < break_block:
                        genome[y][x] = 'B'
                    elif r < question_mush:
                        genome[y][x] = 'M'
                    elif r < question_coin:
                        genome[y][x] = '?'
                    elif r < solid_wall:
                        genome[y][x] = 'X'
                    elif r < empty_space:
                        genome[y][x] = '-'
                    else:
                        continue
        return genome

    # Create zero or more children from self and other
    def generate_children(self, other):
        new_genome = copy.deepcopy(self.genome)
        # Leaving first and last columns alone...
        # do crossover with other
        left = 1
        right = width - 1                              

        for y in range(height):
            if y < 4:
                air = 1
                pipes = 0
            else:
                air = 0
                
            for x in range(left, right):
                # Constraint: Creates a sky in the top 4 rows
                if air is 1:
                    new_genome[y][x] = '-'     
                else:
                    # Constraint: Bases choice of a random number uses Uniform Crossover
                    r = random.random()
                    if r < 0.5:
                        if self.genome[y][x] == 'T' or self.genome[y][x] == '|':
                            if self.genome[y+1][x] == 'X':
                                new_genome[y][x] = self.genome[y][x]
                            else:
                                new_genome[y][x] = '-'
                        else:
                            new_genome[y][x] = self.genome[y][x] 
                        '''elif self.genome[y][x] == 'E':
                            if self.genome[y+1][x] == 'X':
                                new_genome[y][x] = self.genome[y][x]
                            else:
                                new_genome[y+1][x] = '-' '''                              
                    else:
                        if other.genome[y][x] == 'T' or other.genome[y][x] == '|':
                            if other.genome[y+1][x] == 'X':
                                new_genome[y][x] = other.genome[y][x]
                            else:
                                new_genome[y][x] = '-'
                        else:
                            new_genome[y][x] = other.genome[y][x] 
                        '''elif other.genome[y][x] == 'E':
                            if other.genome[y+1][x] == 'X':
                                new_genome[y][x] = other.genome[y][x]
                            else:
                                new_genome[y][x] = '-' '''
                        
        # do mutation; note we're returning a one-element tuple here
        new_genome = Individual.mutate(self, new_genome)
        
        return (Individual_Grid(new_genome),)

    # Turn the genome into a level string (easy for this genome)
    def to_level(self):
        return self.genome

    # These both start with every floor tile filled with Xs
    # STUDENT Feel free to change these
    @classmethod
    def empty_individual(cls):
        g = [["-" for col in range(width)] for row in range(height)]
        g[15][:] = ["X"] * width
        g[14][0] = "m"
        g[7][-1] = "v"
        for col in range(8, 14):
            g[col][-1] = "f"
        for col in range(14, 16):
            g[col][-1] = "X"
        return cls(g)

    @classmethod
    def random_individual(cls):
        # STUDENT consider putting more constraints on this to prevent pipes in the air, etc
        # STUDENT also consider weighting the different tile types so it's not uniformly random
        g = [random.choices(options, k=width) for row in range(height)]
        g[15][:] = ["X"] * width
        g[14][0] = "m"
        g[7][-1] = "v"
        g[8:14][-1] = ["f"] * 6
        g[14:16][-1] = ["X", "X"]
        return cls(g)


def offset_by_upto(val, variance, min=None, max=None):
    val += random.normalvariate(0, variance**0.5)
    if min is not None and val < min:
        val = min
    if max is not None and val > max:
        val = max
    return int(val)


def clip(lo, val, hi):
    if val < lo:
        return lo
    if val > hi:
        return hi
    return val

# Inspired by https://www.researchgate.net/profile/Philippe_Pasquier/publication/220867545_Towards_a_Generic_Framework_for_Automated_Video_Game_Level_Creation/links/0912f510ac2bed57d1000000.pdf


class Individual_DE(object):
    # Calculating the level isn't cheap either so we cache it too.
    __slots__ = ["genome", "_fitness", "_level"]

    # Genome is a heapq of design elements sorted by X, then type, then other parameters
    def __init__(self, genome):
        self.genome = list(genome)
        heapq.heapify(self.genome)
        self._fitness = None
        self._level = None

    # Calculate and cache fitness
    def calculate_fitness(self):
        measurements = metrics.metrics(self.to_level())
        # Default fitness function: Just some arbitrary combination of a few criteria.  Is it good?  Who knows?
        # STUDENT Add more metrics?
        # STUDENT Improve this with any code you like
        coefficients = dict(
            meaningfulJumpVariance=0.5,
            negativeSpace=0.6,
            pathPercentage=0.5,
            emptyPercentage=0.6,
            linearity=-0.5,
            solvability=2.0
        )
        penalties = 0
        # STUDENT For example, too many stairs are unaesthetic.  Let's penalize that
        if len(list(filter(lambda de: de[1] == "6_stairs", self.genome))) > 5:
            penalties -= 2
        # STUDENT If you go for the FI-2POP extra credit, you can put constraint calculation in here too and cache it in a new entry in __slots__.
        self._fitness = sum(map(lambda m: coefficients[m] * measurements[m],
                                coefficients)) + penalties
        return self

    def fitness(self):
        if self._fitness is None:
            self.calculate_fitness()
        return self._fitness

    def mutate(self, new_genome):
        # STUDENT How does this work?  Explain it in your writeup.
        # STUDENT consider putting more constraints on this, to prevent generating weird things
        if random.random() < 0.1 and len(new_genome) > 0:
            to_change = random.randint(0, len(new_genome) - 1)
            de = new_genome[to_change]
            new_de = de
            x = de[0]
            de_type = de[1]
            choice = random.random()
            if de_type == "4_block":
                y = de[2]
                breakable = de[3]
                if choice < 0.33:
                    x = offset_by_upto(x, width / 8, min=1, max=width - 2)
                elif choice < 0.66:
                    y = offset_by_upto(y, height / 2, min=0, max=height - 1)
                else:
                    breakable = not de[3]
                new_de = (x, de_type, y, breakable)
            elif de_type == "5_qblock":
                y = de[2]
                has_powerup = de[3]  # boolean
                if choice < 0.33:
                    x = offset_by_upto(x, width / 8, min=1, max=width - 2)
                elif choice < 0.66:
                    y = offset_by_upto(y, height / 2, min=0, max=height - 1)
                else:
                    has_powerup = not de[3]
                new_de = (x, de_type, y, has_powerup)
            elif de_type == "3_coin":
                y = de[2]
                if choice < 0.5:
                    x = offset_by_upto(x, width / 8, min=1, max=width - 2)
                else:
                    y = offset_by_upto(y, height / 2, min=0, max=height - 1)
                new_de = (x, de_type, y)
            elif de_type == "7_pipe":
                h = de[2]
                if choice < 0.5:
                    x = offset_by_upto(x, width / 8, min=1, max=width - 2)
                else:
                    h = offset_by_upto(h, 2, min=2, max=height - 4)
                new_de = (x, de_type, h)
            elif de_type == "0_hole":
                w = de[2]
                if choice < 0.5:
                    x = offset_by_upto(x, width / 8, min=1, max=width - 2)
                else:
                    w = offset_by_upto(w, 4, min=1, max=width - 2)
                new_de = (x, de_type, w)
            elif de_type == "6_stairs":
                h = de[2]
                dx = de[3]  # -1 or 1
                if choice < 0.33:
                    x = offset_by_upto(x, width / 8, min=1, max=width - 2)
                elif choice < 0.66:
                    h = offset_by_upto(h, 8, min=1, max=height - 4)
                else:
                    dx = -dx
                new_de = (x, de_type, h, dx)
            elif de_type == "1_platform":
                w = de[2]
                y = de[3]
                madeof = de[4]  # from "?", "X", "B"
                if choice < 0.25:
                    x = offset_by_upto(x, width / 8, min=1, max=width - 2)
                elif choice < 0.5:
                    w = offset_by_upto(w, 8, min=1, max=width - 2)
                elif choice < 0.75:
                    y = offset_by_upto(y, height, min=0, max=height - 1)
                else:
                    madeof = random.choice(["?", "X", "B"])
                new_de = (x, de_type, w, y, madeof)
            elif de_type == "2_enemy":
                pass
            new_genome.pop(to_change)
            heapq.heappush(new_genome, new_de)
        return new_genome

    def generate_children(self, other):
        # STUDENT How does this work?  Explain it in your writeup.
        pa = random.randint(0, len(self.genome) - 1) if len(self.genome) > 0 else 0
        pb = random.randint(0, len(other.genome) - 1) if len(other.genome) > 0 else 0
        a_part = self.genome[:pa] if len(self.genome) > 0 else []
        b_part = other.genome[pb:] if len(other.genome) > 0 else []
        ga = a_part + b_part
        b_part = other.genome[:pb] if len(other.genome) > 0 else []
        a_part = self.genome[pa:] if len(self.genome) > 0 else []
        gb = b_part + a_part
        # do mutation
        return Individual_DE(self.mutate(ga)), Individual_DE(self.mutate(gb))

    # Apply the DEs to a base level.
    def to_level(self):
        if self._level is None:
            base = Individual_Grid.empty_individual().to_level()
            for de in sorted(self.genome, key=lambda de: (de[1], de[0], de)):
                # de: x, type, ...
                x = de[0]
                de_type = de[1]
                if de_type == "4_block":
                    y = de[2]
                    breakable = de[3]
                    base[y][x] = "B" if breakable else "X"
                elif de_type == "5_qblock":
                    y = de[2]
                    has_powerup = de[3]  # boolean
                    base[y][x] = "M" if has_powerup else "?"
                elif de_type == "3_coin":
                    y = de[2]
                    base[y][x] = "o"
                elif de_type == "7_pipe":
                    h = de[2]
                    base[height - h - 1][x] = "T"
                    for y in range(height - h, height):
                        base[y][x] = "|"
                elif de_type == "0_hole":
                    w = de[2]
                    for x2 in range(w):
                        base[height - 1][clip(1, x + x2, width - 2)] = "-"
                elif de_type == "6_stairs":
                    h = de[2]
                    dx = de[3]  # -1 or 1
                    for x2 in range(1, h + 1):
                        for y in range(x2 if dx == 1 else h - x2):
                            base[clip(0, height - y - 1, height - 1)][clip(1, x + x2, width - 2)] = "X"
                elif de_type == "1_platform":
                    w = de[2]
                    h = de[3]
                    madeof = de[4]  # from "?", "X", "B"
                    for x2 in range(w):
                        base[clip(0, height - h - 1, height - 1)][clip(1, x + x2, width - 2)] = madeof
                elif de_type == "2_enemy":
                    base[height - 2][x] = "E"
            self._level = base
        return self._level

    @classmethod
    def empty_individual(_cls):
        # STUDENT Maybe enhance this
        g = []
        return Individual_DE(g)

    @classmethod
    def random_individual(_cls):
        # STUDENT Maybe enhance this
        elt_count = random.randint(8, 128)
        g = [random.choice([
            (random.randint(1, width - 2), "0_hole", random.randint(1, 8)),
            (random.randint(1, width - 2), "1_platform", random.randint(1, 8), random.randint(0, height - 1), random.choice(["?", "X", "B"])),
            (random.randint(1, width - 2), "2_enemy"),
            (random.randint(1, width - 2), "3_coin", random.randint(0, height - 1)),
            (random.randint(1, width - 2), "4_block", random.randint(0, height - 1), random.choice([True, False])),
            (random.randint(1, width - 2), "5_qblock", random.randint(0, height - 1), random.choice([True, False])),
            (random.randint(1, width - 2), "6_stairs", random.randint(1, height - 4), random.choice([-1, 1])),
            (random.randint(1, width - 2), "7_pipe", random.randint(2, height - 4))
        ]) for i in range(elt_count)]
        return Individual_DE(g)


Individual = Individual_Grid


def generate_successors(population, counter):
    # Flag determines selection method maybe base off generation?
    if counter % 2 == 0:
        flag = 1
    else:
        flag = 0
    results = []
    # STUDENT Design and implement this
    # Hint: Call generate_children() on some individuals and fill up results.
    # Select based on fitness, calls generate children based on selected 
    #best = max(population, key=Individual.fitness)

    if flag is 0:
        ''' Selection Method #1: Roulette Selection '''
        # Gets the probability for each indiviudal in a list
        print("Running Roulette")
        prob = get_probability_list(population)

        # Draw new population
        # 40 + 1 cause 1st breed with rest = 40
        #print(len(population))
        new_population = roulette_wheel_select(population, prob, int(0.8*len(population)))
        
        # Should have multiple parents to breed in new_population
        #print("New Population: ", new_population)

    else:
        new_population = []
        ''' Selection Method #2: Elitist Selection '''        
        # Gets the current best contenders
        print("Running Elitist")
        #print("Pop ", population)
        new_population = get_elitist_population(population, int(0.8*len(population)))

        # Should have multiple parents to breed in new_population
        #print("New Population: ", new_population)

    # Create Children
    x = random.randint(0, len(new_population)-1)
    for y in range(0, len(new_population)):
        r = random.random()
        '''if r < 0.4:
            successor = Individual.empty_individual()
        else:
            successor = Individual.random_individual()'''
        successor = new_population[x]
        other = new_population[y]
        children = Individual.generate_children(successor, other)
        results.append(children[0])
        
    #print("results ", results)
    #exit()
    
    return results

def get_elitist_population(population, pop_num):
    # Gets the current best contender
    new_population = []
    #counter = 0
    #print("NUmber of elements: ", len(population))
    while pop_num is not 0:
        best = max(population, key=Individual.fitness)
        new_population.append(best)
        population.remove(best)
        #counter += 1
        pop_num -= 1
        #print("Counter: ",counter)
    return new_population

def get_probability_list(population):
    fitness_list = []
    for individual in population:
        fit = Individual.fitness(individual)
        if fit < 0:
            fit = -fit
        fitness_list.append(fit)
        #print("Individual: ", individual)
        #print("fit: ", fit)
        
    total_fitness = sum(fitness_list)
    #print("total_fitness: ", total_fitness)
    relative_fitness = [f/total_fitness for f in fitness_list]
    # Generate probability intervals based on equation
    prob = [float(sum(relative_fitness[:i+1])) for i in range(len(relative_fitness))]
    return prob

def roulette_wheel_select(population, prob, number):
    new_population = []
    for n in range(number):
        r = random.random()
        #print("r: ", r)
        for(i, individual) in enumerate(population):
            #print("individual: ", individual)
            #print("r ,", r, "prob ", prob[i])
            if r <= prob[i]:
                #print("individual picked ", individual)
                new_population.append(individual)
                break
    return new_population

def ga():
    # STUDENT Feel free to play with this parameter
    pop_limit = 180
    # Code to parallelize some computations
    batches = os.cpu_count()
    if pop_limit % batches != 0:
        print("It's ideal if pop_limit divides evenly into " + str(batches) + " batches.")
    batch_size = int(math.ceil(pop_limit / batches))
    with mpool.Pool(processes=os.cpu_count()) as pool:
        init_time = time.time()
        # STUDENT (Optional) change population initialization
        population = [Individual.random_individual() if random.random() < 0.45
                      else Individual.empty_individual()
                      for _g in range(pop_limit)]
        # But leave this line alone; we have to reassign to population because we get a new population that has more cached stuff in it.
        print("CALCULATE FITNESS")
        population = pool.map(Individual.calculate_fitness,
                              population,
                              batch_size)
        init_done = time.time()
        print("Created and calculated initial population statistics in:", init_done - init_time, "seconds")
        generation = 0
        start = time.time()
        now = start
        print("Use ctrl-c to terminate this loop manually.")
        try:
            counter = 0
            best_fit = 0.0
            new_best_fit = 0.0
            N = 10
            while True:
                now = time.time()
                # Print out statistics
                if generation > 0:
                    best = max(population, key=Individual.fitness)
                    print("Generation:", str(generation))
                    print("Max fitness:", str(best.fitness()))
                    print("Average generation time:", (now - start) / generation)
                    print("Net time:", now - start)
                    with open("levels/last.txt", 'w') as f:
                        for row in best.to_level():
                            f.write("".join(row) + "\n")
                generation += 1

                # STOPPING CONDITION: Every 10th generation check to see
                # if fitness changed drastically.
                
                '''if generation % 10 == 0 and generation != 0:
                    greatest = max(population, key=Individual.fitness)
                    new_best_fit = Individual.fitness(greatest)
                elif generation % 10 == 1:
                    cur_best = max(population, key=Individual.fitness)
                    best_fit = Individual.fitness(cur_best)
                if generation % 10 == 0 and generation != 0 and (best_fit + 0.1) < new_best_fit:
                    break
                else:
                    best_fit = new_best_fit'''

                # STOPPING CONDITION: Breaks after N generations
                if generation > N:
                    break
                    
                # STUDENT Also consider using FI-2POP as in the Sorenson & Pasquier paper
                gentime = time.time()
                print("Generate Successors")
                next_population = generate_successors(population, counter)
                gendone = time.time()
                print("Generated successors in:", gendone - gentime, "seconds")
                # Calculate fitness in batches in parallel
                next_population = pool.map(Individual.calculate_fitness,
                                           next_population,
                                           batch_size)
                popdone = time.time()
                print("Calculated fitnesses in:", popdone - gendone, "seconds")
                population = next_population
                counter += 1
        except KeyboardInterrupt:
            pass
    return population


if __name__ == "__main__":
    final_gen = sorted(ga(), key=Individual.fitness, reverse=True)
    best = final_gen[0]
    print("Best fitness: " + str(best.fitness()))
    now = time.strftime("%m_%d_%H_%M_%S")
    # STUDENT You can change this if you want to blast out the whole generation, or ten random samples, or...
    for k in range(0, 1):
        with open("levels/" + now + "_" + str(k) + ".txt", 'w') as f:
            for row in final_gen[k].to_level():
                f.write("".join(row) + "\n")
