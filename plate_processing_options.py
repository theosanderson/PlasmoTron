# PlasmoTron actions
tipcounter = [int(request.form['tips1000']), int(request.form['tips200'])]
maxtips = [96, 12]
dimensions = [[12, 8], [12, 1]]
pipettenames = ['p1000', 'p200x8']
tipracks = ['p1000rack', 'p200rack']
MeasurementPlate = None
MeasurementAvailableWells = []

class CommandIssuer():
  def __init__(self,db):
    self.db = db
  def getTip(pipette):
    nonlocal tipcounter

    if tipcounter[pipette] == maxtips[pipette]:
      email(
          request.form['email'],
          "Please load more tips! <br> <img src='http://phenoplasm.org/sadtips.jpg'>"
      )
    self.db.execute('INSERT INTO CommandQueue (Command) VALUES ("MoreTips")')
      tipcounter[pipette] = 0
    col, row = divmod(tipcounter[pipette], dimensions[pipette][1])
    onexecute = 'UPDATE MachineStatusProperties SET value = ' + str(
        tipcounter[pipette] +
        1) + ' WHERE name = "' + 'tipsusedpipette' + str(pipette) + '"'
    print(onexecute)
    self.db.execute(
        'INSERT INTO CommandQueue (Command, Pipette, Labware, Row, Column, OnCompletion) VALUES ("GetTips",?,?,?,?,?)',
        [pipettenames[pipette], tipracks[pipette], row, col, onexecute])

    tipcounter[pipette] = tipcounter[pipette] + 1

  def dropTip(pipette):
    self.db.execute(
        'INSERT INTO CommandQueue (Command, Pipette, Labware) VALUES ("DropTip",?,"trash")',
        [pipettenames[pipette]])

  def email(email, message):
    self.db.execute(
        'INSERT INTO CommandQueue (Command,email, message) VALUES (?,?,?)',
        ['Email', email, message])

  def aspirate(pipette, labware, volume, row=None, col=None, plateid=None):
    self.db.execute(
        'INSERT INTO CommandQueue (Command, Pipette, Volume, Labware, Row, Column, PlateID) VALUES ("Aspirate",?,?,?,?,?,?)',
        [pipettenames[pipette], volume, labware, row, col, plateid])

  def dispense(pipette,
               labware,
               volume,
               row=None,
               col=None,
               oncompletion=None,
               plateid=None,
               bottom=False):
    if (bottom == True):
      self.db.execute(
          'INSERT INTO CommandQueue (Command, Pipette, Volume, Labware, Row, Column,OnCompletion,PlateID) VALUES ("DispenseBottom",?,?,?,?,?,?,?)',
          [
              pipettenames[pipette], volume, labware, row, col, oncompletion,
              plateid
          ])
    else:
      self.db.execute(
          'INSERT INTO CommandQueue (Command, Pipette, Volume, Labware, Row, Column,OnCompletion,PlateID) VALUES ("Dispense",?,?,?,?,?,?,?)',
          [
              pipettenames[pipette], volume, labware, row, col, oncompletion,
              plateid
          ])

  def resuspendReservoir(pipette, labware):
    self.db.execute(
        'INSERT INTO CommandQueue (Command, Pipette,  Labware) VALUES (?,?,?)',
        ['ResuspendReservoir', pipettenames[pipette], labware])

  def resuspend(pipette,
                labware,
                volume,
                row=None,
                col=None,
                plateid=None,
                double=False):
    if double == False:
      Command = 'Resuspend'
    else:
      Command = 'ResuspendDouble'
    self.db.execute(
        'INSERT INTO CommandQueue (Command, Pipette, Volume, Labware, Row, Column,PlateID) VALUES (?,?,?,?,?,?,?)',
        [Command, pipettenames[pipette], volume, labware, row, col, plateid])

  def airgap(pipette):
    self.db.execute(
        'INSERT INTO CommandQueue (Command, Pipette) VALUES ("AirGap",?)',
        [pipettenames[pipette]])

  def home():
    self.dropTip(0)
    self.dropTip(1)
    self.db.execute('INSERT INTO CommandQueue (Command) VALUES (?)', ['Home'])
    
  def generateMultiDispense(source, destwells):

    curvol = 0
    self.getTip(0)
    for well in destwells:
      (plate, row, col) = well
      if curvol < 200:
        self.aspirate(0, 'TubSybr', 1000)
        curvol = 1000
      self.dispense(0, 'AliquotPlate', 200, row, col)
      curvol = curvol - 200
    self.airgap(0)
    self.dropTip(0)

