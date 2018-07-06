import sys
sys.path.insert(0, '../')
from planet_wars import issue_order
import logging
from math import sqrt, fabs, inf
from collections import defaultdict

c = 2

def nearest_enemies(state, planet):
    return sorted([enemy_planet for enemy_planet in state.enemy_planets()],
               key=lambda p: state.distance(planet.ID, p.ID))

def nearest_allies(state, planet):
    return sorted([ally_planet for ally_planet in state.my_planets() if ally_planet != planet],
               key=lambda p:state.distance(planet.ID, p.ID))

def surplus(state, planet):
    incoming_fleets = sorted([fleet for fleet in state.enemy_fleets() + state.my_fleets()
                              if fleet.destination_planet == planet.ID], key=lambda f:f.turns_remaining)

    num_ships, last_owner, last_arrival, growth_total = planet.num_ships, 1, 0, 0
    for fleet in incoming_fleets:
        num_ships += fleet.num_ships if fleet in state.my_fleets() else -fleet.num_ships
        if last_owner == 1:
            growth_total += planet.growth_rate * (fleet.turns_remaining - last_arrival)
        elif last_owner == 2:
            growth_total -= planet.growth_rate * (fleet.turns_remaining - last_arrival)
        last_arrival = fleet.turns_remaining
        last_owner = 1 if num_ships > 0 else 2

    return num_ships + growth_total if num_ships + growth_total > 0 else -1

def attack_weakest_enemy_planet(state):
    success = False
    my_planets = sorted(state.my_planets(), key=lambda p: p.num_ships)

    enemy_planets = sorted([planet for planet in state.enemy_planets()
                      if not any(fleet.destination_planet == planet.ID for fleet in state.my_fleets())],
                           key=lambda p:p.num_ships)

    viable_moves = []
    for planet in my_planets:
        l = []
        sur = surplus(state, planet)
        for enemy_planet in enemy_planets:
            enemy_fleets = sorted([fleet for fleet in state.enemy_fleets() if fleet.destination_planet == enemy_planet.ID],
                                  key=lambda f: f.turns_remaining)

            distance = state.distance(planet.ID, enemy_planet.ID)
            
            turns_capped, enemy_ships = 0, enemy_planet.num_ships
            for fleet in enemy_fleets:
                enemy_ships += fleet.num_ships
                if distance < fleet.turns_remaining:
                    turns_capped = fleet.turns_remaining - distance

            required_ships = enemy_ships - (turns_capped * enemy_planet.growth_rate) + (distance * enemy_planet.growth_rate) + 1 \
                             if enemy_fleets \
                             else enemy_ships + (distance * enemy_planet.growth_rate) + 1

            if enemy_ships - (turns_capped * enemy_planet.growth_rate) < 0:
                #in this case, our planet growth after capture is greater than their extra incoming fleets
                required_ships = enemy_planet.num_ships + (distance * enemy_planet.growth_rate) + 1

            l.append((distance, planet, enemy_planet, required_ships, sur))

        viable_moves.append(sorted([att[:-1] for att in l if att[4] >= att[3]]))

    #order all moves into dictionary of lists where key is enemy planet and value is moves to that planet
    d = defaultdict(list)
    for my_planet in viable_moves:
        for move in my_planet:
            d[move[2]].append(move)

    #find the best available move to each enemy planet and execute it
    for enemy_planet, move in d.items():
        distance, my_p, enemy_p, req = sorted(move)[0]
        issue_order(state, my_p.ID, enemy_p.ID, req)
        success = True
    
    return success

#only gets run when there are no valid attack options otherwise (for now)
#currently not working (maybe finish before assignment is done
#------------------------------------------------------------------------
##def group_attack_strong_planet(state):
##    success = False
##    my_planets = [planet for planet in state.my_planets()]
##    enemy_planets = [planet for planet in state.enemy_planets()]
##
##    damage, attacking_force = 0, []
##    for enemy_planet in enemy_planets:
##        my_close_planets = filter(lambda x: state.distance(x.ID, enemy_planet.ID) < 8, my_planets)
##
##        farthest = 0
##        for planet in my_close_planets:
##            sur = surplus(state, planet)
##            if sur >= planet.growth_rate * 5:
##                extra = sur - planet.growth_rate * 5
##                damage += extra
##                attacking_force.append((planet, extra))
##                farthest = max(farthest, state.distance(planet.ID, enemy_planet.ID))
##        
##
##        if damage >= enemy_planet.num_ships + enemy_planet.growth_rate * farthest:
##            for planet, amt in attacking_force:
##                issue_order(state, planet.ID, enemy_planet.ID, amt)
##            success = True
##            
##        return success
        
        

