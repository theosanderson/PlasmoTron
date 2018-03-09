
from opentrons import robot, containers, instruments
import sys
import urllib.request
import urllib.parse
equipment = {}
CalibrationMode=None
if len(sys.argv)>1 and sys.argv[1]=="simulate":
    robot.connect()
elif len(sys.argv)>1 and sys.argv[1]=="control":
    robot.connect(robot.get_serial_ports_list()[0])
    if not robot.is_connected():
        raise Exception('Did not connect')
else:
    CalibrationMode=True
if not CalibrationMode:
    import sqlite3
    import time
    import string
    dbd = sqlite3.connect('plasmotron.db', timeout=100000)

############## DECK LAYOUT BEGINS HERE
#CONTAINER DEFINITIONS:
containers.create("epmotion30",grid=(8,1),spacing=(9.02,9.02),diameter=10,depth=55) #EpMotion Reservoir
containers.create("24corning",grid=(4,6),spacing=(19.304,19.304),diameter=16.26,depth=18) #24-well plate

#DECK:
equipment['trash']=containers.load('point', "C1","trash")
equipment['p200rack'] = containers.load('tiprack-200ul', 'E2', 'tiprack200')
equipment['p1000rack']  = containers.load('tiprack-1000ulT', 'A1', 'tiprack1000T')
equipment['CulturePlate']  = containers.load('24corning', 'B2', 'CulturePlate24')
equipment['CulturePlate96']  = containers.load('96-flat', 'B2')
equipment['CulturePlate2']  = containers.load('24corning', 'C2', 'CulturePlate242')
equipment['AliquotPlate']  = containers.load('96-flat', 'C2', 'AliquotPlate')
equipment['TubBlood']=containers.load('epmotion30', "D1","TubBlood")
equipment['TubMedia']=containers.load('epmotion30', "D1","TubMedia")
equipment['TubSybr']=containers.load('epmotion30', "D1","TubSybr")

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
    max_volume=200,
    trash_container=equipment['trash'],
    channels=8
)

#equipment['p200x1'] = instruments.Pipette(
#    name="p200x1",
#    axis="a",
#    min_volume=20,
#    max_volume=1000,
#    trash_container=equipment['trash']
#)
############## DECK LAYOUT ENDS HERE


#equipment['p200x8'] = instruments.Pipette(
#    axis='a',
#    name='P200x8',
#    max_volume=200,
#    min_volume=20,
#    tip_racks=[p200rack,p200rack2],
#    tip_racks=[equipment['p200rack']],
#    trash_container=equipment['trash'],
#    channels=8)

if CalibrationMode:
    # Iterate through all equipment issuing a dummy command to allow calibration
    for key in equipment:
        if key!="p1000" and key !='p200x1' and key != 'p200x8':
            equipment['p1000'].move_to(equipment[key][0])
            #equipment['p200x1'].move_to(equipment[key][0])
            equipment['p200x8'].move_to(equipment[key][0])
