
from opentrons import robot, containers, instruments
import sys
import urllib.request
import urllib.parse
from equipment import getEquipment

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

equipment=getEquipment()
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
    
    while 1:
        db=dbd.cursor()
        a=db.execute("SELECT * FROM CommandQueue  WHERE doneAt is NULL AND queued= 1 ORDER BY OrderOfEvents LIMIT 1" )
        command=a.fetchone()
        db.close()
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

                    db=dbd.cursor()
                    db.execute('UPDATE CommandQueue SET queued=0 WHERE queued=1')
                    dbd.commit()
                    db.close()
                    
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
                    db=dbd.cursor()
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

