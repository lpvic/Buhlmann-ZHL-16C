import math
import json
from pathlib import Path
import numpy as np


h_n2 = np.array([5.0, 8.0, 12.5, 18.5, 27.0, 38.3, 54.3, 77.0, 109.0, 146.0, 187.0, 239.0, 305.0, 390.0, 498.0,
                 635.0])
a_n2 = np.array([1.1696, 1.0000, 0.8618, 0.7562, 0.6200, 0.5043, 0.4410, 0.4000, 0.3750, 0.3500, 0.3295, 0.3065,
                 0.2835, 0.2610, 0.2480, 0.2327])
b_n2 = np.array([0.5578, 0.6514, 0.7222, 0.7825, 0.8126, 0.8434, 0.8693, 0.8910, 0.9092, 0.9222, 0.9319, 0.9403,
                 0.9477, 0.9544, 0.9602, 0.9653])
h_he = np.array([1.88, 3.02, 4.72, 6.99, 10.21, 14.48, 20.53, 29.11, 41.20, 55.19, 70.69, 90.34, 115.29, 147.42,
                 188.24, 240.03])
a_he = np.array([1.6189, 1.3830, 1.1919, 1.0458, 0.9220, 0.8205, 0.7305, 0.6502, 0.5950, 0.5545, 0.5333, 0.5189,
                 0.5181, 0.5176, 0.5172, 0.5119])
b_he = np.array([0.4770, 0.5747, 0.6527, 0.7223, 0.7582, 0.7957, 0.8279, 0.8553, 0.8757, 0.8903, 0.8997, 0.9073,
                 0.9122, 0.9171, 0.9217, 0.9267])


class IncorrectGasMixture(Exception):
    pass


class Setup:
    def __init__(self) -> None:
        self.last_stop_depth = 6
        self.stop_depth_incr = 3

        self.v_asc = 9
        self.v_desc = 20

        self.own_descent_sac = 20
        self.own_bottom_sac = 17
        self.own_ascent_sac = 22
        self.buddy_ascent_sac = 22

    def to_json(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def from_json(self, json_str: str | Path) -> None:
        self.__dict__ = json.loads(json_str)


class Gas:
    def __init__(self, o2: int = 21, he: int = 0) -> None:
        self._O2 = o2
        self._He = he
        self._N2 = 100 - o2 - he

    def ppO2(self, depth: float) -> float:
        pabs = (depth / 10) + 1
        return pabs * self._O2 / 100

    def ppN2(self, depth: float) -> float:
        pabs = (depth / 10) + 1
        return pabs * self._N2 / 100

    def ppHe(self, depth: float) -> float:
        pabs = (depth / 10) + 1
        return pabs * self._He / 100

    @property
    def O2(self) -> int:
        return self._O2

    @O2.setter
    def O2(self, v: int) -> None:
        self._O2 = v
        self._N2 = 100 - self._O2 - self._He

    @property
    def He(self) -> int:
        return self._He

    @He.setter
    def He(self, v: int):
        self._He = v
        self._N2 = 100 - self._O2 - self._He

    @property
    def N2(self) -> int:
        return self._N2

    def __str__(self) -> str:
        if (self._O2 == 21) and (self._He == 0):
            return 'Air'
        elif self._He == 0:
            return 'EAN{}'.format(self._O2)
        else:
            return 'Trimix{}/{}'.format(self._O2, self._He)

    def __repr__(self) -> str:
        return '<Gas Mixture: O2: {} N2: {} He: {}>'.format(self._O2, self._N2, self._He)


class Tank:
    def __init__(self, p_start: int = 200, gas: Gas = Gas(), size: int = 15):
        self._gas = gas
        self.pressure = [p_start]
        self._size = size

    @property
    def gas(self):
        return self._gas

    @property
    def size(self):
        return self._size


class Waypoint:
    def __init__(self, depth: float, time: int, tank: int) -> None:
        self._depth = depth
        self._time = time
        self._tank = tank
        self.compartments = np.zeros(16)
        self.runtime = 0

    @property
    def ata_depth(self):
        return (self._depth / 10) + 1

    @property
    def depth(self):
        return self._depth

    @property
    def time(self):
        return self._time

    @property
    def tank(self):
        return self._tank


class Profile:
    def __init__(self, setup: Setup, tanks: list[Tank], waypoints: list[Waypoint]) -> None:
        self._setup = setup
        self._tanks = tanks
        self._waypoints = waypoints

        self._complete_profile()
        self._calculate_profile()

    def add_waypoint(self, segment):
        pass

    def _complete_profile(self):
        if self._waypoints[0].depth != 0:
            time_to_bottom = math.ceil(self._waypoints[0].depth / self._setup.v_desc)
            self._waypoints.insert(0, Waypoint(depth=0, time=time_to_bottom,
                                               tank=self._waypoints[0].tank))
        if self._waypoints[-1].depth != 0:
            self._waypoints.append(Waypoint(depth=5, time=3, tank=self._tanks.index(self._tanks[-1])))
            time_to_surface = math.ceil(self._waypoints[-1].depth / self._setup.v_asc)
            self._waypoints.append(Waypoint(depth=5, time=time_to_surface,
                                            tank=self._tanks.index(self._tanks[-1])))
            time_to_surface = math.ceil(self._waypoints[-1].depth / self._setup.v_asc)
            self._waypoints.append(Waypoint(depth=0, time=0,
                                            tank=self._tanks.index(self._tanks[-1])))

    def _calculate_profile(self):
        self._waypoints[0].compartments = np.full(16, 0.79 * (1 - 0.0567))

        for wp in range(1, len(self._waypoints)):
            self._waypoints[wp].runtime = self._waypoints[wp-1].runtime + self._waypoints[wp-1].time
            self._calculate_gas(wp)

    def _calculate_gas(self, wp):
        cons = (self._waypoints[wp - 1].ata_depth + self._waypoints[wp].ata_depth) / 2
        cons = cons * self._waypoints[wp - 1].time
        start_press = self._tanks[self._waypoints[wp - 1].tank].pressure[wp - 1]
        end_press = (start_press -
                     (cons * self._setup.own_bottom_sac / self._tanks[self._waypoints[wp - 1].tank].size))
        self._tanks[self._waypoints[wp - 1].tank].pressure.append(math.floor(end_press))

        for cyl in range(len(self._tanks)):
            if cyl != self._waypoints[wp - 1].tank:
                self._tanks[cyl].pressure.append(self._tanks[cyl].pressure[wp - 1])

    @property
    def waypoints(self):
        return dict(enumerate(self._waypoints))

    @property
    def tanks(self):
        return dict(enumerate(self._tanks))
