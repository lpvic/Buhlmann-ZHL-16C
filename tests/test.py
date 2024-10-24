from src.yabai import *

# Initialize setup object
params = Parameters(dt=Time(1, 's'), gf_low=1., gf_high=1., last_stop_depth=3, gas_switch='stop')

# Create tanks
tanks = [Tank(size=15, gas=Gas(o2=21), start_pressure=200),
         Tank(size=10, gas=Gas(o2=50), start_pressure=200)]

# Create waypoints
waypoints = [Waypoint(45, 75)]  # , Waypoint(30, 2)]
# waypoints = [Waypoint(45, 7), Waypoint(45, (45 - 5) / params.v_asc),
#              Waypoint(5, 3), Waypoint(0, 0)]
# waypoints = [Waypoint(45, 25), Waypoint(15, 10), Waypoint(45, 0)]

# Create profile
profile = Profile(waypoints=waypoints, tanks=tanks, params=params)

for ip in profile.integration_points:
    pass
    print(ip)

for wp in profile.waypoints:
    print(wp)

profile.plot_waypoints()
profile.plot_integration_points()
profile.plot_compartments('N2')
profile.plot_ceilings()
profile.plot_ceiling()
profile.plot()
