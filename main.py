from profile import *

# Initialize setup object
setup = Setup()

# Create tanks
cylinders = [Tank(size=12),
             Tank(gas=Gas(o2=50), size=10)]

# Create Waypoints
waypoints = [Waypoint(depth=30, time=20, tank=0),
             Waypoint(depth=25, time=10, tank=1)]

# Create profile
profile = Profile(setup=setup, tanks=cylinders, waypoints=waypoints)

i = 0
for k, w in profile.waypoints.items():
    print(w.depth, w.runtime, w.time, w.tank, profile.tanks[w.tank].gas, profile.tanks[w.tank].pressure[k])
