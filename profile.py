import json
from math import log, ceil
from pathlib import Path
from copy import deepcopy
from collections import namedtuple
from matplotlib import pyplot as plt
from dataclasses import dataclass

import numpy as np

# Coefficients for Bühlmann ZH-L16C
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

Waypoint = namedtuple('Waypoint', 'depth duration runtime', defaults=[0, 0, 0])


class IncorrectGasMixture(Exception):
    pass


@dataclass
class Parameters:
    last_stop_depth = 6
    stop_depth_incr = 3

    v_asc = 10
    v_desc = 20

    own_descent_sac = 20
    own_bottom_sac = 20
    own_ascent_sac = 17
    buddy_ascent_sac = 17

    gf_high = 1.
    gf_low = 1.

    calc_ascent = True
    deco_stops = True
    safety_stop = True

    dt = 10. / 60.

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

    @property
    def He(self) -> int:
        return self._He

    @property
    def N2(self) -> int:
        return self._N2

    @property
    def fO2(self) -> float:
        return self._O2 / 100.

    @property
    def fN2(self) -> float:
        return self._N2 / 100.

    @property
    def fHe(self) -> float:
        return self._He / 100.

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


class Point:
    def __init__(self, depth: float, time: int = -1, tank: int = 0) -> None:
        self._depth = depth
        self._tank = tank
        self.time = time
        self.runtime = 0
        self.load_n2 = np.zeros(16)
        self.load_he = np.zeros(16)
        self.ceilings = np.ones(16)

    @property
    def ata_depth(self) -> float:
        return (self._depth / 10.) + 1.

    @property
    def depth(self) -> float:
        return self._depth

    @property
    def tank(self) -> int:
        return self._tank

    @property
    def ceiling(self) -> float:
        if np.max(self.ceilings) > 1.:
            return (np.max(self.ceilings) - 1.) * 10.
        else:
            return 0.

    def __str__(self) -> str:
        return ' '.join([str(self.depth), str(self.runtime), str(self.time), str(self.tank), str(self.ceiling)])


class Profile:
    def __init__(self, waypoints: list[Waypoint], tanks: list[Tank],
                 params: Parameters = Parameters()) -> None:
        self._params = params
        self._tanks = tanks
        self._waypoints = []
        self._max_depth_ata = 0.
        self._depth = []
        self._ceiling = []
        self._runtime = []
        self._points = []

        self._complete_waypoints(waypoints)

    def _complete_waypoints(self, waypoints):
        if waypoints[0].depth != 0:
            time_to_bottom = waypoints[0].depth / self._params.v_desc
            self._waypoints.append(Waypoint(0, time_to_bottom, 0))
            self._waypoints.append(Waypoint(waypoints[0].depth, waypoints[0].duration, self._waypoints[0].duration))
        else:
            self._waypoints.append(Waypoint(waypoints[0].depth, waypoints[0].duration, 0))

        for idx, wp in enumerate(waypoints[1:], start=1):
            prev_wp = self._waypoints[-1]

            if wp.depth > prev_wp.depth:
                desc_time = (wp.depth - prev_wp.depth) / self._params.v_desc
                self._waypoints.append(Waypoint(prev_wp.depth, desc_time, prev_wp.runtime + prev_wp.duration))
            elif wp.depth < prev_wp.depth:
                asc_time = (prev_wp.depth - wp.depth) / self._params.v_asc
                self._waypoints.append(Waypoint(prev_wp.depth, asc_time, prev_wp.runtime + prev_wp.duration))

            prev_wp = self._waypoints[-1]
            if idx == (len(waypoints) - 1):
                duration = 0
            else:
                duration = wp.duration
            self._waypoints.append(Waypoint(wp.depth, duration, prev_wp.runtime + prev_wp.duration))

    @property
    def waypoints(self):
        return self._waypoints

    @staticmethod
    def _schreiner(pi: float | np.ndarray, p0: float | np.ndarray, r: float, t: float, k: float | np.ndarray) -> float:
        out = pi
        out = out + r * (t - (1 / k))
        out = out - (pi - p0 - (r / k)) * np.exp(-k * t)

        return out

    @staticmethod
    def _interpolate(wp_0: Waypoint, wp_1: Waypoint, runtime: float):
        out = (wp_1.depth - wp_0.depth) / (wp_1.runtime - wp_0.runtime)
        out = out * (runtime - wp_0.runtime)
        out = out + wp_0.depth

        return out

    def plot(self):
        depth = []
        runtime = []
        for wp in self._waypoints:
            depth.append(wp.depth)
            runtime.append(wp.runtime)
        plt.gca().invert_yaxis()
        plt.plot(runtime, depth, 'bo-')
        plt.show()
