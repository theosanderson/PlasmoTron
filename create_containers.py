from opentrons import robot, containers, instruments
from utilities import *

# create the custom containers: 24 and 6 well plates
# this will create a file ./containers/_contaiers_create.json
# which will be used to load the custom containers
# It should not be necessary to run this script as the
# JSON file is part of the repo so this is mainly here
# for reference to show how it was created.
# When using this, check the created file for order of
# well, which should be given in the same order that 
# they are to be used, i.e. A1, B1, C1 .. , A2, B2, C2...
containers.create("24corning",grid=(4,6),spacing=(19.304,19.304),diameter=16.26,depth=18) #24-well plate
containers.create("6corning",grid=(2,3),spacing=(39.12,39.12),diameter=34.80,depth=11.27) #6-well plate

