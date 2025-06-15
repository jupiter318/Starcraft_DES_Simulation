from __future__ import annotations

from dataclasses import dataclass, field
import simpy


@dataclass
class CommandCenter:
    env: simpy.Environment
    mineral_container: simpy.Container
    supply_container: simpy.Container
    building_no: int = 0
    building_type: str = 'c'
    unit_build_time: int = 22
    unit_number: int = 4
    price: int = 400
    end_time: float = float('inf')
    build_slot: simpy.Resource = field(init=False)
    mining_number: int = field(init=False)

    def __post_init__(self) -> None:
        self.build_slot = simpy.Resource(self.env, capacity=1)
        self.mining_number = self.unit_number

    def build_unit(self) -> simpy.events.Event:
        yield self.env.timeout(self.unit_build_time)
        self.end_time = self.env.now
        self.unit_number += 1
        self.mining_number += 1


@dataclass
class Barracks:
    env: simpy.Environment
    mineral_container: simpy.Container
    supply_container: simpy.Container
    barracks_store: simpy.Store
    building_no: int = -1
    build_time: int = 60
    unit_build_time: int = 24
    building_type: str = 'b'
    price: int = 150
    end_time: float = 0
    build_slot: simpy.Resource = field(init=False)
    unit_number: int = 0

    def __post_init__(self) -> None:
        self.build_slot = simpy.Resource(self.env, capacity=1)

    def build_unit(self) -> simpy.events.Event:
        yield self.env.timeout(self.unit_build_time)
        self.end_time = self.env.now
        self.barracks_store.put(self.building_no)
        self.unit_number += 1


@dataclass
class SupplyDepot:
    env: simpy.Environment
    mineral_container: simpy.Container
    building_no: int = -1
    building_type: str = 'u'
    price: int = 100
    build_time: int = 40
    end_time: float = float('inf')
    unit_number: int = 0
    build_slot: simpy.Resource = field(init=False)

    def __post_init__(self) -> None:
        self.build_slot = simpy.Resource(self.env, capacity=1)
