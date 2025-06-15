from __future__ import annotations

from dataclasses import dataclass
import itertools
import math
import simpy

from .buildings import CommandCenter, Barracks, SupplyDepot


SIM_TIME = 10 * 30


def mining_rate(scv_number: int) -> float:
    rates = [0, 65.0, 65.0, 65.0, 65.0, 65.0, 65.0, 65.0, 65.0, 65.0,
             62.5, 60.3, 58.65, 57.0, 55.8, 54.6, 53.65, 52.7, 51.0, 51.3]
    scv_number = min(scv_number, len(rates) - 1)
    return rates[scv_number] * scv_number / 60.0


def mine_mineral(env: simpy.Environment, mineral: simpy.Container,
                 command_center: CommandCenter, buildings: list[object]):
    while True:
        yield env.timeout(1)
        yield mineral.put(mining_rate(command_center.unit_number))


def build_unit(env: simpy.Environment, building: object):
    with building.build_slot.request() as req:
        yield req
        yield env.process(building.build_unit())


def build_building(env: simpy.Environment, building: object,
                   buildings: list[object], command_center: CommandCenter,
                   barracks_store: simpy.Store):
    command_center.mining_number -= 1
    yield env.timeout(building.build_time)
    building.building_no = len(buildings)
    buildings.append(building)
    if getattr(building, 'building_type', '') == 'b':
        barracks_store.put(len(buildings) - 1)
    command_center.mining_number += 1


@dataclass
class SimulationResult:
    end_time: float = float('inf')


def setup(env: simpy.Environment, order: str, result: SimulationResult) -> None:
    buildings: list[object] = []
    mineral = simpy.Container(env=env, init=50)
    supply = simpy.Container(env=env, init=6)
    barracks_store = simpy.Store(env=env)
    cc = CommandCenter(env, mineral, supply)
    buildings.append(cc)
    env.process(mine_mineral(env, mineral, cc, buildings))

    for next_product in order:
        if next_product == 's':
            yield mineral.get(50)
            yield supply.get(1)
            env.process(build_unit(env, cc))
        elif next_product == 'b':
            yield mineral.get(150)
            env.process(build_building(env, Barracks(env, mineral, supply, barracks_store),
                                       buildings, cc, barracks_store))
        elif next_product == 'm':
            while len(buildings) == 1:
                yield env.timeout(1)
            yield mineral.get(50)
            yield supply.get(1)
            building_no = yield barracks_store.get()
            env.process(build_unit(env, buildings[building_no]))
            b = buildings[building_no]
            result.end_time = b.end_time + b.unit_build_time
        elif next_product == 'u':
            yield mineral.get(100)
            env.process(build_building(env, SupplyDepot(env, mineral), buildings,
                                       cc, barracks_store))
            supply.put(8)
    return None


def simulate_order(order: str, sim_time: int = SIM_TIME) -> float:
    env = simpy.Environment()
    result = SimulationResult()
    env.process(setup(env, order, result))
    env.run(until=sim_time)
    return result.end_time


def find_best_order(target_marines: int) -> tuple[str, float]:
    required_supply = 4 + target_marines
    depot_count = 0 if required_supply <= 6 else math.ceil((required_supply - 6) / 8)
    base_items = ['b'] + ['u'] * depot_count + ['m'] * target_marines

    best_time = float('inf')
    best_order = ''

    for perm in set(itertools.permutations(base_items)):
        order = ''.join(perm)
        completion = simulate_order(order)
        if completion < best_time:
            best_time = completion
            best_order = order
    if best_order:
        print(f"Best order: {best_order} {best_time}")
    return best_order, best_time