def createOnExecute(action, plateid, platerow, platecol, actionValue=None):
  if actionValue is None:
    onexecute = ('INSERT INTO Actions '
                 '(PlateID,Row,Column,TypeOfOperation,ActionTime) VALUES ('
                ) + str(plateid) + ',' + str(platerow) + ',' + str(
                    platecol) + ",'" + action + "'," + '<time>)'
  else:
    onexecute = (
        'INSERT INTO Actions '
        '(PlateID,Row,Column,TypeOfOperation,ActionTime,ValueOfOperation)'
        ' VALUES ('
    ) + str(plateid) + ',' + str(platerow) + ',' + str(
        platecol) + ",'" + action + "'," + '<time>,' + str(actionValue) + ')'

  return (onexecute)


def getNextMeasurementWell():
  nonlocal MeasurementAvailableWells
  nonlocal MeasurementPlate
  if (len(MeasurementAvailableWells) == 0):
    cur = db.execute(
        'SELECT * FROM Plates WHERE PlatePurpose=2 AND PlateFinished=0')
    plates = cur.fetchall()
    for one in plates:
      MeasurementPlate = one['PlateID']
      MeasurementAvailableWells = []
      for y in range(12):
        for x in range(8):
          MeasurementAvailableWells.append((x, y))

      cur2 = db.execute('SELECT * FROM PlatePositions WHERE PlateID=?',
                        [one['PlateID']])
      wells = cur2.fetchall()
      for well in wells:

        indices = [
            i for i, tupl in enumerate(MeasurementAvailableWells)
            if tupl[0] == well['Row'] and tupl[1] == well['Column']
        ]
        MeasurementAvailableWells.pop(indices[0])
      if len(MeasurementAvailableWells) > 0:
        break
    if len(MeasurementAvailableWells) == 0:
      #flash('No measurement plates available')
      return (-1, -1, -1)

  (row, col) = MeasurementAvailableWells[0]
  MeasurementAvailableWells.pop(0)
  return (MeasurementPlate, row, col)

db = get_db()
cur = db.execute('SELECT * FROM CommandQueue WHERE doneAt IS NULL')
if (cur.fetchone() != None):
  flash('Please clear the queue first')
  return redirect(url_for('view_refreshed'))
home()
cur = db.execute(
    'SELECT PlateRows,PlateCols,PlateClass FROM Plates INNER JOIN PlateClasses ON Plates.PlateClass= PlateClasses.PlateClassID WHERE PlateID= ?',
    [request.form['plateid']])

platestats = cur.fetchone()

if platestats['PlateClass'] == 0:
  cur = db.execute(
      'INSERT INTO CommandQueue (Command, Labware, LabwareType,Slot) VALUES ("InitaliseLabware","CulturePlate","96-flat","B1")'
  )

  feedVolume = 200
  extraRemoval = 5
  aliquotvol = 40
  resuspvol = 150

elif platestats['PlateClass'] == 1:
  cur = db.execute(
      'INSERT INTO CommandQueue (Command, Labware, LabwareType,Slot) VALUES ("InitaliseLabware","CulturePlate","24-well-plate","B1")'
  )
  feedVolume = 900
  extraRemoval = 15
  aliquotvol = 20
  resuspvol = 800
  fullVolume = 1000
else:
  raise Exception('Undefined plate class?')
cur = db.execute(
    'select * FROM Cultures INNER JOIN PlatePositions ON Cultures.CultureID = PlatePositions.CultureID INNER JOIN Plates ON PlatePositions.PlateID=Plates.PlateID  WHERE Plates.PlateID=? AND (PlatePositions.Status IS NULL OR PlatePositions.Status != 10) ORDER BY Column, Row',
    [request.form['plateid']])