def spread_to_weakest_neutral_planet(state):
    success = False
    my_planets = sorted(state.my_planets(), key = lambda p: p.num_ships, reverse = True)
    neutral_planets = sorted([planet for planet in state.neutral_planets()
                      if not any(fleet.destination_planet == planet.ID for fleet in state.my_fleets())],
                                  key = lambda p: p.num_ships)
    viable_moves = []
    for planet in my_planets:
        l = []
        sur = surplus(state, planet)
        for neutral_planet in neutral_planets:
            enemy_fleets = sorted([fleet for fleet in state.enemy_fleets() if fleet.destination_planet == neutral_planet.ID],
                                  key=lambda f: f.turns_remaining)
            distance = state.distance(planet.ID, neutral_planet.ID)

            turns_capped, neutral_ships = inf, neutral_planet.num_ships
            for fleet in enemy_fleets:
                neutral_ships -= fleet.num_ships
                if neutral_ships < 0:
                    turns_capped = distance - fleet.turns_remaining


            if turns_capped < 1:
                continue                

            required_ships = fabs(neutral_ships) + (turns_capped * neutral_planet.growth_rate) + 1 \
                             if enemy_fleets \
                             else neutral_planet.num_ships + 1

            #arbitrary: don't send more ships to take a neutral planet then my planet's growth rate * 10
            if sur - required_ships < planet.growth_rate * 10:
                continue

            #arbitrary ranking of which planets are best to take
            planet_ratio = c * sqrt(distance) + sqrt(fabs(neutral_ships)) - neutral_planet.growth_rate

            l.append((planet_ratio, planet, neutral_planet, required_ships, sur))

        viable_moves.append(sorted([att[:-1] for att in l]))

    #order all moves into dictionary of lists where key is neutral planet and value is moves to that planet
    d = defaultdict(list)
    for my_planet in viable_moves:
        for move in my_planet:
            d[move[2]].append(move)

    #find the best available move to each enemy planet and execute it
    planets_have_spread = set()
    for neutral_planet, move in d.items():
        ratio, my_p, neutral_p, req = sorted(move)[0]
        if my_p not in planets_have_spread:
            issue_order(state, my_p.ID, neutral_p.ID, req)
            planets_have_spread.add(my_p)
        success = True

    return success

def defend_weakest_ally(state):
    success = False
    my_planets_under_attack = [planet for planet in state.my_planets() if surplus(state, planet) < 0]

    for planet_under_attack in my_planets_under_attack:
        enemy_fleets = sorted([fleet for fleet in state.enemy_fleets() if fleet.destination_planet == planet_under_attack.ID],
                              key=lambda f:f.turns_remaining)

        turns_capped, my_ships, last_arrival = inf, planet_under_attack.num_ships, 0
        for fleet in enemy_fleets:
            my_ships -= (fleet.num_ships - (planet_under_attack.growth_rate * (fleet.turns_remaining - last_arrival)))
            last_arrival = fleet.turns_remaining
            if my_ships < 0 and turns_capped == inf:
                turns_capped = fleet.turns_remaining
        
        #check if I have another planet close enough to assist
        my_other_planets = [planet for planet in state.my_planets() if planet not in my_planets_under_attack]

        for other_planet in my_other_planets:
            if state.distance(other_planet.ID, planet_under_attack.ID) < turns_capped and surplus(state, other_planet) > fabs(my_ships):
                issue_order(state, other_planet.ID, planet_under_attack.ID, fabs(my_ships) + 1)
                success = True
                my_planets_under_attack.remove(planet_under_attack)
                break
            
    return success

#  This doesn't really improve things. Leaving it in to see if it can be improved in the future
#  --------------------------------------------------------------------------------------------
##def reinforce_new_planet(state):
##    success = False
##    neutral_planets_being_taken = sorted([planet for planet in state.neutral_planets() if any(fleet.destination_planet == planet.ID for fleet in state.my_fleets())], key=lambda p:surplus(state, p))
##    
##    for planet in neutral_planets_being_taken:
##        closest_planet = nearest_ally(state, planet)
##        if surplus(state, closest_planet) > closest_planet.growth_rate:
##            issue_order(state, closest_planet.ID, planet.ID, closest_planet.growth_rate)
##            success = True
##
##    return success
