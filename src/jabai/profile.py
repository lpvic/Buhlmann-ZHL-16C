import json
import math
from math import log, ceil
from pathlib import Path
from copy import deepcopy

import numpy as np

h_n2 = np.array([5.0, 8.0, 12.5, 18.5, 27.0, 38.3, 54.3, 77.0, 109.0, 146.0, 187.0, 239.0, 305.0, 390.0, 498.0, 635.0])
a_n2 = np.array([1.1696, 1.0000, 0.8618, 0.7562, 0.6200, 0.5043, 0.4410, 0.4000, 0.3750, 0.3500, 0.3295, 0.3065, 0.2835,
                 0.2610, 0.2480, 0.2327])
b_n2 = np.array([0.5578, 0.6514, 0.7222, 0.7825, 0.8126, 0.8434, 0.8693, 0.8910, 0.9092, 0.9222, 0.9319, 0.9403, 0.9477,
                 0.9544, 0.9602, 0.9653])
h_he = np.array([1.88, 3.02, 4.72, 6.99, 10.21, 14.48, 20.53, 29.11, 41.20, 55.19, 70.69, 90.34, 115.29, 147.42, 188.24,
                 240.03])
a_he = np.array([1.6189, 1.3830, 1.1919, 1.0458, 0.9220, 0.8205, 0.7305, 0.6502, 0.5950, 0.5545, 0.5333, 0.5189, 0.5181,
                 0.5176, 0.5172, 0.5119])
b_he = np.array([0.4770, 0.5747, 0.6527, 0.7223, 0.7582, 0.7957, 0.8279, 0.8553, 0.8757, 0.8903, 0.8997, 0.9073, 0.9122,
                 0.9171, 0.9217, 0.9267])
pw = 0.0567


def schreiner_equation(pi: float | np.ndarray, p0: float | np.ndarray, r: float, t: float, k: float | np.ndarray)\
        -> float:
    out = pi
    out = out + r * (t - (1 / k))
    out = out - (pi - p0 - (r / k)) * np.exp(-k * t)

    return out


class IncorrectGasMixture(Exception):
    pass


class Parameters:
    def __init__(self) -> None:
        self.last_stop_depth = 6
        self.stop_depth_incr = 3

        self.v_asc = 9
        self.v_desc = 20

        self.own_descent_sac = 20
        self.own_bottom_sac = 20
        self.own_ascent_sac = 17
        self.buddy_ascent_sac = 17

        self.gf_high = 1.
        self.gf_low = 1.

        self.calc_ascent = True
        self.deco_stops = True
        self.safety_stop = True

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

    def mod(self, pp_o2=1.4):
        return 10 * ((pp_o2 / (self._O2 / 100)) - 1)

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
    def __init__(self, depth: float, time: int = -1, tank: int = 0) -> None:
        self._depth = depth
        self._tank = tank
        self.time = time
        self.runtime = 0
        self.load_n2 = np.zeros(16)
        self.load_he = np.zeros(16)
        self.ceilings = np.ones(16)

    @property
    def ata_depth(self):
        return (self._depth / 10) + 1

    @property
    def depth(self):
        return self._depth

    @property
    def tank(self):
        return self._tank

    @property
    def ceiling(self):
        if np.max(self.ceilings) > 1.:
            return (np.max(self.ceilings) - 1) * 10
        else:
            return 0.

    def __str__(self):
        return ' '.join([str(self.depth), str(self.runtime), str(self.time), str(self.tank), str(self.ceiling)])