cultures = cur.fetchall()
tipnumber = 0
email(
    'email@example.com',
    'Started processing a new plate with command: ' + request.form['manual'])
if request.form['manual'] == 'split':
  cur = db.execute(
      'SELECT *, PlatePositions.Row AS Row, PlatePositions.Column AS Column FROM Cultures INNER JOIN PlatePositions ON Cultures.CultureID = PlatePositions.CultureID INNER JOIN Plates ON Plates.PlateID=PlatePositions.PlateID AND Plates.PlatePurpose=1 INNER JOIN ( SELECT MAX(timeSampled),* FROM Measurements INNER JOIN PlatePositions ON PlatePositions.Row=Measurements.Row AND PlatePositions.Column=Measurements.Column AND PlatePositions.PlateID = Measurements.PlateID GROUP BY CultureID ) latestparasitaemia ON Cultures.CultureID=latestparasitaemia.CultureID WHERE PlatePositions.PlateID = ?',
      [request.form['plateid']])
  splitcultures = cur.fetchall()
  splitcultures = calcExpectedParasitaemas(splitcultures)
  desiredParasitaemia = float(request.form['parasitaemia'])
  if not (desiredParasitaemia > 0 and desiredParasitaemia < 101):
    return ('Error, enter reasonable parasitaemia')
  addback = []
  for culture in splitcultures:
    if culture['expectednow'] > desiredParasitaemia:
      factor = desiredParasitaemia / culture['expectednow']
      amountToRemove = (1 - factor) * fullVolume
      getTip(0)
      cur = resuspend(
          0,
          'CulturePlate',
          resuspvol,
          culture['Row'],
          culture['Column'],
          plateid=request.form['plateid'],
          double=True)
      cur = aspirate(
          0,
          'CulturePlate',
          amountToRemove,
          culture['Row'],
          culture['Column'],
          plateid=request.form['plateid'])
      airgap(0)
      dropTip(0)
      addback.append([
          amountToRemove, culture['Row'], culture['Column'],
          request.form['plateid'], factor
      ])
  getTip(0)
  resuspendReservoir(0, 'TubBlood')
  for item in addback:
    cur = aspirate(0, 'TubBlood', item[0])
    onexec = createOnExecute('split', request.form['plateid'], item[1],
                             item[2], item[4])
    cur = dispense(
        0, 'CulturePlate', item[0], item[1], item[2], onexec, plateid=item[3])
  dropTip(0)

elif request.form['manual'] == 'splittonewplate':
  cur = db.execute(
      'SELECT *, PlatePositions.Row AS Row, PlatePositions.Column AS Column FROM Cultures INNER JOIN PlatePositions ON Cultures.CultureID = PlatePositions.CultureID INNER JOIN Plates ON Plates.PlateID=PlatePositions.PlateID AND Plates.PlatePurpose=1 INNER JOIN ( SELECT MAX(timeSampled),* FROM Measurements INNER JOIN PlatePositions ON PlatePositions.Row=Measurements.Row AND PlatePositions.Column=Measurements.Column AND PlatePositions.PlateID = Measurements.PlateID GROUP BY CultureID ) latestparasitaemia ON Cultures.CultureID=latestparasitaemia.CultureID WHERE PlatePositions.PlateID = ?',
      [request.form['plateid']])
  splitcultures = cur.fetchall()
  splitcultures = calcExpectedParasitaemas(splitcultures)
  desiredParasitaemia = float(request.form['parasitaemia'])
  if not (desiredParasitaemia > 0 and desiredParasitaemia < 101):
    return ('Error, enter reasonable parasitaemia')
  addback = []
  getTip(0)
  resuspendReservoir(0, 'TubBlood')
  for culture in splitcultures:
    if culture['expectednow'] > desiredParasitaemia:
      factor = desiredParasitaemia / culture['expectednow']
      amountToTransfer = (factor) * fullVolume
      amountOfNewBlood = (1 - factor) * fullVolume

      cur = aspirate(0, 'TubBlood', amountOfNewBlood)
      cur = dispense(
          0,
          'CulturePlate2',
          amountOfNewBlood,
          culture['Row'],
          culture['Column'],
          plateid=request.form['plateid'])

      addback.append([
          amountToTransfer, culture['Row'], culture['Column'],
          request.form['plateid'], factor
      ])
    else:
      factor = 1
      amountToTransfer = (factor) * fullVolume
      amountOfNewBlood = (1 - factor) * fullVolume
      addback.append([
          amountToTransfer, culture['Row'], culture['Column'],
          request.form['plateid'], factor
      ])
  dropTip(0)
  for item in addback:
    getTip(0)
    cur = resuspend(
        0, 'CulturePlate', item[0], item[1], item[2], plateid=item[3])
    cur = aspirate(
        0, 'CulturePlate', item[0], item[1], item[2], plateid=item[3])
    onexec = createOnExecute('split', request.form['plateid'], culture['Row'],
                             culture['Column'], item[4])
    cur = dispense(
        0,
        'CulturePlate2',
        item[0],
        item[1],
        item[2],
        onexec,
        plateid=item[3],
        bottom=True)
    dropTip(0)
