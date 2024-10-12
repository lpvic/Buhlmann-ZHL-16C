from profile import *

# Initialize setup object
params = Parameters(dt=Time(1, 's'))

# Create tanks
tanks = [Tank(size=12, gas=Gas(o2=21), p_start=200)]  # ,
         # Tank(size=10, gas=Gas(o2=50), p_start=200)]

# Create waypoints
# waypoints = [Waypoint(45, 15), Waypoint(15, 10), Waypoint(45, 0)]
# waypoints = [Waypoint(45, 7), Waypoint(45, (45 - 5) / params.v_asc),
#              Waypoint(5, 3), Waypoint(0, 0)]
waypoints = [Waypoint(45, 15), Waypoint(15, 10), Waypoint(45, 0)]

# Create profile
profile = Profile(waypoints=waypoints, tanks=tanks, params=params)

for ip in profile.integration_points:
    print(ip)

profile.plot_waypoints()
profile.plot_integration_points()
profile.plot_compartments('N2')
profile.plot_ceilings()
profile.plot_ceiling()
