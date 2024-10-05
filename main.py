from profile import *
from matplotlib import pyplot as plt

# Initialize setup object
setup = Setup()

# Create tanks
cylinders = [Tank(size=12, gas=Gas(o2=32)),
             ]

# Create Waypoints
waypoints = [Waypoint(depth=45, time=20, tank=0),
             Waypoint(depth=45, time=4, tank=0)]

# Create profile
profile = Profile(setup=setup, tanks=cylinders, waypoints=waypoints)

i = 0
depth = []
runtime = []
for k, w in profile.waypoints.items():
    print(w.depth, w.runtime, w.time, w.tank, profile.tanks[w.tank].gas,
          [profile.tanks[t].pressure[k] for t in range(len(profile.tanks))], w.ceiling)

    depth.append(w.depth)
    runtime.append(w.runtime)

plt.gca().invert_yaxis()
plt.plot(runtime, depth)
plt.show()