elif request.form['manual'] == 'dilutenewplate':

  desiredParasitaemia = float(request.form['parasitaemia'])
  if not (desiredParasitaemia > 0 and desiredParasitaemia < 101):
    return ('Error, enter reasonable parasitaemia')
  addback = []
  getTip(0)
  resuspendReservoir(0, 'TubBlood')
  for culture in cultures:

    if 100 > desiredParasitaemia:
      factor = desiredParasitaemia / 100
      amountToTransfer = (factor) * fullVolume
      amountOfNewBlood = (1 - factor) * fullVolume

      cur = aspirate(0, 'TubBlood', amountOfNewBlood)
      cur = dispense(
          0,
          'CulturePlate2',
          amountOfNewBlood,
          culture['Row'],
          culture['Column'],
          plateid=request.form['plateid'])

      addback.append([
          amountToTransfer, culture['Row'], culture['Column'],
          request.form['plateid'], factor
      ])
    else:
      factor = 1
      amountToTransfer = (factor) * fullVolume
      amountOfNewBlood = (1 - factor) * fullVolume
      addback.append([
          amountToTransfer, culture['Row'], culture['Column'],
          request.form['plateid'], factor
      ])
  dropTip(0)
  for item in addback:
    getTip(0)
    cur = resuspend(
        0, 'CulturePlate', item[0], item[1], item[2], plateid=item[3])
    cur = aspirate(
        0, 'CulturePlate', item[0], item[1], item[2], plateid=item[3])
    onexec = createOnExecute('split', request.form['plateid'], culture['Row'],
                             culture['Column'], item[4])
    cur = dispense(
        0,
        'CulturePlate2',
        item[0],
        item[1],
        item[2],
        onexec,
        plateid=item[3],
        bottom=True)
    dropTip(0)

elif request.form['manual'] == 'dispense-sybr-green':
  getTip(0)
  curvol = 0
  for x in range(8):
    for y in range(6):
      if curvol < 200:
        cur = aspirate(0, 'TubSybr', 1000)
        curvol = 1000
      cur = dispense(0, 'AliquotPlate', 200, x, y)
      curvol = curvol - 200
  dropTip(0)
elif request.form['manual'] == 'dispense-sybr-green2':
  getTip(1)

  for x in range(4):
    cur = aspirate(1, 'TubSybr', 200)
    cur = dispense(1, 'AliquotPlate', 200, 0, x)
  dropTip(1)

