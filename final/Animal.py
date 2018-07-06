from random import choice, random, randint, choices
from math import ceil
import os
from time import time
import multiprocessing.pool as mpool
from functools import partial
from Environment import Environment

# No matter what environment is we hav esimilar creatures.
# Not weighting environment when taking in to account the sp

possible_traits = {
    'temperature': [['fur', random()], ['scales', random()], ['hide', random()]],
    'size': [random() for i in range(5)],
    'diet': ['herbivore', 'carnivore', 'omnivore'],
    'aggression': [random() for i in range(5)],
    'strength': [random() for i in range(5)],
    'speed': [random() for i in range(5)],
    'fat': [random() for i in range(5)],
    'reproduction': ['mammalian', 'reptilian', 'avian', 'insect'],
    'toes': [randint(0, 10)],
    'arms': [randint(0, 4)],
    'legs': [choice([0, 2, 3, 4])],
    'shoulders': [choice([2, 4])],
    'chest': ['scrawny', 'meaty', 'pointed'],
    'neck': ['short', 'long', 'thick', 'flexible'],
    'skin type': ['dry', 'moist', 'webby', 'hairy', 'flabby', 'swole']
    
}   

class Animal:
    def __init__(self, traits={}):
        if not traits:
            self.traits = {key: choice(list(value)) for key, value in possible_traits.items()}
            self.traits['size'] += (self.traits['toes']*.005 + self.traits['arms']*.025 + self.traits['legs']*.025)/1.25
            self.traits['speed'] -= .2*self.traits['size']
        else:
            self.traits = traits
            '''self.traits['size'] = random()
            self.traits['speed'] = random()
            self.traits['strength'] = random()'''

        self._fitness = 0

    def __repr__(self):
        return '\n'.join([str(key) + ": " + str(value) for key, value in self.traits.items()])

    def calculate_fitness(self, environment):
        # Stores the fitness created by the functions
        coefficients = dict(
            temperature=self.temperature_fitness(environment),
            food_density=self.food_fitness(environment),
            limb=self.limb_fitness(environment),
            combative=self.combative_fitness(environment),
            athletic=self.athletic_fitness(environment),
            disaster=self.disaster_fitness(environment),
            pollutive=self.pollutive_fitness(environment)
        )

        # Weight extremes with respective factors
        factors = self.calculate_balance(environment)

        self._fitness = sum(map(lambda m: coefficients[m] * factors[m], coefficients))
        return self

    def calculate_balance(self, environment):
        # Dict keys are same as coe and values are 0 - 1 that are multiplied on to the fitness
        # Something that could go wrong is everyting is weighted the same amount or too similar

        # Temperature/Food/Limb/Combative/Athletic/Disaster/Pollutive

        # Weights higher for more extreme temperatures (really hot or really cold)
        temp = environment.traits['temperature']
        temp_factor = ((1 - (abs(.5 - temp)) - .5) / .5)

        # Weights higher for more extreme amounts of resources (a lot or little)
        # Should it be only in cases of little to no food?
        p_d = environment.traits['plant density']
        a_d = environment.traits['prey density']
        if self.traits['diet'] == 'carnivore':
            food_factor = 1 - a_d
        elif self.traits['diet'] == 'herbivore':
            food_factor = 1 - p_d
        else:
            # Might have to switch a bit
            food_factor = ((1 - (abs(.25 - ((p_d + a_d) / 2))) - .25) / .75)

        # Weight for limb/skin type
        fert = environment.traits['fertility']
        nat_d = environment.traits['natural disaster']
        sun_expose = environment.traits['sun exposure']
        precip = environment.traits['precipitation']
        wind = environment.traits['wind']
        limb_factor = (fert + nat_d + sun_expose + precip + wind) / 5

        # Weight for combative
        hostility = environment.traits['hostility']
        combative_factor = 1 - hostility

        # Weight for athletic
        geovar = environment.traits['geovariance']
        athletic_factor = 1 - geovar

        # Weight for disaster
        n_d = environment.traits['natural disaster']
        disaster_factor = 1 - n_d

        # Weight for pollutive
        pollu = environment.traits['pollution']
        pollutive_factor = 1 - pollu

        # Weights for limbs
        factors = dict(
            temperature=temp_factor,
            food_density=food_factor,
            limb=limb_factor,
            combative=combative_factor,
            athletic=athletic_factor,
            disaster=disaster_factor,
            pollutive=pollutive_factor
        )
        return factors

    def temperature_fitness(self, environment):
        temp = self.traits['temperature']
        env_temp = environment.traits['temperature']
        if temp[0] == 'fur':
            fitness = abs(temp[1] - env_temp) + (-.15 if env_temp > .5 else .15)
            fitness = (fitness + .15) / 1.3
        elif temp[0] == 'scales':
            fitness = ((0.7 * env_temp) + (0.3 * temp[1]))
        else:
            fitness = ((1 - (abs(.5 - env_temp)) - .5)) + .5 * (temp[1])
            if env_temp > .5:
                fitness = 1 - fitness

        return fitness

    def food_fitness(self, environment):
        p_d = environment.traits['plant density']
        a_d = environment.traits['prey density']
        size = self.traits['size']
        diet = self.traits['diet']
        speed = self.traits['speed']
        aggression = self.traits['aggression']

        # bigger size ----> more food required
        # carnivore ----> more animal density
        # herbivore ---> more plant density
        # omnivore ---> mix of both
        # if prey > .6 theres a variance of kinds of prey
        # if big and fast a higher prey density is better
        # if big with low prey density not as fit as someone with small and prey density
        # lot of prey bigger is better / small of prey smaller is better
        # faster as carnivore is better
        # herbivore use aggression to run into fitness to differentiate them between each other

        if diet == 'carnivore':
            # higher speed higher aggression lower size
            fitness = (a_d + speed + aggression - size) / 2

        elif diet == 'herbivore':
            fitness = ((p_d - size) + 1) / 2

        elif diet == 'omnivore':
            fitness = ((.5 * (a_d + speed + aggression) + .5 * p_d) - size) / 2

        return fitness

    def limb_fitness(self, environment):
        # how feasible to work in environment.
        # Only works off of skin type does not include limbs as of now.
        # ('none', 'dry', 'moist', 'webby', 'hairy', 'flabby', 'swole')

        # Abiotic Factors of the environment
        fert = environment.traits['fertility']
        nat_d = environment.traits['natural disaster']
        sun_expose = environment.traits['sun exposure']
        precip = environment.traits['precipitation']
        wind = environment.traits['wind']

        # Species Factors that affect the fitness
        skin_type = self.traits['skin type']

        # Natural disaster same in all skin type?
        # Moist - mid fertil for living in dirt, high precip for body immersion, low ND makes sense,
        # small medium sun do not want to boil or steam, small wind do not want to dry out skin
        # If want more diversity change the natural disaster number.
        if skin_type == 'moist':
            # Check the different abiotic facors
            fitness = (((1 - abs(.7 - fert)) - 0.3) / .7) + (1 - abs(0 - nat_d)) + \
                      (1 - (abs(.4 - sun_expose) - .4) / .6) + (1 - abs(1 - precip)) + (
                      (1 - (abs(.25 - wind)) - .25) / .75)

        # Webby - fertility does not necessairly affect, low ND, low average does not like extreme weather,
        # low average recip not extreme, low average wind
        elif skin_type == 'webby':
            # Check the different abiotic facors
            fitness = ((1 - (abs(.65 - fert)) - .35) / .65) + (1 - abs(0 - nat_d)) + \
                      ((1 - (abs(.25 - sun_expose)) - .25) / .75) + ((1 - (abs(.4 - precip)) - .4) / .6) + (
                      (1 - (abs(.15 - wind)) - .15) / .85)

        # Hairy - fert average, low precip, low ND, low average sun exposure sweating no energy, high average wind
        elif skin_type == 'hairy':
            # Check the different abiotic facors
            fitness = ((1 - (abs(.5 - fert)) - .5) / .5) + (1 - abs(0 - nat_d)) + \
                      ((1 - (abs(.35 - sun_expose)) - .35) / .65) + ((1 - (abs(.15 - precip)) - .15) / .85) + (
                      (1 - (abs(.75 - wind)) - .25) / .75)


        # Flabby - fert above average eat grass, low ND, high average sun Exposure,
        # low precip too wet dirt, below average wind
        elif skin_type == 'flabby':
            # Check the different abiotic facors
            fitness = ((1 - (abs(.75 - fert)) - .25) / .75) + (1 - abs(0 - nat_d)) + \
                      ((1 - (abs(.75 - sun_expose)) - .25) / .75) + ((1 - (abs(.15 - precip)) - .15) / .85) + (
                      (1 - (abs(.25 - wind)) - .25) / .75)


        # Swole - fert high grow stuff and pick, low ND, above average sun exposure, precip low affect grip on things,
        # low wind does not want to fight against it (wind resistance)
        elif skin_type == 'swole':
            # Check the different abiotic facors
            fitness = ((1 - (abs(.9 - fert)) - .1) / .9) + (1 - abs(0 - nat_d)) + \
                      ((1 - (abs(.60 - sun_expose)) - .4) / .6) + ((1 - (abs(.15 - precip)) - .15) / .85) + (
                      (1 - (abs(.20 - wind)) - .2) / .8)

        # Dry - Low average fertility, low ND makes sense, high average sun exposure like to sun bathe, low precip does not like wet skin,
        # moderately high wind cause like to dry skin in wind
        else:
            # Check the different abiotic facors
            fitness = ((1 - (abs(.2 - fert)) - .2) / .8) + (1 - abs(0 - nat_d)) + \
                      ((1 - (abs(.85 - sun_expose)) - .15) / .85) + ((1 - (abs(.15 - precip)) - .15) / .85) + (
                      (1 - (abs(.75 - wind)) - .25) / .75)

        return fitness / 5

    def combative_fitness(self, environment):
        fitness_list = []
        # How likely creature is to survive in environment
        # Natural disasters weather geovariance speed strength agility size pollution
        agility = self.traits['speed']
        strength = self.traits['strength']
        size = self.traits['size']
        aggro = self.traits['aggression']

        geovar = environment.traits['geovariance']
        n_d = environment.traits['natural disaster']
        pollu = environment.traits['pollution']
        hostility = environment.traits['hostility']
        env_list = [(geovar, 'geovariance'), (n_d, 'natural disaster'), (pollu, 'pollution'),
                    (hostility, 'hostility')]
        '''
        # all factors scale from 0-1, 0 being worst case for the creature, 1 being best
        # creatures general athleticism in the environment, normalized
        # stronger and faster creatures do better in environments which require a lot of
        # strenuous movement
        athletics_factor = ((agility + strength - geovar) + 1) / 3'''

        '''
        # creatures general ability to get away from natural disasters
        # faster and stronger creatures get away from disasters, bigger ones can have more trouble doing so
        disaster_factor = ((agility + strength - size - n_d) + 2) / 4'''

        # creatures general ability to deal with other creatures
        # since size(and maybe strength in the future) is partially influenced by limbs, limbs add to
        # creatures fighting capability
        fitness = ((agility - (1 - size) + aggro + strength - hostility) + 1) / 5

        '''
        # creatures reaction to environmental pollution(foreign substances)
        # stronger creatures can fare better against pollutants, but bigger ones suffer
        pollutive_factor = ((strength - size - pollu) + 2) / 3
        if self.traits['diet'] is 'carnivore':
            pollutive_factor *= .5
        if self.traits['diet'] is 'omnivore':
            pollutive_factor *= .75'''

        # weight hostility fitness based on the prevalence of the environment. I.E a creature that survives well in a
        # polluted environment is better than a combative creature in that same environment
        # sorted list of environmental variables in order to weight which is the most important survivability
        '''env_list.sort()
        # print(env_list)
        # creates list in order of the most important fitness to least
        for i in env_list:
            if i[1] is 'geovariance':
                fitness_list.append(athletics_factor)
            if i[1] is 'natural disaster':
                fitness_list.append(disaster_factor)
            if i[1] is 'hostility':
                fitness_list.append(combative_factor)
            else:
                fitness_list.append(pollutive_factor)
        # most important fitness weighted the most
        fitness = fitness_list[0] * .4 + fitness_list[1] * .3 + fitness_list[1] * .2 + fitness_list[1] * .1

        # fitness = (geovarathletics_factor + n_ddisaster_factor + hostilitycombative_factor + pollu*pollutive_factor)/4

        #print("Athleticism: ", athletics_factor, "/ Disaster Survival: ", disaster_factor, "/ Prowess: ",
              #combative_factor, "/ Fragility: ", pollutive_factor)'''

        return fitness

    def athletic_fitness(self, environment):
        agility = self.traits['speed']
        strength = self.traits['strength']

        geovar = environment.traits['geovariance']

        # all factors scale from 0-1, 0 being worst case for the creature, 1 being best
        # creatures general athleticism in the environment, normalized
        # stronger and faster creatures do better in environments which require a lot of
        # strenuous movement
        fitness = ((agility + strength - geovar) + 1) / 3

        return fitness

    def disaster_fitness(self, environment):
        agility = self.traits['speed']
        strength = self.traits['strength']
        size = self.traits['size']

        # creatures general ability to get away from natural disasters
        # faster and stronger creatures get away from disasters, bigger ones can have more trouble doing so
        n_d = environment.traits['natural disaster']

        fitness = ((agility + strength - size - n_d) + 2) / 4

        return fitness

    def pollutive_fitness(self, environment):
        strength = self.traits['strength']
        size = self.traits['size']

        pollu = environment.traits['pollution']

        # creatures reaction to environmental pollution(foreign substances)
        fitness = ((strength - size - pollu) + 2) / 3

        if self.traits['diet'] is 'carnivore':
            fitness *= .5
        if self.traits['diet'] is 'omnivore':
            fitness *= .75

        return fitness
                
    def fitness(self, environment):
        if self._fitness == 0:
            self.calculate_fitness(environment)
        return self._fitness

    def mutate(self, genome):
        #for the mutation, pick one random trait on the animal to change
        trait_to_mutate = choice(list(genome))
        if trait_to_mutate in ('speed', 'fat', 'aggression', 'strength', 'size'):
            genome[trait_to_mutate] += random() * .01 - .005
            genome[trait_to_mutate] = max(min(genome[trait_to_mutate], .995), .005)
        else:
            genome[trait_to_mutate] = choice(possible_traits[trait_to_mutate])
            if trait_to_mutate in 'temperature':
                genome[trait_to_mutate][1] += random()*.01 - .005
                genome[trait_to_mutate][1] = max(min(genome[trait_to_mutate][1], .995), .005)

        return genome

    #mutate percent can be adjusted
    def generate_children(self, other, mutate_percent=.005):
        new_genome_1 = {}
        new_genome_2 = {}

        iter = 0
        for key, value in sorted(self.traits.items()):
            #if key in ['speed', 'size', 'strength']:
                #continue

            if iter % 2 == 0:
                new_genome_1[key] = value
            else:
                new_genome_2[key] = value

            iter += 1

        iter = 0
        for key, value in sorted(other.traits.items()):
            #if key in ['speed', 'size', 'strength']:
                #continue

            if iter % 2 == 0:
                new_genome_2[key] = value
            else:
                new_genome_1[key] = value

            iter += 1

        if random() < mutate_percent:
            new_genome_1 = self.mutate(new_genome_1)
        if random() < mutate_percent:
            new_genome_2 = self.mutate(new_genome_2)

        return Animal(new_genome_1), Animal(new_genome_2)


