import json
from math import floor, log
from pathlib import Path
from matplotlib import pyplot as plt
from dataclasses import dataclass

import numpy as np

# Coefficients for Bühlmann ZH-L16C
ZH_L16 = {
    'C': {
        'N2': {
            'ht': np.array([5.0, 8.0, 12.5, 18.5, 27.0, 38.3, 54.3, 77.0, 109.0, 146.0, 187.0, 239.0, 305.0, 390.0,
                            498.0, 635.0]),
            'a': np.array([1.1696, 1.0000, 0.8618, 0.7562, 0.6200, 0.5043, 0.4410, 0.4000, 0.3750, 0.3500, 0.3295,
                           0.3065, 0.2835, 0.2610, 0.2480, 0.2327]),
            'b': np.array([0.5578, 0.6514, 0.7222, 0.7825, 0.8126, 0.8434, 0.8693, 0.8910, 0.9092, 0.9222, 0.9319,
                           0.9403, 0.9477, 0.9544, 0.9602, 0.9653])},
        'He': {
            'ht': np.array([1.88, 3.02, 4.72, 6.99, 10.21, 14.48, 20.53, 29.11, 41.20, 55.19, 70.69, 90.34, 115.29,
                            147.42, 188.24, 240.03]),
            'a': np.array([1.6189, 1.3830, 1.1919, 1.0458, 0.9220, 0.8205, 0.7305, 0.6502, 0.5950, 0.5545, 0.5333,
                           0.5189, 0.5181, 0.5176, 0.5172, 0.5119]),
            'b': np.array([0.4770, 0.5747, 0.6527, 0.7223, 0.7582, 0.7957, 0.8279, 0.8553, 0.8757, 0.8903, 0.8997,
                           0.9073, 0.9122, 0.9171, 0.9217, 0.9267])}}}

pw = 0.0567


class IncorrectGasMixture(Exception):
    pass


class IncorrectTimeUnit(Exception):
    pass


class InterpolationError(Exception):
    pass


class Time:
    def __init__(self, time: float | int, unit='m'):
        self._unit = unit
        if self._unit == 'm':
            self._minutes: float = time
            self._seconds: int = int(round(time * 60., 0))
        elif self._unit == 's':
            self._seconds = time
            self._minutes = self.seconds / 60
        else:
            raise IncorrectTimeUnit

    @property
    def seconds(self) -> int:
        return self._seconds

    @property
    def minutes(self) -> float:
        return self._minutes

    @property
    def unit(self) -> str:
        return self._unit

    def __str__(self) -> str:
        mins = floor(self._minutes)
        secs = self._seconds - mins * 60
        return '{:02d}:{:04.1f}'.format(int(floor(mins)), secs)

    def __repr__(self) -> str:
        return '<Time: {}>'.format(self._minutes)