elif request.form['manual'] == 'feed':
  if platestats['PlateClass'] == 1:
    for culture in cultures:
      getTip(0)
      cur = aspirate(
          0,
          'CulturePlate',
          feedVolume + extraRemoval,
          culture['Row'],
          culture['Column'],
          plateid=request.form['plateid'])
      # cur = db.execute('INSERT INTO CommandQueue (Command, Volume, Labware) VALUES ("Dispense",?,"Trash")',[feedVolume+extraRemoval])
      dropTip(0)
    getTip(0)
    for culture in cultures:

      cur = aspirate(0, 'TubMedia', feedVolume)
      onexec = createOnExecute('feed', request.form['plateid'],
                               culture['Row'], culture['Column'])
      cur = dispense(
          0,
          'CulturePlate',
          feedVolume,
          culture['Row'],
          culture['Column'],
          onexec,
          plateid=request.form['plateid'])

    dropTip(0)
    cur = db.execute('INSERT INTO CommandQueue (Command) VALUES ("Home")')
  elif platestats['PlateClass'] == 0:
    rows = {}
    for culture in cultures:
      row = culture['Column']
      rows[row] = 1
    rows = rows.keys()
    for row in rows:
      getTip(1)
      cur = aspirate(1, 'CulturePlate96', feedVolume, 0, row)
      cur = dispense(1, 'trash', feedVolume)
      dropTip(1)
    getTip(1)
    for row in rows:
      cur = aspirate(1, 'TubMedia', feedVolume)
      cur = dispense(1, 'CulturePlate96', feedVolume, 0, row)
    dropTip(1)
    cur = db.execute('INSERT INTO CommandQueue (Command) VALUES ("Home")')
elif request.form['manual'] == 'dispenseXtoall':
  if platestats['PlateClass'] == 1:
    getTip(0)
    for culture in cultures:
      feedVolume = request.form['parasitaemia']
      cur = aspirate(0, 'TubMedia', feedVolume)
      onexec = createOnExecute('feed', request.form['plateid'],
                               culture['Row'], culture['Column'])
      cur = dispense(
          0,
          'CulturePlate',
          feedVolume,
          culture['Row'],
          culture['Column'],
          onexec,
          plateid=request.form['plateid'])

    dropTip(0)
    cur = db.execute('INSERT INTO CommandQueue (Command) VALUES ("Home")')
elif request.form['manual'] == 'feedandaliquot' or request.form[
    'manual'] == 'justaliquot':
  cur = db.execute(
      'INSERT INTO CommandQueue (Command, Labware, LabwareType,Slot) VALUES ("InitaliseLabware","AliquotPlate","96-flat","C1")'
  )
  alwells = []
  culwells = []
  for culture in cultures:
    (alplate, alrow, alcol) = getNextMeasurementWell()
    alwells.append([alplate, alrow, alcol])
    culwells.append([culture['Row'], culture['Column'], culture['CultureID']])
  generateMultiDispense('TubSybr', alwells)
  for i in range(len(culwells)):
    culwell = culwells[i]
    (alplate, alrow, alcol) = alwells[i]
    getTip(0)
    if request.form['manual'] == 'feedandaliquot':
      cur = aspirate(0, 'CulturePlate', feedVolume + extraRemoval, culwell[0],
                     culwell[1], request.form['plateid'])
      airgap(0)
      dropTip(0)
      getTip(0)
      cur = aspirate(0, 'TubMedia', feedVolume)
      onexec = createOnExecute('feed', request.form['plateid'], culwell[0],
                               culwell[1])
      cur = dispense(
          0,
          'CulturePlate',
          feedVolume,
          culwell[0],
          culwell[1],
          onexec,
          plateid=request.form['plateid'],
          bottom=True)
    cur = resuspend(
        0,
        'CulturePlate',
        resuspvol,
        culwell[0],
        culwell[1],
        plateid=request.form['plateid'])
    cur = aspirate(
        0,
        'CulturePlate',
        aliquotvol,
        culwell[0],
        culwell[1],
        plateid=request.form['plateid'])

    if (alplate == -1):
      flash('Please add a new measurement plate')
      return redirect(url_for('show_plates'))
    onexecute = ('INSERT INTO PlatePositions '
                 '(PlateID,Row,Column,CultureID,timeSampled) VALUES ('
                ) + str(alplate) + ',' + str(alrow) + ',' + str(
                    alcol) + ',' + str(culwell[2]) + ',' + '<time>)'
    cur = dispense(
        0,
        'AliquotPlate',
        aliquotvol,
        alrow,
        alcol,
        onexecute,
        alplate,
        bottom=True)
    cur = aspirate(0, 'AliquotPlate', 100, alrow, alcol, plateid=alplate)
    cur = dispense(
        0, 'AliquotPlate', 100, alrow, alcol, plateid=alplate, bottom=True)
    airgap(0)
    dropTip(0)
  cur = db.execute('INSERT INTO CommandQueue (Command) VALUES ("Home")')
