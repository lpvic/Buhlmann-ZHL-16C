from profile import *
from matplotlib import pyplot as plt

# Initialize setup object
setup = Setup()

# Create tanks
tanks = [Tank(size=12, gas=Gas(o2=21), p_start=200),
         Tank(size=10, gas=Gas(o2=50), p_start=200)]

# Create Waypoints
waypoints = [Waypoint(depth=15, time=15),
             Waypoint(depth=25)]

# Create profile
profile = Profile(setup=setup, tanks=tanks, waypoints=waypoints)

i = 0
depth = []
runtime = []
ceiling = []
for k, w in profile.waypoints.items():
    print(w.depth, w.runtime, w.time, w.tank, profile.tanks[w.tank].gas,
          [profile.tanks[t].pressure[k] for t in range(len(profile.tanks))], w.ceiling)

    depth.append(w.depth)
    runtime.append(w.runtime)
    ceiling.append(w.ceiling)

plt.gca().invert_yaxis()
plt.plot(runtime, depth, 'bo-')
plt.plot(runtime, ceiling, 'rv--')
plt.show()
