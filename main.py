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
import itertools
import math
class CommandCenter(object):
    def __init__(self, env, mineral_container, supply_container):
        self.building_no = 0
        self.building_type = 'c'
        self.unit_build_time = 22
        self.unit_number = 4
        self.env = env
        self.price = 400
        self.mineral_container = mineral_container
        self.supply_container = supply_container
        self.end_time = float('inf')
        self.build_slot = simpy.Resource(self.env, capacity=1)

        self.mining_number = self.unit_number

    def build_unit(self):
        yield self.env.timeout(self.unit_build_time)
        self.end_time = self.env.now
        self.unit_number += 1
        self.mining_number += 1


class Barracks(object):
    def __init__(self, env, mineral_container, supply_container, barracks_store):
        self.building_no = -1
        self.build_time = 60
        self.unit_build_time = 24
        self.building_type = 'b'
        self.env = env
        self.price = 150
        self.mineral_container = mineral_container
        self.supply_container = supply_container
        self.barracks_store = barracks_store
        self.end_time = env.now
        self.build_slot = simpy.Resource(self.env, capacity=1)

        self.unit_number = 0

    def build_unit(self):
        yield self.env.timeout(self.unit_build_time)
        self.end_time = self.env.now
        self.barracks_store.put(self.building_no)
        self.unit_number += 1


class SupplyDepot(object):
    def __init__(self, env, mineral_container):
        self.building_no = -1
        self.env = env
        self.building_type = 'u'
        self.price = 100
        self.build_time = 40
        self.mineral_container = mineral_container
        self.end_time = float('inf')
        self.unit_number = 0
        self.build_slot = simpy.Resource(self.env, capacity=1)

#data_logs = pd.DataFrame(columns=['time',
                      # 'current_mineral', 'mining_scv_number', 'total_scv_number',
                      # 'supply_depot_number', 'supply_count', 'supply_capacity',
                      # 'barracks_number', 'total_marine_number'])
# gantt_chart = pd.DataFrame()

def mining_rate(scv_number):
    mining_rate_per_scv_min = [0, 65.0, 65.0, 65.0, 65.0, 65.0, 65.0, 65.0, 65.0, 65.0,  # 0~9
                           62.5, 60.3, 58.65, 57.0, 55.8, 54.6, 53.65, 52.7, 51.0, 51.3]   # 10~19
    if scv_number > len(mining_rate_per_scv_min):
        scv_number = len(mining_rate_per_scv_min)
    return mining_rate_per_scv_min[scv_number]*scv_number/60.0


def mine_mineral(env, mineral_container, command_center, building_list):
    while True:
        yield env.timeout(1)
        yield mineral_container.put(mining_rate(command_center.unit_number))
        # print(f"{env.now}\t"
        #       f"\t{mineral_container.level}\t"
        #       f"\t{command_center.supply_container.level}\t"
        #       f"\t{[x.unit_number for x in building_list]}\t"
        #       f"mining_scv_number\t{command_center.mining_number}\t"
        #       f"scv_number\t{command_center.unit_number}\t"
        #       f"production_slot\t{[x.build_slot.count for x in building_list]}\t"
        #       )


def build_unit(env, building):
    with building.build_slot.request() as req:
        yield req
        yield env.process(building.build_unit())


def build_building(env: simpy.Environment, building, building_list: list, command_center: CommandCenter, barracks_store):
    command_center.mining_number -= 1
    yield env.timeout(building.build_time)
    building.building_no = len(building_list)
    building_list.append(building)
    if building.building_type == 'b':
        barracks_store.put(len(building_list)-1)
    command_center.mining_number += 1


def setup(env, order_string):
    global csv_output, end_production_time
    building_list = []
    mineral_container = simpy.Container(env=env, init=50)
    supply_container = simpy.Container(env=env, init=6)
    barracks_store = simpy.Store(env=env)
    building_list.append(CommandCenter(env, mineral_container, supply_container))
    env.process(mine_mineral(env=env, mineral_container=mineral_container, command_center=building_list[0],
                             building_list=building_list))

    for next_product in order_string:
        if next_product == 's':     # Add SCV
            yield mineral_container.get(50)
            yield supply_container.get(1)
            env.process(build_unit(env, building_list[0]))

        elif next_product == 'b':   # Add Barracks
            yield mineral_container.get(150)
            env.process(build_building(env, Barracks(env, mineral_container, supply_container, barracks_store), building_list,
                                             building_list[0], barracks_store))
        elif next_product == 'm':   # Add Marine
            while len(building_list) == 1:      # wait until first barracks
                yield env.timeout(1)
            yield mineral_container.get(50)
            yield supply_container.get(1)
            building_no = yield barracks_store.get()
            env.process(build_unit(env, building_list[building_no]))
            end_production_time = building_list[building_no].end_time + building_list[building_no].unit_build_time
        elif next_product == 'u':   # Add Supply Depot
            yield mineral_container.get(100)
            env.process(
                build_building(env, SupplyDepot(env=env, mineral_container=mineral_container), building_list,
                               building_list[0], barracks_store))
            supply_container.put(8)
    # csv_output = csv_output.append({'order': order_string, 'end_time': end_production_time}, ignore_index=True)
    # print(order_string, f"\t{end_production_time}")


def find_best_order(target_marines):
    """Search build orders to produce the target number of marines."""
    required_supply = 4 + target_marines
    depot_count = 0 if required_supply <= 6 else math.ceil((required_supply - 6) / 8)
    base_items = ['b'] + ['u'] * depot_count + ['m'] * target_marines

    best_time = float('inf')
    best_order = ''

    for perm in set(itertools.permutations(base_items)):
        order = ''.join(perm)
        global end_production_time
        end_production_time = float('inf')
        env = simpy.Environment()
        env.process(setup(env, order))
        env.run(until=SIM_TIME)
        if end_production_time < best_time:
            best_time = end_production_time
            best_order = order

    print(f"Best order: {best_order} {best_time}")
    return best_order, best_time


# #
SIM_TIME = 10 * 30

end_production_time = 800

if __name__ == "__main__":
    find_best_order(6)

#
#
# marine_no = 8
# for barracks_no in range(1, 5):
#     for scv_no in range(6-barracks_no):
#         supply_no = 1
#         orders = pd.read_csv(f'./input/m{marine_no}b{barracks_no}s{scv_no}u{supply_no}.txt')
#         order_no = 0
#         total_order = len(orders['order'])
#         csv_output = pd.DataFrame(columns=["order", "end_time"])
#         for i in orders['order']:
#             env = simpy.Environment()
#             env.process(setup(env, i))
#             env.run(until=SIM_TIME)
#             print(f"\t{order_no}/{total_order}\t", barracks_no, scv_no)
#             order_no += 1
#         csv_output.to_csv(rf'./output2/m{marine_no}b{barracks_no}s{scv_no}u{supply_no}.csv', index=False)
#
#
# print(csv_output)