elif request.form['manual'] == 'feedandkeepx':
  propToKeep = float(request.form['parasitaemia'])
  if not (propToKeep > 0 and propToKeep < 101):
    return ('Error, enter reasonable value for X')
  amountToRemove = 1000 * (1 - propToKeep / 100)

  cur = db.execute(
      'INSERT INTO CommandQueue (Command, Labware, LabwareType,Slot) VALUES ("InitaliseLabware","AliquotPlate","96-flat","C1")'
  )
  for culture in cultures:
    getTip(0)
    cur = aspirate(
        0,
        'CulturePlate',
        feedVolume + extraRemoval,
        culture['Row'],
        culture['Column'],
        plateid=request.form['plateid'])
    airgap(0)
    dropTip(0)
    getTip(0)
    cur = aspirate(0, 'TubMedia', feedVolume)
    cur = dispense(
        0,
        'CulturePlate',
        feedVolume,
        culture['Row'],
        culture['Column'],
        plateid=request.form['plateid'],
        bottom=True)
    cur = resuspend(
        0,
        'CulturePlate',
        resuspvol,
        culture['Row'],
        culture['Column'],
        plateid=request.form['plateid'])
    cur = aspirate(
        0,
        'CulturePlate',
        amountToRemove,
        culture['Row'],
        culture['Column'],
        plateid=request.form['plateid'])
    airgap(0)
    dropTip(0)
  getTip(0)

  resuspendReservoir(0, 'TubBlood')
  vol = 0
  for culture in cultures:
    if vol < amountToRemove:
      cur = aspirate(0, 'TubBlood', 1000 - vol)
      vol = 1000
    cur = dispense(
        0,
        'CulturePlate',
        amountToRemove,
        culture['Row'],
        culture['Column'],
        plateid=request.form['plateid'])
    vol = vol - amountToRemove

  dropTip(0)
  cur = db.execute('INSERT INTO CommandQueue (Command) VALUES ("Home")')
elif request.form['manual'] == 'feedanddiscard50':
  cur = aspirate(0, 'TubMedia', 1500)
  cur = db.execute(
      'INSERT INTO CommandQueue (Command, Labware, LabwareType,Slot) VALUES ("InitaliseLabware","AliquotPlate","96-flat","C1")'
  )
  for culture in cultures:
    getTip(0)
    cur = aspirate(
        0,
        'CulturePlate',
        feedVolume + extraRemoval,
        culture['Row'],
        culture['Column'],
        plateid=request.form['plateid'])
    airgap(0)
    dropTip(0)
    getTip(0)
    cur = aspirate(0, 'TubMedia', feedVolume)
    cur = dispense(
        0,
        'CulturePlate',
        feedVolume,
        culture['Row'],
        culture['Column'],
        plateid=request.form['plateid'],
        bottom=True)
    cur = resuspend(
        0,
        'CulturePlate',
        resuspvol,
        culture['Row'],
        culture['Column'],
        plateid=request.form['plateid'])
    cur = aspirate(
        0,
        'CulturePlate',
        500,
        culture['Row'],
        culture['Column'],
        plateid=request.form['plateid'])
    airgap(0)
    dropTip(0)
  getTip(0)
  vol = 0
  for culture in cultures:
    if vol == 0:
      cur = aspirate(0, 'TubBlood', 1000)
      vol = 1000
    cur = dispense(
        0,
        'CulturePlate',
        500,
        culture['Row'],
        culture['Column'],
        plateid=request.form['plateid'])
    vol = vol - 1000

  dropTip(0)

elif request.form['manual'] == 'auto':
  print('pph')
else:
  raise Exception('Neither manual nor auto chosen')
email(request.form['email'], 'Processing of plate complete')
home()
db.commit()
return redirect(url_for('view_refreshed'))
