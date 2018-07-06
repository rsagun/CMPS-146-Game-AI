#!/usr/bin/env python

"""
// There is already a basic strategy in place here. You can use it as a
// starting point, or you can throw it out entirely and replace it with your
// own.
"""
import logging, traceback, sys, os, inspect
logging.basicConfig(filename=__file__[:-3] +'.log', filemode='w', level=logging.DEBUG)
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from behavior_tree_bot.behaviors import *
from behavior_tree_bot.checks import *
from behavior_tree_bot.bt_nodes import Selector, Sequence, Action, Check, Inverter, Succeeder

from planet_wars import PlanetWars, finish_turn

# You have to improve this tree or create an entire new one that is capable
# of winning against all the 5 opponent bots
def setup_behavior_tree():

    # Top-down construction of behavior tree
    root = Selector(name='High Level Ordering of Strategies')

    #attack plan
    invert_att = Inverter()
    succeed_att = Succeeder()
    offensive_plan = Sequence(name='Offensive Strategy')
    enough_planets_check = Check(has_enough_planets)
    attack = Action(attack_weakest_enemy_planet)
    invert_att.child_node = succeed_att
    succeed_att.child_node = offensive_plan
    offensive_plan.child_nodes = [enough_planets_check, attack]

    #defense plan
    invert_def = Inverter()
    succeed_def = Succeeder()
    defense = Action(defend_weakest_ally)
    succeed_def.child_node = defense
    invert_def.child_node = succeed_def

    #reinforce plan
    #invert_reinforce = Inverter()
    #succeed_reinforce = Succeeder()
    #reinforce = Action(reinforce_new_planet)
    #succeed_reinforce.child_node = reinforce
    #invert_reinforce.child_node = succeed_reinforce

    #spread plan
    spread_sequence = Sequence(name='Spread Strategy')
    neutral_planet_check = Check(if_neutral_planet_available)
    spread_action = Action(spread_to_weakest_neutral_planet)
    spread_sequence.child_nodes = [neutral_planet_check, spread_action]

    root.child_nodes = [invert_att, invert_def, spread_sequence, attack.copy()]

    logging.info('\n' + root.tree_to_string())
    return root

# You don't need to change this function
def do_turn(state):
    behavior_tree.execute(planet_wars)

if __name__ == '__main__':
    logging.basicConfig(filename=__file__[:-3] + '.log', filemode='w', level=logging.DEBUG)

    behavior_tree = setup_behavior_tree()
    try:
        map_data = ''
        while True:
            current_line = input()
            if len(current_line) >= 2 and current_line.startswith("go"):
                planet_wars = PlanetWars(map_data)
                do_turn(planet_wars)
                finish_turn()
                map_data = ''
            else:
                map_data += current_line + '\n'

    except KeyboardInterrupt:
        print('ctrl-c, leaving ...')
    except Exception:
        traceback.print_exc(file=sys.stdout)
        logging.exception("Error in bot.")
