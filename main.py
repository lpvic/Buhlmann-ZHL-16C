from profile import *
from matplotlib import pyplot as plt

# Initialize setup object
params = Parameters()
params.gf_low = 0.3
params.gf_high = .75

# Create tanks
tanks = [Tank(size=12, gas=Gas(o2=21), p_start=200),
         Tank(size=10, gas=Gas(o2=50), p_start=200)]

# Create Waypoints
waypoints1 = [Waypoint(depth=5, time=0.25),
              Waypoint(depth=10, time=0.25), Waypoint(depth=10, time=0.25), Waypoint(depth=10, time=0.25), Waypoint(depth=10, time=0.25), Waypoint(depth=10, time=0.25), Waypoint(depth=10, time=0.25), Waypoint(depth=10, time=0.25), Waypoint(depth=10, time=0.25),
              Waypoint(depth=15, time=0.25),
              Waypoint(depth=20, time=0.25),
              Waypoint(depth=25, time=0.25),
              Waypoint(depth=30, time=0.25),
              Waypoint(depth=35, time=0.25),
              Waypoint(depth=40, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45, time=0.25),
              Waypoint(depth=45)]

waypoints2 = [Waypoint(depth=10, time=2), Waypoint(depth=10, time=2),
              Waypoint(depth=45, time=15),
              Waypoint(depth=45)]

# Create profile
profile1 = Profile(params=params, tanks=tanks, waypoints=waypoints1)
profile2 = Profile(params=params, tanks=tanks, waypoints=waypoints2)

for k, w in profile1.waypoints.items():
    print(w.depth, w.runtime, w.time, w.tank, profile1.tanks[w.tank].gas,
          [profile1.tanks[t].pressure[k] for t in range(len(profile1.tanks))], w.ceiling)

plt.gca().invert_yaxis()
plt.plot(profile1.runtime, profile1.depth, 'bo-')
plt.plot(profile1.runtime, profile1.ceiling, 'ro--')
plt.plot(profile2.runtime, profile2.depth, 'ko-')
plt.plot(profile2.runtime, profile2.ceiling, 'go--')
plt.show()
