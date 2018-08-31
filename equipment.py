
from opentrons import robot, containers, instruments
from utilities import *

def getEquipment():
        equipment={}
        ############## DECK LAYOUT BEGINS HERE
        #CONTAINER DEFINITIONS:
        TransposeTipBox=True

        containers.create("24corning",grid=(4,6),spacing=(19.304,19.304),diameter=16.26,depth=18) #24-well plate

        #DECK:
        equipment['trash']=containers.load('point', "C1","trash")
        equipment['p200rack'] = containers.load('tiprack-200ul', 'E2', 'tiprack200')
        if TransposeTipBox:
             equipment['p1000rack']  = create_container_instance("TR1000-Transposed",slot="A1",grid=(8,12),spacing=(9.02,-9.02),diameter=5,depth=85,Transposed=True)
        else:
             equipment['p1000rack']  = create_container_instance("TR1000-Normal",slot="A1",grid=(8,12),spacing=(9.02,9.02),diameter=5,depth=85)
        equipment['CulturePlate']  = containers.load('24corning', 'B2', 'CulturePlate24')
        equipment['CulturePlate96']  = containers.load('96-flat', 'B2')
        equipment['CulturePlate2']  = containers.load('24corning', 'C2', 'CulturePlate242')
        equipment['AliquotPlate']  = containers.load('96-flat', 'C2', 'AliquotPlate')
        equipment['TubBlood']=create_container_instance("TubBlood",slot="D1",grid=(8,1),spacing=(9.02,9.02),diameter=0,depth=55)
        equipment['TubMedia']=create_container_instance("TubMedia",slot="D1",grid=(8,1),spacing=(9.02,9.02),diameter=0,depth=55)
        equipment['TubSybr']=create_container_instance("TubSybr",slot="D1",grid=(8,1),spacing=(9.02,9.02),diameter=0,depth=55)

        #PIPETTE(S)
        equipment['p1000'] = instruments.Pipette(
            name="P1000",
            axis="b",
            min_volume=20,
            max_volume=1000,
            tip_racks=[equipment['p1000rack']],
            trash_container=equipment['trash']
        )


        equipment['p200x8'] = instruments.Pipette(
            name="p200x8",
            axis="a",
            min_volume=20,
            max_volume=300,
            trash_container=equipment['trash'],
            channels=8
        )
        return(equipment)
