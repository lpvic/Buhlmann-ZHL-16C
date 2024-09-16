import json
from pathlib import Path


class IncorrectGasMixture(Exception):
    pass


class Config:
    def __init__(self):
        self.lastStopDepth = 6
        self.ownBottomSAC = 20
        self.ownAscentSAC = 22
        self.buddyAscentSAC = 22

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def fromJSON(self, json_str: str | Path):
        self.__dict__ = json.loads(json_str)


class GasMixture:
    def __init__(self, o2=21, he=0):
        self._O2 = o2
        self._He = he
        self._N2 = 100 - o2 - he

    def ppO2(self, depth):
        pabs = (depth / 10) + 1
        return pabs * self._O2 / 100

    def ppN2(self, depth):
        pabs = (depth / 10) + 1
        return pabs * self._N2 / 100

    def ppHe(self, depth):
        pabs = (depth / 10) + 1
        return pabs * self._He / 100

    @property
    def O2(self):
        return self._O2

    @O2.setter
    def O2(self, v):
        self._O2 = v
        self._N2 = 100 - self._O2 - self._He

    @property
    def He(self):
        return self._He

    @He.setter
    def He(self, v):
        self._He = v
        self._N2 = 100 - self._O2 - self._He

    def __str__(self):
        if (self._O2 == 21) and (self._He == 0):
            return 'Air'
        elif self._He == 0:
            return 'Nitrox{}'.format(self._O2)
        else:
            return 'Trimix{}/{}'.format(self._O2, self._He)

    def __repr__(self):
        return '<Gas Mixture: O2: {} N2: {} He: {}>'.__format__(self._O2, self._N2, self._He)


class Cylinder:
    def __init__(self):
        self.gas = GasMixture()
        self.pressure = {}

class ProfilePoint:
    def __init__(self, depth, time):
        self._depth = depth
        self._time = time

    @property
    def depth(self):
        return self._depth

    @property
    def time(self):
        return self._time


class Profile:
    def __init__(self):
        self.segments = {}

    def add_segment(self, segment, cylinder):



if __name__ == '__main__':
    profile = {}

