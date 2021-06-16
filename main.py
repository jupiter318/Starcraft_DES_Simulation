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

import pandas as pd
import simpy

######
# initial parameters
## minerals and supply
mineral = 0
initial_scv_number = 4
total_supply = 0

## build_times
scv_build_time = 20
marine_build_time = 24
barracks_build_time = 60
supply_build_time = 40
#######
status_msg = ""
#data_logs = pd.DataFrame(columns=['time',
                      # 'current_mineral', 'mining_scv_number', 'total_scv_number',
                      # 'supply_depot_number', 'supply_count', 'supply_capacity',
                      # 'barracks_number', 'total_marine_number'])
# gantt_chart = pd.DataFrame()

# mining rate from number of SCVs [/s]
def mining_rate(scv_number):
    mining_rate_per_scv_min = [0, 65.0, 65.0, 65.0, 65.0, 65.0, 65.0, 65.0, 65.0, 65.0,  # 0~9
                           62.5, 60.3, 58.65, 57.0, 55.8, 54.6, 53.65, 52.7, 51.0, 51.3]   # 10~19
    if scv_number > len(mining_rate_per_scv_min):
        scv_number = len(mining_rate_per_scv_min)
    return mining_rate_per_scv_min[scv_number]*scv_number/60.0


# current marine number in game
def current_marine_number(barracks_list):
    marine_number = 0
    if len(barracks_list) > 0:
        for barracks in barracks_list:
            marine_number += barracks.marine_number
    return marine_number


# current supply numbers
# need to be added
def population_number(cmd_center):
    marine_number = current_marine_number(cmd_center.barracks_list)
    scv_number = cmd_center.scv_number
    return marine_number + scv_number


class CommandCenter(object):
    def __init__(self, env, mineral_container):
        # command center initialize
        self.env = env
        self.scv_number = initial_scv_number
        self.mining_number = self.scv_number
        self.supply_number = 0
        self.barracks_number = 0
        self.build_slot = simpy.Resource(self.env, capacity=1)
        self.supply_build_slot = simpy.Resource(self.env, capacity=1)
        self.barracks_build_slot = simpy.Resource(self.env, capacity=10)
        self.mineral_container = mineral_container
        self.barracks_list = []

    def build_scv(self):
        global status_msg
        status_msg += f"\tstart {self.scv_number+1}th SCV production ..."
        yield self.env.timeout(scv_build_time)
        status_msg += "\tend SCV production ..."
        self.scv_number += 1
        self.mining_number += 1

    def build_barracks(self):
        global status_msg
        self.mining_number -= 1
        status_msg += f"\tstart {self.barracks_number+1}th Barracks production ..."
        self.barracks_number += 1
        yield self.env.timeout(barracks_build_time)
        status_msg += "\tend Barracks production ..."
        self.barracks_list.append(Barracks(self.env, self.mineral_container, len(self.barracks_list)))
        self.mining_number += 1

    def build_supply(self):
        global status_msg
        self.mining_number -= 1
        status_msg += f"\tstart {self.supply_number+1}th Supply production ..."
        yield self.env.timeout(supply_build_time)
        self.supply_number += 1
        status_msg += f"\tend Supply production ..."
        self.mining_number += 1


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
        yield self.env.timeout(marine_build_time)
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
              f"supply_current\t{population_number(command_center)}\t"
              f"supply_cap\t{command_center.supply_number*8+10}\t"
              f"mining_scv_number\t{command_center.mining_number}\t"
              f"scv_number\t{command_center.scv_number}\t"
              f"barracks_number\t{command_center.barracks_list.__len__()}\t"
              f"total_marine_number\t{current_marine_number(command_center.barracks_list)}\t"
              f"marine_production_number\t{[x.marine_number for x in command_center.barracks_list]}\t"
              f"barracks_end_time\t{[x.end_time for x in command_center.barracks_list]}",
              status_msg)
        status_msg = ""


def supply_check(env, command_center):
    while population_number(command_center) == (command_center.supply_number*8 + 10):
        yield env.timeout(1)


def setup(env, order_string):
    global status_msg, end_production_time
    mineral_container = simpy.Container(env=env, init=50)
    cmd_center = CommandCenter(env=env, mineral_container=mineral_container)
    env.process(mineral_mining(env=env, mineral_container=mineral_container, command_center=cmd_center))

    for next_product in order_string:
        if next_product == 's':     # Add SCV
            yield env.process(supply_check(env, command_center=cmd_center))
            yield mineral_container.get(50)
            yield env.process(build_scv(cmd_center))
        elif next_product == 'b':   # Add Barracks
            yield env.process(supply_check(env, command_center=cmd_center))
            yield mineral_container.get(150)
            yield env.process(build_barracks(cmd_center))
        elif next_product == 'm':   # Add Marine
            while len(cmd_center.barracks_list) == 0:      # wait until first barracks
                yield env.timeout(1)
            yield mineral_container.get(50)
            end_time_list = [x.end_time for x in cmd_center.barracks_list]
            status_msg += f'\torder to {end_time_list.index(min(end_time_list))}'
            yield env.process(build_marine(cmd_center.barracks_list[end_time_list.index(min(end_time_list))]))
            end_time_list = [x.end_time for x in cmd_center.barracks_list]
            end_production_time = max(end_time_list)
        elif next_product == 'u':   # Add Supply Depot
            yield mineral_container.get(100)
            yield env.process(build_supply(cmd_center))
    print(order_string, f"\t{end_production_time}")


end_production_time = 800

i = "ssssbbsummmmmmmm"
env = simpy.Environment()
env.process(setup(env, i))
env.run(until=1.5*end_production_time)
