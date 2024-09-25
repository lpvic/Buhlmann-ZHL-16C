from profile import *

# Initialize setup object
setup = Setup()

# Create cylinders
cylinders = [Cylinder(size=12), Cylinder(gas=GasMixture(o2=50), size=10)]

# Create Waypoints
waypoints = [Waypoint(depth=30, time=20, cylinder=0), Waypoint(depth=25, time=10, cylinder=1)]

# Create profile
profile = Profile(setup=setup, cylinders=cylinders, waypoints=waypoints)

for w in profile.waypoints:
    print(w.depth, w.time, profile._cylinders[w.cylinder].gas, profile._cylinders[w.cylinder].pressure)