else:
    robot.home()

    robot.head_speed(8000)

    dbd.row_factory=sqlite3.Row
    db=dbd.cursor()
    while 1:
        a=db.execute("SELECT * FROM CommandQueue  WHERE doneAt is NULL AND queued= 1 ORDER BY OrderOfEvents" )
        command=a.fetchone()
        if(command == None):

            time.sleep(0.1)
            #print("none")
        else:
            if command['Command']=="Email":

                    params = urllib.parse.urlencode({'email': command['email'], 'msg': command['message']})
                    req="http://phenoplasm.org/sendplasmotronemail.php?";
                    try: 
                        urllib.request.urlopen(req+params)
                    except urllib.error.URLError as e:
                        print(e.reason)
            if command['Command']=="MoreTips":
                    #todo prompt for more tips, for now will just pause queue
                    db.execute('UPDATE CommandQueue SET queued=0 WHERE queued=1')
                    dbd.commit()
            if command['Command']=="Home":
                robot.home()
            if command['Command']=="Aspirate":
                if command['Row'] is not None:
                    location=equipment[command['Labware']].cols(int(command['Row'])).wells(int(command['Column']))
                else:
                    location=equipment[command['Labware']]

                equipment[command['Pipette']].aspirate(command['Volume'],location)
            if command['Command']=="AirGap":
                #print("gap")
                try:
                    equipment[command['Pipette']].air_gap(20)
                except:
                    print("airgapproblem")
            if command['Command']=="GetTips":
                if command['Row'] is not None:
                    location=equipment[command['Labware']].cols(int(command['Row'])).wells(int(command['Column']))
                else:
                    raise Exception("Where are tips?") 

                equipment[command['Pipette']].pick_up_tip(location)
            if command['Command']=="ResuspendReservoir":
                for i in range(8):
                    equipment[command['Pipette']].aspirate(1000,equipment[command['Labware']][i],rate=2)
                    equipment[command['Pipette']].dispense(1000,equipment[command['Labware']][i].bottom(),rate=2)

            if command['Command']=="Resuspend" or command['Command']=="ResuspendDouble":
                if command['Row'] is not None:
                    location=equipment[command['Labware']].cols(int(command['Row'])).wells(int(command['Column']))
                else:
                    location=equipment[command['Labware']]


                well_edge = location.from_center(x=0.5,y=0,z=-1)
                destination = (location, well_edge)
                equipment[command['Pipette']].aspirate(700,destination,rate=1.8)
                equipment[command['Pipette']].dispense(700,destination,rate=2)
                well_edge = location.from_center(x=0,y=0.5,z=-1)
                destination = (location, well_edge)
                equipment[command['Pipette']].aspirate(700,destination,rate=1.8)
                equipment[command['Pipette']].dispense(700,destination,rate=2)
                well_edge = location.from_center(x=-0.5,y=0,z=-1)
                destination = (location, well_edge)
                equipment[command['Pipette']].aspirate(700,destination,rate=1.8)
                equipment[command['Pipette']].dispense(700,destination,rate=2)
                well_edge = location.from_center(x=0,y=-0.5,z=-1)
                destination = (location, well_edge)
                equipment[command['Pipette']].aspirate(700,destination,rate=1.8)
                equipment[command['Pipette']].dispense(700,destination,rate=2)
                if command['Command']=="ResuspendDouble":
                    well_edge = location.from_center(x=0.35,y=0.35,z=-1)
                    destination = (location, well_edge)
                    equipment[command['Pipette']].aspirate(700,destination,rate=1.8)
                    equipment[command['Pipette']].dispense(700,destination,rate=2)
                    well_edge = location.from_center(x=-0.35,y=-0.35,z=-1)
                    destination = (location, well_edge)
                    equipment[command['Pipette']].aspirate(700,destination,rate=1.8)
                    equipment[command['Pipette']].dispense(700,destination,rate=2)
                    well_edge = location.from_center(x=-0.35,y=.35,z=-1)
                    destination = (location, well_edge)
                    equipment[command['Pipette']].aspirate(700,destination,rate=1.8)
                    equipment[command['Pipette']].dispense(700,destination,rate=2)
                    well_edge = location.from_center(x=.35,y=-0.35,z=-1)
                    destination = (location, well_edge)
                    equipment[command['Pipette']].aspirate(700,destination,rate=1.8)
                    equipment[command['Pipette']].dispense(700,destination,rate=2)
                
            if command['Command']=="Dispense":
                if command['Row'] is not None:
                    location=equipment[command['Labware']].cols(int(command['Row'])).wells(int(command['Column']))
                else:
                    location=equipment[command['Labware']]
                equipment[command['Pipette']].dispense(command['Volume'],location)
            if command['Command']=="DispenseBottom":
                if command['Row'] is not None:
                    location=equipment[command['Labware']].cols(int(command['Row'])).wells(int(command['Column'])).bottom()
                else:
                    location=equipment[command['Labware']]
                equipment[command['Pipette']].dispense(command['Volume'],location)
            if command['Command']=="DropTip":
                equipment[command['Pipette']].dispense(equipment['trash'],rate=2)
                equipment[command['Pipette']].drop_tip()

            while 1:
                try:
                    timestamp=time.time()
                    db.execute("UPDATE CommandQueue SET doneAt=?, queued=0 WHERE CommandID= ?",[timestamp,command['CommandID']])
                    dbd.commit()
                    if(command['OnCompletion'] is not None):
                        torun=command['OnCompletion']

                        torun=torun.replace( "<time>", str(timestamp))
                        #print(torun)
                        db.execute(torun)
                        dbd.commit()
                    break;
                except sqlite3.OperationalError as err:
                    print("database locked? "+ str(err))
                    time.sleep(0.5)
            dbd.commit()
            #time.sleep(3)

    db.close()