def generate_successors(population, environment, percent=10):
    results = []

    elitist_pops = sorted(population, key=lambda a: a.fitness(environment), reverse=True)[:len(population) // percent]
    results.extend(elitist_pops)

    population_size = len(population)
    num_parent_parings = population_size // 2 - len(elitist_pops) // 2

    min_element = min(population, key=lambda p: p.fitness(environment)).fitness(environment)
    max_element = max(population, key=lambda p: p.fitness(environment)).fitness(environment)
    if min_element == max_element:
        return population
    population_weights = [(p.fitness(environment) - min_element) / (max_element - min_element) for p in population]

    for p in range(num_parent_parings):
        p1, p2 = choices(population, weights=population_weights, k=2)
        while p1 == p2:
            p1, p2 = choices(population, weights=population_weights, k=2)

        results.extend(p1.generate_children(p2))
    return results

def genetic_algorithm(environment):
    #arbitrary number
    pop_limit = 1000

    batches = os.cpu_count()
    batch_size = int(ceil(pop_limit / batches))
    with mpool.Pool(processes=os.cpu_count()) as pool:
        init_time = time()

        adam = Animal()
        with open("animals/first.txt", 'w') as f:
            f.write(str(adam))
            #f.write('\n\n'+ str(environment))
        population = [adam]
        for _ in range(pop_limit - 1):
            population.append(Animal({key: min(max(value + ((random() * .4 - .2)), 0), 1) if key in ('fat', 'speed', 'aggression', 'size', 'strength') else value for key, value in adam.traits.items()}))
        #population = [adam].extend([Animal({key: min(max(value + ((random() * .2 - .1)), 0), 1) if key in ('fat', 'speed', 'aggression', 'size', 'strength') else value for key, value in adam.traits.items()}) for _ in range(pop_limit - 1)])
        #population = [Animal() for _ in range(pop_limit)]
        e = [environment for _ in range(pop_limit)]
        population = pool.starmap(Animal.calculate_fitness, zip(population, e), batch_size)
        init_done = time()
        print("Created and calculated initial population statistics in:", init_done - init_time, "seconds")

        generation = 0
        start = time()
        now = start
        print("Use ctrl-c to terminate this loop manually.")

        try:
            while 1:
                now = time()
                if generation > 0:
                    best = max(population, key=lambda a: a.fitness(environment))
                    print("Generation:", str(generation))
                    print("Max fitness:", str(best.fitness(environment)))
                    print("Average generation time:", (now - start) / generation)
                    print("Net time:", now - start)

                    with open("animals/last.txt", 'w') as f:
                        f.write(str(best))
                        f.write('\n\n'+ str(environment))

                generation += 1
                if generation > 500:
                    break

                gen_time = time()
                next_pop = generate_successors(population, environment)
                gen_done = time()

                print("Generated successors in:", gen_done - gen_time, "seconds")
                next_pop = pool.starmap(Animal.calculate_fitness, zip(next_pop, e), batch_size)
                pop_done = time()
                print("Calculated fitnesses in:", pop_done - gen_done, "seconds")
                population = next_pop
        except KeyboardInterrupt:
            pass
    return population

def main():
    #a = Animal()
    #b = Animal()
    e = Environment()
    #print(str(a) + '\n')
    #print(str(b) + '\n')
    #a.generate_chidren(b)

    genetic_algorithm(e)


    #print(str(e) + '\n')
    #print("Temperature_Fitness:", a.temperature_fitness(e))
    #print("Food_Fitness:", a.food_fitness(e))
    #print("Limb_Fitness:", a.limb_fitness(e))


                         


if __name__ == '__main__':
    main()
