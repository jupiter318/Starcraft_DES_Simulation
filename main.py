# Input: 문자열
#   생산 순서에 따라 Ex) SSSBSMMMBMMMMM
#   units
#   S: SCV      20
#   M: Marine   24
#
#   buildings
#   C: Command Center   120
#   U: Supply Depot     40
#   B: Barracks         80
#
# 시간 단위는 Normal Gamespeed 기준에서 second 단위.
# Fastest 는 30% 빠름


import simpy
import pandas as pd

######
# initial parameters
## minerals and supply
mineral = 0
initial_scv_number = 3
total_supply = 0

## build_times
scv_build_time = 20
marine_build_time = 24
barracks_build_time = 60
supply_build_time = 40
#######
status_msg = ""

# mining rate from number of SCVs [/s]
def mining_rate(scv_number):
    mining_rate_ = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    if scv_number > mining_rate_.__len__():
        scv_number = mining_rate_.__len__()
    return mining_rate_[scv_number]


# current marine number in game
def current_marine_number(barracks_list):
    marine_number = 0
    for barracks in barracks_list:
        marine_number += barracks.marine_number
    return marine_number


# current supply numberss
# need to be added
def population_number(cmd_center):
    marine_number = current_marine_number(cmd_center)
    return


class CommandCenter(object):
    def __init__(self, env, mineral_container):
        # command center initialize
        self.env = env
        self.scv_number = initial_scv_number
        self.supply_number = 0
        self.barracks_number = 0
        self.build_slot = simpy.Resource(self.env, capacity=1)
        self.barracks_build_slot = simpy.Resource(self.env, capacity=10)
        self.mineral_container = mineral_container
        self.barracks_list = []

    def build_scv(self):
        global status_msg
        status_msg += f"\tstart {self.scv_number+1}th SCV production ..."
        yield self.env.timeout(scv_build_time)
        status_msg += "\tend SCV production ..."
        self.scv_number += 1

    def build_barracks(self):
        global status_msg
        self.scv_number -= 1
        status_msg += f"\tstart {self.barracks_number+1}th Barracks production ..."
        self.barracks_number += 1
        yield self.env.timeout(barracks_build_time)
        status_msg += "\tend Barracks production ..."
        self.barracks_list.append(Barracks(self.env, self.mineral_container, len(self.barracks_list)))
        self.scv_number += 1

    def build_supply(self):
        global status_msg
        self.scv_number -= 1
        status_msg += f"\tstart {self.supply_number+1}th Supply production ..."
        yield self.env.timeout(supply_build_time)
        self.supply_number += 1
        status_msg += f"\tend Supply production ..."
        self.scv_number += 1


class Barracks(object):
    def __init__(self, env, mineral_container, number):
        self.env = env
        self.build_slot = simpy.Resource(self.env, capacity=1)
        self.mineral_container = mineral_container
        self.marine_number = 0
        self.end_time = env.now
        self.barracks_number = number

    def build_marine(self):
        global status_msg
        self.end_time = (env.now + marine_build_time) if (env.now > self.end_time) else (self.end_time + marine_build_time)
        status_msg += f'\tstart marine {self.barracks_number}, {self.marine_number}'
        yield self.env.timeout(scv_build_time)
        self.marine_number += 1
        status_msg += f'\tend marine {self.barracks_number}, {self.marine_number}'


def build_scv(cmd_center):
    with cmd_center.build_slot.request() as req:
        yield req
        yield env.process(cmd_center.build_scv())


def build_barracks(cmd_center):
    with cmd_center.barracks_build_slot.request() as req:
        yield req
        yield env.process(cmd_center.build_barracks())


def build_marine(barracks):
    with barracks.build_slot.request() as req:
        yield req
        yield env.process(barracks.build_marine())


def build_supply(cmd_center):
    with cmd_center.barracks_build_slot.request() as req:
        yield req
        yield env.process(cmd_center.build_supply())


def mineral_mining(env, mineral_container, command_center):
    global status_msg
    while True:
        yield env.timeout(1)
        yield mineral_container.put(mining_rate(command_center.scv_number))
        print(f"{env.now}:\t"
              f"current mineral\t{mineral_container.level}\t"
              f"scv_number\t{command_center.scv_number}\t"
              f"barracks_number\t{command_center.barracks_list.__len__()}\t"
              f"total_marine_number\t{current_marine_number(command_center.barracks_list)}\t"
              f"marine_production_number\t{[x.marine_number for x in command_center.barracks_list]}\t"
              f"barracks_end_time\t{[x.end_time for x in command_center.barracks_list]}",
              status_msg)
        status_msg = ""


def setup(env, input_string):
    global status_msg
    mineral_container = simpy.Container(env=env, init=50)
    cmd_center = CommandCenter(env=env, mineral_container=mineral_container)
    env.process(mineral_mining(env=env, mineral_container=mineral_container, command_center=cmd_center))
    
    for next_product in input_string:
        if next_product == 'S': # Add SCV
            yield mineral_container.get(50)
            env.process(build_scv(cmd_center))
        elif next_product == 'B':   # Add Barracks
            yield mineral_container.get(150)
            env.process(build_barracks(cmd_center))
        elif next_product == 'M':   # Add Marine
            while cmd_center.barracks_list.__len__() == 0:      # wait until first barracks
                yield env.timeout(1)
            yield mineral_container.get(50)
            end_time_list = [x.end_time for x in cmd_center.barracks_list]
            status_msg += f'\torder to {end_time_list.index(min(end_time_list))}'
            env.process(build_marine(cmd_center.barracks_list[end_time_list.index(min(end_time_list))]))
            # end_time이 가장 작은 배럭에 주문 추가
        # elif next_product == 'U': # Add Supply Depot
        #     yield mineral_container.get(100)
        #     env.process(build_supply(cmd_center))


SIM_TIME = 600
env = simpy.Environment()
input_string = "SSBMMMBBMMMMBBMMMMMMMMMMM"
env.process(setup(env, input_string))
env.run(until=SIM_TIME)



# order = pd.read_csv('project.CSV')

# print(order)
#
# for i in order:
#     env = simpy.Environment()
#     print(i)
#     env.process(setup(env, i))
#     env.run(until=SIM_TIME)
