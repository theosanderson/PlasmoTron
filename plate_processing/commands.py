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
  def command_queue_is_empty(self):
    cur = self.db.execute('SELECT * FROM CommandQueue WHERE doneAt IS NULL')
      return cur.fetchone() is None
    
  def getTip(self,pipette):
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

  def dropTip(self,pipette):
    self.db.execute(
        'INSERT INTO CommandQueue (Command, Pipette, Labware) VALUES ("DropTip",?,"trash")',
        [pipettenames[pipette]])

  def email(self,email, message):
    self.db.execute(
        'INSERT INTO CommandQueue (Command,email, message) VALUES (?,?,?)',
        ['Email', email, message])

  def aspirate(self,pipette, labware, volume, row=None, col=None, plateid=None):
    self.db.execute(
        'INSERT INTO CommandQueue (Command, Pipette, Volume, Labware, Row, Column, PlateID) VALUES ("Aspirate",?,?,?,?,?,?)',
        [pipettenames[pipette], volume, labware, row, col, plateid])

  def dispense(self,pipette,
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

  def resuspendReservoir(self,pipette, labware):
    self.db.execute(
        'INSERT INTO CommandQueue (Command, Pipette,  Labware) VALUES (?,?,?)',
        ['ResuspendReservoir', pipettenames[pipette], labware])

  def resuspend(self,pipette,
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

  def airgap(self,pipette):
    self.db.execute(
        'INSERT INTO CommandQueue (Command, Pipette) VALUES ("AirGap",?)',
        [pipettenames[pipette]])

  def home(self,):
    self.dropTip(0)
    self.dropTip(1)
    self.db.execute('INSERT INTO CommandQueue (Command) VALUES (?)', ['Home'])
    
  def generateMultiDispense(self,source, destwells):

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
  def getNextMeasurementWell(self):
    nonlocal MeasurementAvailableWells
    nonlocal MeasurementPlate
    if (len(MeasurementAvailableWells) == 0):
      cur = self.db.execute(
          'SELECT * FROM Plates WHERE PlatePurpose=2 AND PlateFinished=0')
      plates = cur.fetchall()
      for one in plates:
        MeasurementPlate = one['PlateID']
        MeasurementAvailableWells = []
        for y in range(12):
          for x in range(8):
            MeasurementAvailableWells.append((x, y))

        cur2 = self.db.execute('SELECT * FROM PlatePositions WHERE PlateID=?',
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
  def createOnExecute(self,action, plateid, platerow, platecol, actionValue=None):
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
  def get_cultures(self):
    cur = self.db.execute(
      'select * FROM Cultures INNER JOIN PlatePositions ON Cultures.CultureID = PlatePositions.CultureID INNER JOIN Plates ON PlatePositions.PlateID=Plates.PlateID  WHERE Plates.PlateID=? AND (PlatePositions.Status IS NULL OR PlatePositions.Status != 10) ORDER BY Column, Row',
      [request.form['plateid']])
    return(cur.fetchall())