class Profile:
    def __init__(self, params: Parameters, tanks: list[Tank], waypoints: list[Waypoint]) -> None:
        self._params = params
        self._tanks = tanks
        self._waypoints = waypoints
        self._max_depth_ata = 0.
        self._depth = []
        self._ceiling = []
        self._runtime = []

        for wp in self._waypoints:
            if wp.ata_depth > self._max_depth_ata:
                self._max_depth_ata = wp.ata_depth

        self._calculate_profile()

        for wp in self._waypoints:
            self._depth.append(wp.depth)
            self._ceiling.append(wp.ceiling)
            self._runtime.append(wp.runtime)

    def _calculate_waypoint(self, wp):
        self._waypoints[wp].runtime = self._waypoints[wp - 1].runtime + self._waypoints[wp - 1].time
        self._calculate_gas(wp)
        self._waypoints[wp].load_n2, self._waypoints[wp].load_he = self._calculate_compartments(wp)
        self._waypoints[wp].ceilings = self._calculate_ceilings(wp)

    def _calculate_profile(self):
        if self._waypoints[0].depth != 0:
            time_to_bottom = ceil(self._waypoints[0].depth / self._params.v_desc)
            self._waypoints.insert(0, Waypoint(depth=0, time=time_to_bottom, tank=self._waypoints[0].tank))
        self._waypoints[0].load_n2 = np.full(16, 0.79 * (1 - pw))
        self._waypoints[0].runtime = 0

        for wp in range(1, len(self._waypoints)):
            self._calculate_waypoint(wp)

        if self._waypoints[-1].depth > 0:
            if self._waypoints[-1].ceiling <= 0:
                if self._params.safety_stop:
                    self._add_safety_stop()
                else:
                    self._add_direct_ascent()
            else:
                while self._waypoints[-1].ceiling > 0:
                    stop_depth = (math.ceil(self._waypoints[-1].ceiling / self._params.stop_depth_incr) *
                                  self._params.stop_depth_incr)
                    tank = self._select_gas(stop_depth)
                    time_to_stop = ceil((self._waypoints[-1].depth - stop_depth) / self._params.v_asc)
                    self._waypoints[-1].time = time_to_stop
                    self._waypoints.append(Waypoint(depth=stop_depth, time=1, tank=tank))
                    self._calculate_waypoint(len(self._waypoints) - 1)

                    tank = self._select_gas(stop_depth)
                    time_to_stop = ceil(3 / self._params.v_asc)
                    self._waypoints.append(Waypoint(depth=stop_depth, time=time_to_stop, tank=tank))
                    self._calculate_waypoint(len(self._waypoints) - 1)

                    while self._waypoints[-1].ceiling > (stop_depth - self._params.stop_depth_incr):
                        self._waypoints[-2].time = self._waypoints[-2].time + 1
                        self._calculate_waypoint(len(self._waypoints) - 2)
                        self._calculate_waypoint(len(self._waypoints) - 1)

                tank = self._select_gas(0)
                time_to_surface = ceil(self._waypoints[-1].depth / self._params.v_asc)
                self._waypoints[-1].time = time_to_surface
                self._waypoints.append(Waypoint(depth=0, time=0, tank=tank))
                self._calculate_waypoint(len(self._waypoints) - 1)

    def _calculate_gas(self, wp: int):
        cons = (self._waypoints[wp - 1].ata_depth + self._waypoints[wp].ata_depth) / 2
        cons = cons * self._waypoints[wp - 1].time
        start_press = self._tanks[self._waypoints[wp - 1].tank].pressure[wp - 1]
        end_press = (start_press - (cons * self._params.own_bottom_sac /
                                    self._tanks[self._waypoints[wp - 1].tank].size))
        if (len(self._tanks[self._waypoints[wp - 1].tank].pressure) - 1) <= wp:
            self._tanks[self._waypoints[wp - 1].tank].pressure.append(math.floor(end_press))
        else:
            self._tanks[self._waypoints[wp - 1].tank].pressure[wp] = math.floor(end_press)

        for cyl in range(len(self._tanks)):
            if cyl != self._waypoints[wp - 1].tank:
                if (len(self._tanks[cyl].pressure) - 1) <= wp:
                    self._tanks[cyl].pressure.append(self._tanks[cyl].pressure[wp - 1])
                else:
                    self._tanks[cyl].pressure[wp] = self._tanks[cyl].pressure[wp - 1]

    def _calculate_compartments(self, wp: int):
        depth_ata = (self._waypoints[wp].depth / 10) + 1

        # Nitrogen first
        p0 = self._waypoints[wp - 1].load_n2
        f_n2 = self._tanks[self._waypoints[wp - 1].tank].gas.N2 / 100
        pi_n2 = np.full(16, f_n2 * (depth_ata - pw))
        r_n2 = ((((self._waypoints[wp].depth - self._waypoints[wp - 1].depth) / self._waypoints[wp - 1].time) * f_n2)
                / 10)
        k_n2 = log(2) / h_n2
        load_n2 = schreiner_equation(pi_n2, p0, r_n2, self._waypoints[wp - 1].time, k_n2)

        # Helium next
        p0 = self._waypoints[wp - 1].load_he
        f_he = self._tanks[self._waypoints[wp - 1].tank].gas.He / 100
        pi_he = np.full(16, f_he * (depth_ata - pw))
        r_he = ((((self._waypoints[wp].depth - self._waypoints[wp - 1].depth) / self._waypoints[wp - 1].time) * f_he)
                / 10)
        k_he = log(2) / h_he
        load_he = schreiner_equation(pi_he, p0, r_he, self._waypoints[wp - 1].time, k_he)

        return load_n2, load_he

    def _calculate_ceilings(self, wp: int):
        a = ((a_n2 * self._waypoints[wp].load_n2 + a_he * self._waypoints[wp].load_he) /
             (self._waypoints[wp].load_n2 + self._waypoints[wp].load_he))
        b = ((b_n2 * self._waypoints[wp].load_n2 + b_he * self._waypoints[wp].load_he) /
             (self._waypoints[wp].load_n2 + self._waypoints[wp].load_he))
        p_tol = (self._waypoints[wp].load_n2 + self._waypoints[wp].load_he - a) * b
        gf = self._params.gf_high - self._params.gf_low
        gf = gf / (1. - self._max_depth_ata)
        gf = gf * (self._waypoints[wp].ata_depth - 1.)
        gf = gf + self._params.gf_high

        return self._waypoints[wp].ata_depth - gf * (self._waypoints[wp].ata_depth - p_tol)

    def _add_direct_ascent(self):
        if self._waypoints[-1].time < 0:
            self._waypoints[-1].time = ceil(self._waypoints[-1].depth / self._params.v_asc)

        tank = self._select_gas(0)
        self._waypoints.append(Waypoint(depth=0, time=0, tank=tank))
        self._calculate_waypoint(len(self._waypoints) - 1)

    def _add_safety_stop(self):
        if self._waypoints[-1].time < 0:
            self._waypoints[-1].time = ceil(self._waypoints[-1].depth / self._params.v_asc)

        tank = self._select_gas(5)
        self._waypoints.append(Waypoint(depth=5, time=3, tank=tank))
        self._calculate_waypoint(len(self._waypoints) - 1)

        tank = self._select_gas(5)
        time_to_surface = ceil(self._waypoints[-1].depth / self._params.v_asc)
        self._waypoints.append(Waypoint(depth=5, time=time_to_surface, tank=tank))
        self._calculate_waypoint(len(self._waypoints) - 1)

        tank = self._select_gas(0)
        self._waypoints.append(Waypoint(depth=0, time=0, tank=tank))
        self._calculate_waypoint(len(self._waypoints) - 1)

    def _select_gas(self, depth):
        tank = 0
        max_o2 = 0
        for t in self._tanks:
            if (t.gas.O2 > max_o2) and (t.gas.mod(pp_o2=1.6) > depth):
                tank = self._tanks.index(t)

        return tank

    @property
    def waypoints(self):
        return dict(enumerate(self._waypoints))

    @property
    def tanks(self):
        return dict(enumerate(self._tanks))

    @property
    def depth(self):
        return deepcopy(self._depth)

    @property
    def ceiling(self):
        return deepcopy(self._ceiling)

    @property
    def runtime(self):
        return deepcopy(self._runtime)
