from profile import *

# Initialize setup object
params = Parameters(gf_low=1., gf_high=1.)

# Create tanks
tanks = [Tank(size=12, gas=Gas(o2=21), p_start=200),
         Tank(size=10, gas=Gas(o2=50), p_start=200)]

# Create waypoints
waypoints = [Waypoint(45, 15), Waypoint(15, 10), Waypoint(45, 0)]

# Create profile
profile = Profile(waypoints=waypoints, tanks=tanks, params=params)

for ip in profile.integration_points:
    print(ip)

profile.plot_integration_points()
