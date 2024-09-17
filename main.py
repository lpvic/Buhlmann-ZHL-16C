import math
import json
from pathlib import Path


class IncorrectGasMixture(Exception):
    pass


class Setup:
    def __init__(self) -> None:
        self.last_stop_depth = 6
        self.stop_depth_incr = 3

        self.v_asc = 9
        self.v_desc = 20

        self.own_bottom_sac = 20
        self.own_ascent_sac = 22
        self.buddy_ascent_sac = 22

    def to_json(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def from_json(self, json_str: str | Path) -> None:
        self.__dict__ = json.loads(json_str)


class GasMixture:
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
            return 'Nitrox{}'.format(self._O2)
        else:
            return 'Trimix{}/{}'.format(self._O2, self._He)

    def __repr__(self) -> str:
        return '<Gas Mixture: O2: {} N2: {} He: {}>'.format(self._O2, self._N2, self._He)


class Cylinder:
    def __init__(self, o2: int = 21, he: int = 0):
        self.gas = GasMixture(o2, he)
        self.pressure = []


class Waypoint:
    def __init__(self, depth: float, time: int, cylinder: int) -> None:
        self._depth = depth
        self._time = time
        self._cylinder = cylinder

    @property
    def depth(self):
        return self._depth

    @property
    def time(self):
        return self._time

    @property
    def cylinder(self):
        return self._cylinder



class Profile:
    def __init__(self, setup: Setup, cylinders: list[Cylinder], waypoints: list[Waypoint]) -> None:
        self._setup = setup
        self._cylinders = cylinders
        self._waypoints = waypoints

        self._complete_profile()

    def add_waypoint(self, segment):
        pass

    def _complete_profile(self):
        if waypoints[0].depth != 0:
            time_to_bottom = math.ceil(self._waypoints[0].depth / self._setup.v_desc)
            self._waypoints.insert(0, Waypoint(depth=0, time=time_to_bottom, cylinder=self._waypoints[0].cylinder))


if __name__ == '__main__':
    # Initialize setup object
    setup = Setup()

    # Create cylinders
    cylinders = [Cylinder(), Cylinder(o2=50)]

    # Create Waypoints
    waypoints = [Waypoint(depth=30, time=20, cylinder=0), Waypoint(depth=25, time=10, cylinder=0)]

    # Create profile
    profile = Profile(setup=setup, cylinders=cylinders, waypoints=waypoints)

    for w in profile._waypoints:
        print(w.depth, w.time, w.cylinder)