@dataclass
class Parameters:
    last_stop_depth: float = 6
    stop_depth_incr: float = 3

    v_asc: float = 10
    v_desc: float = 20

    own_descent_sac: float = 20
    own_bottom_sac: float = 20
    own_ascent_sac: float = 17
    buddy_ascent_sac: float = 17

    gf_high: float = 1.
    gf_low: float = 1.

    calc_ascent: bool = True
    deco_stops: bool = True
    safety_stop: bool = True

    gas_switch = 'depth'  # 'depth' | 'stop'

    dt: Time = Time(time=5, unit='s')

    def to_json(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def from_json(self, json_str: str | Path) -> None:
        self.__dict__ = json.loads(json_str)


class Gas:
    def __init__(self, o2: int = 21, he: int = 0) -> None:
        self._O2: int = o2
        self._He: int = he
        self._N2: int = 100 - o2 - he

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


class Waypoint:
    def __init__(self, depth: float = 0., duration: float | Time = None, runtime: float | Time = None) -> None:
        self.depth: float = depth / 1.
        self.duration: Time
        self.runtime: Time

        if duration is None:
            self.duration = Time(0)
        elif isinstance(duration, Time):
            self.duration = duration
        else:
            self.duration = Time(duration)

        if runtime is None:
            self.runtime = Time(0)
        elif isinstance(runtime, Time):
            self.runtime = runtime
        else:
            self.runtime = Time(runtime)

    def __str__(self) -> str:
        return ('Waypoint(depth={depth:.1f}, duration={duration}, runtime={runtime})'
                .format(depth=self.depth, duration=self.duration, runtime=self.runtime))


class IntegrationPoint:
    def __init__(self, waypoint: Waypoint, tank: int) -> None:
        self.waypoint = waypoint
        self.tank = tank
        self.load_ig = {'N2': np.full(16, 0.79 * (1 - pw)), 'He': np.zeros(16)}
        self.ceilings = np.ones(16)

    @property
    def p_amb(self) -> float:
        return (self.waypoint.depth / 10.) + 1.

    @property
    def ceiling(self) -> float:
        if np.max(self.ceilings) > 0.:
            return np.max(self.ceilings)
        else:
            return 0.

    def __str__(self):
        return ('IntegrationPoint(depth={depth:.1f}, duration={duration}, runtime={runtime}, tank={tank},'
                ' ceiling={ceiling:.1f})'
                .format(depth=self.waypoint.depth, duration=self.waypoint.duration, runtime=self.waypoint.runtime,
                        tank=self.tank, ceiling=self.ceiling))


class Profile:
    def __init__(self, waypoints: list[Waypoint], tanks: list[Tank], params: Parameters = Parameters()) -> None:
        self._params: Parameters = params
        self._tanks: list[Tank] = tanks
        self._waypoints: list[Waypoint] = []
        self._integration_points: list[IntegrationPoint] = []

        self._complete_waypoints(waypoints)

        t = 0
        for idx, wp in enumerate(self._waypoints):
            if t > (wp.runtime.seconds + wp.duration.seconds):
                continue
            else:
                while t <= (wp.runtime.seconds + wp.duration.seconds):
                    new_wp = Waypoint(self._interpolate_depth(Time(t, 's')), self._params.dt, Time(t, 's'))

                    new_ip = IntegrationPoint(new_wp, self._select_tank(new_wp.depth))

                    if self._integration_points:
                        prev_ip = self._integration_points[-1]
                        new_ip.load_ig = self._calculate_compartments(new_ip, prev_ip)

                    new_ip.ceilings = self._calculate_ceilings(new_ip)
                    self._integration_points.append(new_ip)
                    t = t + self._params.dt.seconds

    def _complete_waypoints(self, waypoints: list[Waypoint]) -> None:
        if waypoints[0].depth != 0:
            time_to_bottom = Time(waypoints[0].depth / self._params.v_desc, unit='m')
            self._waypoints.append(Waypoint(0, time_to_bottom, Time(0)))
            self._waypoints.append(Waypoint(waypoints[0].depth, waypoints[0].duration, self._waypoints[0].duration))
        else:
            self._waypoints.append(Waypoint(waypoints[0].depth, waypoints[0].duration, Time(0)))

        for idx, wp in enumerate(waypoints[1:], start=1):
            prev_wp = self._waypoints[-1]

            if wp.depth > prev_wp.depth:
                desc_time = Time((wp.depth - prev_wp.depth) / self._params.v_desc)
                self._waypoints.append(Waypoint(prev_wp.depth, desc_time,
                                                prev_wp.runtime.minutes + prev_wp.duration.minutes))
            elif wp.depth < prev_wp.depth:
                asc_time = Time((prev_wp.depth - wp.depth) / self._params.v_asc)
                self._waypoints.append(Waypoint(prev_wp.depth, asc_time,
                                                prev_wp.runtime.minutes + prev_wp.duration.minutes))

            prev_wp = self._waypoints[-1]
            if idx == (len(waypoints) - 1):
                duration = Time(0)
            else:
                duration = wp.duration
            self._waypoints.append(Waypoint(wp.depth, duration, prev_wp.runtime.minutes + prev_wp.duration.minutes))

    def _calculate_compartments(self, ip: IntegrationPoint, prev_ip: IntegrationPoint):
        out = {}
        p_amb = ip.p_amb

        for g in ['N2', 'He']:
            p0 = prev_ip.load_ig[g]
            f_ig = self._tanks[prev_ip.tank].gas.fN2 if g == 'N2' else self._tanks[prev_ip.tank].gas.fHe
            pi = np.full(16, f_ig * (p_amb - pw))
            r = (((ip.waypoint.depth - prev_ip.waypoint.depth) / prev_ip.waypoint.duration.minutes) * f_ig) / 10
            k = log(2) / ZH_L16['C'][g]['ht']

            # Schreiner equation
            p_ig = pi
            p_ig = p_ig + r * (prev_ip.waypoint.duration.minutes - (1 / k))
            p_ig = p_ig - (pi - p0 - (r / k)) * np.exp(-k * prev_ip.waypoint.duration.minutes)

            out[g] = p_ig

        return out

    def _calculate_ceilings(self, ip: IntegrationPoint):
        a_n2 = ZH_L16['C']['N2']['a']
        b_n2 = ZH_L16['C']['N2']['b']
        a_he = ZH_L16['C']['He']['a']
        b_he = ZH_L16['C']['He']['b']
        load_n2 = ip.load_ig['N2']
        load_he = ip.load_ig['He']
        p_amb = ip.p_amb

        p_max = 0.
        for wp in self._waypoints:
            p_max = wp.depth if wp.depth > p_max else p_max
        p_max = (p_max / 10) + 1

        a = ((a_n2 * load_n2 + a_he * load_he) / (load_n2 + load_he))
        b = ((b_n2 * load_n2 + b_he * load_he) / (load_n2 + load_he))
        p_comp = load_n2 + load_he
        gf = self._params.gf_high - self._params.gf_low
        gf = gf / (1. - p_max)
        gf = gf * (p_amb - 1.)
        gf = gf + self._params.gf_high

        out = (p_comp - (a * gf))
        out = out / ((gf / b) - gf + 1.)

        return (out - 1.) * 10

    def _calculate_direct_ascent(self, ip: IntegrationPoint):
        prev_ip = ip
        new_ip = None
        t = ip.waypoint.runtime.seconds
        while prev_ip.waypoint.depth > 0.:
            t = t + self._params.dt
            new_wp = Waypoint(depth=prev_ip.waypoint.depth - (self._params.v_asc * self._params.dt.minutes),
                              duration=self._params.dt, runtime=Time(t))
            new_ip = IntegrationPoint(new_wp, prev_ip.tank)
            new_ip.load_ig = self._calculate_compartments(new_ip, prev_ip)
            new_ip.ceilings = self._calculate_ceilings(new_ip)

            prev_ip = new_ip

        return new_ip


    @property
    def waypoints(self) -> list[Waypoint]:
        return self._waypoints

    @property
    def integration_points(self) -> list[IntegrationPoint]:
        return self._integration_points

    @staticmethod
    def _schreiner_eq(pi: float | np.ndarray, p0: float | np.ndarray, r: float,
                      t: float, k: float | np.ndarray) -> float:
        out = pi
        out = out + r * (t - (1 / k))
        out = out - (pi - p0 - (r / k)) * np.exp(-k * t)

        return out

    def _select_tank(self, depth: float):
        tank = 0
        max_o2 = 0
        for t in self._tanks:
            if (t.gas.O2 > max_o2) and (t.gas.mod(pp_o2=1.6) > depth):
                tank = self._tanks.index(t)

        return tank

    def _interpolate_depth(self, runtime: Time) -> float:
        wp_0 = None
        wp_1 = None

        for idx, wp in enumerate(self._waypoints):
            if runtime.seconds == wp.runtime.seconds:
                return wp.depth
            elif runtime.seconds > wp.runtime.seconds:
                wp_0 = wp
                wp_1 = self._waypoints[idx + 1]
                continue

        if (wp_0 is None) or (wp_1 is None):
            raise InterpolationError

        out = (wp_1.depth - wp_0.depth) / (wp_1.runtime.seconds - wp_0.runtime.seconds)
        out = out * (runtime.seconds - wp_0.runtime.seconds)
        out = out + wp_0.depth

        return out

    def plot_waypoints(self):
        depth = []
        runtime = []
        for wp in self._waypoints:
            depth.append(wp.depth)
            runtime.append(wp.runtime.seconds)
        plt.gca().invert_yaxis()
        plt.plot(runtime, depth, 'bo-')
        plt.show()

    def plot_integration_points(self):
        depth = []
        runtime = []
        for ip in self._integration_points:
            depth.append(ip.waypoint.depth)
            runtime.append(ip.waypoint.runtime.seconds)
        plt.gca().invert_yaxis()
        plt.plot(runtime, depth, 'bo-', markersize=2)
        plt.show()

    def plot_compartment(self, gas: str, compartment: int):
        p_ig = []
        runtime = []
        for ip in self._integration_points:
            p_ig.append(ip.load_ig[gas][compartment - 1])
            runtime.append(ip.waypoint.runtime.seconds)
        plt.gca().invert_yaxis()
        plt.plot(runtime, p_ig, 'bo-', markersize=2)
        plt.show()

    def plot_compartments(self, gas: str):
        colors = 'bgrcmkbgrcmkbgrc'
        for c in range(16):
            p_ig = []
            runtime = []
            for ip in self._integration_points:
                p_ig.append(ip.load_ig[gas][c])
                runtime.append(ip.waypoint.runtime.seconds)
            plt.plot(runtime, p_ig, colors[c] + 'o-', markersize=2)
        plt.gca().invert_yaxis()
        plt.show()

    def plot_ceilings(self):
        colors = 'bgrcmkbgrcmkbgrc'
        for c in range(16):
            ceilings = []
            runtime = []
            for ip in self._integration_points:
                ceilings.append(ip.ceilings[c])
                runtime.append(ip.waypoint.runtime.seconds)
            plt.plot(runtime, ceilings, colors[c] + 'o-', markersize=2)
        plt.gca().invert_yaxis()
        plt.show()

    def plot_ceiling(self):
        ceiling = []
        runtime = []
        for ip in self._integration_points:
            ceiling.append(ip.ceiling)
            runtime.append(ip.waypoint.runtime.seconds)
        plt.gca().invert_yaxis()
        plt.plot(runtime, ceiling, 'bo-', markersize=2)
        plt.show()
