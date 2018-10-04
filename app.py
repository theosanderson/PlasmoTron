# all the imports
from __future__ import print_function
import os
import sqlite3
import time
import sys
import datetime
import re
import subprocess
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
import sys
import atexit
from operator import itemgetter
import string

ALLOWED_EXTENSIONS = set(['csv'])


def eprint(*args, **kwargs):
  print(*args, file=sys.stderr, **kwargs)


app = Flask(__name__)  # create the application instance :)
app.config.from_object(__name__)  # load config from this file
queueProcessor = 'beginning'
#this is used so that the system knows the queue processor script has not been started yet.

InitCommand = 0  #Hacky variable  so that we don't try to kill the queue-processor when initialise the database, creating an error message which would scare users

# Database configuration
app.config.update(
    dict(
        DATABASE=os.path.join(app.root_path, 'plasmotron.db'),
        SECRET_KEY='development key',
        USERNAME='admin',
        PASSWORD='default',
        DEBUG=True))
app.config.from_envvar('PLASMOTRON_SETTINGS', silent=True)

# local instance configuration: if a file
# local_config.cfg exists, it is read. This can be
# used to set the instance name for example
localConfigFilePath="local_config.cfg"
if os.path.isfile( localConfigFilePath ):
  app.config.from_pyfile('local_config.cfg')

numberstoletters = dict(enumerate(string.ascii_uppercase,
                                  1))  #Used in function below


def reverseRowColumn(cell):
  #This function generates rows and columns from a reference like "A5" , "B8"
  cell = cell.lower()

  # generate matched object via regex (groups grouped by parentheses)
  ############################################################################
  # [a-z] matches a character that is a lower-case letter
  # [0-9] matches a character that is a number
  # The + means there must be at least one and repeats for the character it matches
  # the parentheses group the objects (useful with .group())
  m = re.match('([a-z]+)([0-9]+)', cell)

  # if m is None, then there was no match
  if m is None:
    # let's tell the user that there was no match because it was an invalid cell
    from sys import stderr
    print('Invalid cell: {}'.format(cell), file=stderr)
    return (None)
  else:
    # we have a valid cell!
    # let's grab the row and column from it

    var1 = 0

    # run through all of the characters in m.group(1) (the letter part)
    for ch in m.group(1):
      # ord('a') == 97, so ord(ch) - 96 == 1
      var1 += ord(ch) - 96
    var2 = int(m.group(2))
    row = var1 - 1
    col = var2 - 1
    return ((row, col))


def formatRowColumn(Row, Column):
  #This function generates "A1" from 0,0, etc.
  if Row == None:
    newrow = ''
  else:
    newrow = numberstoletters[Row + 1]
  if Column == None:
    newcol = ''
  else:
    newcol = Column + 1
  return (newrow + str(newcol))


def displayTime(timer):
  # This function generates a formatted time from a UNIX timestamp
  value = datetime.datetime.fromtimestamp(timer)
  return (value.strftime('%Y-%m-%d %H:%M:%S'))


def renderCellStyle(parasitaemia):
  # This function generates a colour value for cell backgrounds, proportional to parasitaemia (0-100)
  if parasitaemia is None:
    return ('')
  else:
    val = float(min([float(parasitaemia), 10])) / 10
    startr = 255
    startg = 255
    startb = 255
    endr = 255
    endg = 0
    endb = 0
    red = startr + val * (endr - startr)
    green = startg + val * (endg - startg)
    blue = startb + val * (endb - startb)
    style = 'background-color:rgb(' + str(int(red)) + ', ' + str(
        int(green)) + ', ' + str(int(blue)) + ')'
    return (style)


def renderParasitaemiaText(parasitaemia):
  #Generates a nicely formatted textual version of a parasitaemia (0-100)
  if parasitaemia is None:
    return ('')
  else:
    return ('(' + str(parasitaemia) + '%)')


#Load these helper functions:
app.jinja_env.globals.update(
    formatRowColumn=formatRowColumn,
    displayTime=displayTime,
    renderParasitaemiaText=renderParasitaemiaText,
    renderCellStyle=renderCellStyle)


def connect_db():
  """Connects to the specific database."""
  rv = sqlite3.connect(app.config['DATABASE'], timeout=30)
  #rv.execute('PRAGMA journal_mode=wal')
  rv.row_factory = sqlite3.Row
  return rv


def get_db():
  """Opens a new database connection if there is none yet for the

    current application context.
    """
  if not hasattr(g, 'sqlite_db'):
    g.sqlite_db = connect_db()
  return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
  """Closes the database again at the end of the request."""
  if hasattr(g, 'sqlite_db'):
    g.sqlite_db.close()


def init_db():
  global InitCommand
  InitCommand = 1
  db = get_db()
  with app.open_resource('model.mysql', mode='r') as f:
    db.cursor().executescript(f.read())
  db.commit()


@app.cli.command('initdb')
def initdb_command():
  """Initializes the database."""
  init_db()
  print('Initialized the database.')


@app.route('/')
def show_plates():
  db = get_db()
  cur = db.execute(
      'select Plates.PlateID, Plates.PlateName, COUNT(PlatePositions.Row) AS count, PlatePurpose, PlateFinished from Plates LEFT JOIN PlatePositions ON PlatePositions.PlateID=Plates.PlateID GROUP BY Plates.PlateID order by Plates.PlatePurpose, Plates.PlateID DESC'
  )
  entries = cur.fetchall()
  return render_template('showPlates.html', entries=entries)


def getMachineProperties():
  db = get_db()
  cur = db.execute('SELECT * FROM MachineStatusProperties')
  properties = {}
  entries = cur.fetchall()
  for entry in entries:
    properties[entry['name']] = entry['value']
  return (properties)


@app.route('/plate/<plateID>')
def show_plate(plateID):
  db = get_db()
  cur = db.execute(
      'select * FROM Plates INNER JOIN PlateClasses ON Plates.PlateClass= PlateClasses.PlateClassID WHERE PlateID= ?',
      [plateID])
  plate = cur.fetchone()
  #   cur = db.execute('select * FROM Cultures INNER JOIN PlatePositions ON Cultures.CultureID = PlatePositions.CultureID WHERE PlateID= ?',[plateID])
  if plate['PlatePurpose'] == 2:
    cur = db.execute(
        ' SELECT * FROM  PlatePositions LEFT JOIN Measurements ON PlatePositions.Row=Measurements.Row AND PlatePositions.Column=Measurements.Column AND PlatePositions.PlateID = Measurements.PlateID INNER JOIN Cultures ON Cultures.CultureID=PlatePositions.CultureID WHERE PlatePositions.PlateID= ?',
        [plateID])
  else:
    cur = db.execute(
        'SELECT * FROM Cultures INNER JOIN PlatePositions ON Cultures.CultureID = PlatePositions.CultureID INNER JOIN Plates ON Plates.PlateID=PlatePositions.PlateID AND Plates.PlatePurpose=1 LEFT JOIN ( SELECT MAX(timeSampled),* FROM Measurements INNER JOIN PlatePositions ON PlatePositions.Row=Measurements.Row AND PlatePositions.Column=Measurements.Column AND PlatePositions.PlateID = Measurements.PlateID GROUP BY CultureID ) latestparasitaemia ON Cultures.CultureID=latestparasitaemia.CultureID WHERE PlatePositions.PlateID= ?',
        [plateID])

  entries = cur.fetchall()
  dimx = plate['PlateRows']
  dimy = plate['PlateCols']

  rows = [[{'name': '', 'id': -1} for i in range(dimy)] for j in range(dimx)]
  for entry in entries:
    rows[entry['Row']][entry['Column']] = entry

  machineproperties = getMachineProperties()

  return render_template(
      'viewPlate.html',
      plate=plate,
      rows=rows,
      machineproperties=machineproperties)


@app.route('/culture/<cultureID>')
def show_culture(cultureID):
  db = get_db()

  cur = db.execute(
      'select * FROM Cultures INNER JOIN PlatePositions ON Cultures.CultureID = PlatePositions.CultureID INNER JOIN Plates ON PlatePositions.PlateID=Plates.PlateID  WHERE Plates.PlatePurpose=1 AND Cultures.CultureID= ?',
      [cultureID])
  culture = cur.fetchone()
  cur = db.execute(
      'select * FROM CommandQueue WHERE PlateID = ? AND Row = ? AND Column = ?',
      [culture['PlateID'], culture['Row'], culture['Column']])
  history = cur.fetchall()
  cur = db.execute(
      'select * FROM Actions WHERE PlateID = ? AND Row = ? AND Column = ?',
      [culture['PlateID'], culture['Row'], culture['Column']])
  actions = cur.fetchall()
  cur = db.execute(
      'select * FROM Cultures INNER JOIN PlatePositions ON Cultures.CultureID = PlatePositions.CultureID INNER JOIN Plates ON PlatePositions.PlateID=Plates.PlateID INNER JOIN Measurements ON Measurements.PlateID=Plates.PlateID AND Measurements.Row=PlatePositions.Row AND Measurements.Column=PlatePositions.Column  WHERE Plates.PlatePurpose=2 AND Cultures.CultureID= ?',
      [cultureID])
  measurements = cur.fetchall()
  return render_template(
      'viewCulture.html',
      culture=culture,
      history=history,
      actions=actions,
      measurements=measurements)


@app.route('/addculture', methods=['POST'])
def add_culture():

  db = get_db()
  cur = db.execute(
      'SELECT PlateRows,PlateCols FROM Plates INNER JOIN PlateClasses ON Plates.PlateClass= PlateClasses.PlateClassID WHERE PlateID= ?',
      [request.form['plateID']])
  platestats = cur.fetchone()
  cur = db.execute(
      'SELECT MAX(Column) AS maxCol FROM PlatePositions WHERE PlateID= ?',
      [request.form['plateID']])
  posresults = cur.fetchone()

  if posresults['maxCol'] is None:
    currentRow = -1
    currentCol = 0
  else:
    currentCol = posresults['maxCol']
    cur = db.execute(
        'SELECT MAX(Row) AS maxRow FROM PlatePositions WHERE PlateID= ? AND Column = ?',
        [request.form['plateID'], currentCol])
    posresults = cur.fetchone()
    currentRow = posresults['maxRow']

  currentRow = currentRow + 1
  if currentRow == platestats['PlateRows']:
    currentRow = 0
    currentCol = currentCol + 1
  if request.form['row'] is not '' and request.form['col'] is not '':
    currentRow = int(request.form['row'])
    currentCol = int(request.form['col'])
  if currentRow >= platestats['PlateRows'] or currentCol >= platestats[
      'PlateCols']:
    flash('Culture was attempted to be created outside bounds of plate')
    return redirect(url_for('show_plate', plateID=request.form['plateID']))
  if request.form['title'] == '':
    return ('Error: please enter a name for the culture')

  db.execute('insert into Cultures (CultureName) values (?)',
             [request.form['title']])
  db.execute(
      'insert into PlatePositions (CultureID,PlateID,Row,Column) values (last_insert_rowid(),?,?,?)',
      [request.form['plateID'], currentRow, currentCol])
  db.commit()
  flash('New culture successfully created and added to the plate')
  return redirect(url_for('show_plate', plateID=request.form['plateID']))


@app.route('/addplate', methods=['POST'])
def add_plate():

  db = get_db()
  title = request.form['title'].strip()
  if len(title) > 0:
    db.execute(
        'insert into Plates (PlateName,PlateClass,PlateFinished,PlatePurpose) values (?,?,0,1)',
        [request.form['title'], request.form['class']])
    db.commit()
    flash('New plate was successfully added')
  else:
    flash('Please enter a name for your plate.')

  return redirect(url_for('show_plates'))


@app.route('/addmanualaction', methods=['POST'])
def add_manual_action():

  timestamp = int(time.time())
  db = get_db()
  db.execute(
      'insert into Actions (PlateID,Row,Column,TypeOfOperation,ActionText,ActionTime) values (?,?,?,?,?,?)',
      [
          request.form['plateid'], request.form['row'], request.form['col'],
          'custom', request.form['text'], timestamp
      ])
  db.commit()
  flash('The action was successfully added')
  return redirect(url_for('show_culture', cultureID=request.form['cultureid']))

@app.route('/addmanualactionforchechcalib', methods=['POST'])
def add_manual_action_for_check_calib():

  doAction = request.form['doAction']
  usePipette = request.form['usePipette']
  useContainer = None
  if 'useContainer' in request.form and request.form['useContainer']:
    useContainer = request.form['useContainer']

  useRow = None
  if 'useRow' in request.form and request.form['useRow']:
    useRow = request.form['useRow']

  useCol = None
  if 'useCol' in request.form and request.form['useCol']:
    useCol = request.form['useCol']

  useVolume = None
  if 'useVolume' in request.form and request.form['useVolume']:
    useVolume = request.form['useVolume']

  db = get_db()
  db.execute(
      'insert into CommandQueue (Command,Pipette,Labware,Row,Column,Volume,queued) values (?,?,?,?,?,?,?)',
      [
          doAction, usePipette, useContainer, useRow,useCol,useVolume,1
      ])
  db.commit()
  return redirect(url_for('checkCalibration'))


@app.route('/processplate', methods=['POST'])
def process_plate():
  tipcounter = [int(request.form['tips1000']), int(request.form['tips200'])]
  maxtips = [96, 12]
  dimensions = [[12, 8], [12, 1]]
  pipettenames = ['p1000', 'p200x8']
  tipracks = ['p1000rack', 'p200rack']
  MeasurementPlate = None
  MeasurementAvailableWells = []

  def getTip(pipette):
    nonlocal tipcounter
    nonlocal db

    if tipcounter[pipette] == maxtips[pipette]:
      email(
          request.form['email'],
          "Please load more tips! <br> <img src='http://phenoplasm.org/sadtips.jpg'>"
      )
      cur = db.execute('INSERT INTO CommandQueue (Command) VALUES ("MoreTips")')
      tipcounter[pipette] = 0
    col, row = divmod(tipcounter[pipette], dimensions[pipette][1])
    onexecute = 'UPDATE MachineStatusProperties SET value = ' + str(
        tipcounter[pipette] +
        1) + ' WHERE name = "' + 'tipsusedpipette' + str(pipette) + '"'
    print(onexecute)
    cur = db.execute(
        'INSERT INTO CommandQueue (Command, Pipette, Labware, Row, Column, OnCompletion) VALUES ("GetTips",?,?,?,?,?)',
        [pipettenames[pipette], tipracks[pipette], row, col, onexecute])

    tipcounter[pipette] = tipcounter[pipette] + 1

  def dropTip(pipette):
    cur = db.execute(
        'INSERT INTO CommandQueue (Command, Pipette, Labware) VALUES ("DropTip",?,"trash")',
        [pipettenames[pipette]])

  def email(email, message):
    cur = db.execute(
        'INSERT INTO CommandQueue (Command,email, message) VALUES (?,?,?)',
        ['Email', email, message])

  def aspirate(pipette, labware, volume, row=None, col=None, plateid=None):
    cur = db.execute(
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
      cur = db.execute(
          'INSERT INTO CommandQueue (Command, Pipette, Volume, Labware, Row, Column,OnCompletion,PlateID) VALUES ("DispenseBottom",?,?,?,?,?,?,?)',
          [
              pipettenames[pipette], volume, labware, row, col, oncompletion,
              plateid
          ])
    else:
      cur = db.execute(
          'INSERT INTO CommandQueue (Command, Pipette, Volume, Labware, Row, Column,OnCompletion,PlateID) VALUES ("Dispense",?,?,?,?,?,?,?)',
          [
              pipettenames[pipette], volume, labware, row, col, oncompletion,
              plateid
          ])

  def resuspendReservoir(pipette, labware):
    cur = db.execute(
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
    cur = db.execute(
        'INSERT INTO CommandQueue (Command, Pipette, Volume, Labware, Row, Column,PlateID) VALUES (?,?,?,?,?,?,?)',
        [Command, pipettenames[pipette], volume, labware, row, col, plateid])

  def airgap(pipette):
    cur = db.execute(
        'INSERT INTO CommandQueue (Command, Pipette) VALUES ("AirGap",?)',
        [pipettenames[pipette]])

  def home():
    dropTip(0)
    dropTip(1)
    cur = db.execute('INSERT INTO CommandQueue (Command) VALUES (?)', ['Home'])

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

  def generateMultiDispense(source, destwells):

    curvol = 0
    getTip(0)
    for well in destwells:
      (plate, row, col) = well
      if curvol < 200:
        cur = aspirate(0, 'TubSybr', 1000)
        curvol = 1000
      cur = dispense(0, 'AliquotPlate', 200, row, col)
      curvol = curvol - 200
    airgap(0)
    dropTip(0)

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


@app.route('/queue')
@app.route('/queue/<history>')
def view_queue(history=0):
  if int(history) == 1:
    extra = ''
  else:
    extra = 'WHERE queued != -1'
  db = get_db()
  cur = db.execute('SELECT * FROM CommandQueue ' + extra)
  cur2 = db.execute(
      'SELECT SUM(Volume) AS totalvolume, Labware FROM CommandQueue WHERE queued != -1 AND Command = "Aspirate" GROUP BY Labware'
  )
  return render_template(
      'viewQueue.html', queue=cur.fetchall(), vols=cur2.fetchall())


@app.route('/refresh')
def view_refreshed():

  return render_template('raspberrypi.html')


@app.route('/justQueue')
def justQueue():
  db = get_db()
  cur = db.execute('SELECT * FROM TimeEstimates')
  estimates = cur.fetchall()
  estimatedict = {}
  for estimate in estimates:
    estimatedict[estimate['Command']] = estimate['TimeTaken']
  cur = db.execute('SELECT * FROM CommandQueue WHERE doneAt IS NULL')
  totalTimeLeft = 0
  commands = cur.fetchall()
  for command in commands:
    if command['Command'] in estimatedict:
      totalTimeLeft += estimatedict[command['Command']]
  output = None
  if queueProcessor == 'beginning':
    result = 'notstarted'
  else:
    poll = queueProcessor.poll()
    if poll == None:
      result = 'running'
    else:

      result = 'Crashed'
      #It would be nice to capture output and display it but this seems to involve threading..
  minutes, seconds = divmod(totalTimeLeft, 60)
  seconds = '%02d' % (int(seconds),)
  minutes = int(minutes)
  totalTimeLeft = '%s:%s' % (minutes, seconds)
  return render_template(
      'justQueue.html',
      queue=commands,
      status=result,
      totalTimeLeft=totalTimeLeft)


@app.route('/clearqueue', methods=['POST'])
def clearqueue():
  db = get_db()
  db.execute('DELETE FROM CommandQueue WHERE doneAt IS NULL')
  db.execute('UPDATE CommandQueue SET queued = -1')
  db.commit()
  flash('Queue cleared')
  return redirect(url_for('view_queue'))


@app.route('/archivePlatePosition', methods=['POST'])
def archivePlatePosition():
  db = get_db()
  db.execute(
      'UPDATE PlatePositions SET Status=10 WHERE  PlateID= ? AND Row = ? AND Column = ?',
      [request.form['plateid'], request.form['row'], request.form['col']])
  db.commit()
  flash('Culture archived')
  return redirect(url_for('show_plate', plateID=request.form['plateid']))


@app.route('/unarchivePlatePosition', methods=['POST'])
def unarchivePlatePosition():
  db = get_db()
  db.execute(
      'UPDATE PlatePositions SET Status=0 WHERE  PlateID= ? AND Row = ? AND Column = ?',
      [request.form['plateid'], request.form['row'], request.form['col']])
  db.commit()
  flash('Culture archived')
  return redirect(url_for('show_plate', plateID=request.form['plateid']))


@app.route('/deletePlatePosition', methods=['POST'])
def deletePlatePosition():
  db = get_db()
  db.execute(
      'DELETE FROM PlatePositions WHERE  PlateID= ? AND Row = ? AND Column = ?',
      [request.form['plateid'], request.form['row'], request.form['col']])
  db.commit()
  flash('Plate position deleted')
  return redirect(url_for('show_plate', plateID=request.form['plateid']))


@app.route('/pauseQueue', methods=['POST'])
def pausequeue():
  db = get_db()
  cur = db.execute('UPDATE CommandQueue SET queued=0 WHERE queued=1')
  db.commit()
  flash('Queue paused')
  return redirect(url_for('view_refreshed'))


@app.route('/runQueue', methods=['POST'])
def runqueue():
  db = get_db()
  cur = db.execute('UPDATE CommandQueue SET queued=1 WHERE queued=0')
  db.commit()
  flash('Queue started')
  return redirect(url_for('view_refreshed'))


@app.route('/createMeasurementPlate', methods=['POST'])
def createMeasurementPlate():
  db = get_db()
  cur = db.execute(
      'SELECT * FROM Plates WHERE PlatePurpose=2 ORDER BY PlateID DESC')
  latest = cur.fetchone()
  if latest == None:
    lastnum = 0
  else:

    lastname = latest['PlateName']
    lastnum = int(re.findall('\d+', lastname)[0])
  newnum = lastnum + 1
  db.execute(
      'insert into Plates (PlateName,PlateClass,PlateFinished,PlatePurpose) values (?,0,0,2)',
      ['MeasurementPlate' + str(newnum)])
  db.commit()
  flash('Measurement plate ' + str(newnum) + ' created')
  return redirect(url_for('show_plates'))


def allowed_file(filename):
  return '.' in filename and \
         filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/uploadReadings', methods=['POST'])
def uploadReadings():
  db = get_db()
  if request.method == 'POST':
    # check if the post request has the file part
    if 'file' not in request.files:
      flash('No CSV file')
      return redirect(url_for('show_plate', plateID=request.form['plateID']))
    file = request.files['file']
    # if user does not select file, browser also
    # submit a empty part without filename
    if file.filename == '':
      flash('No selected file')
      return redirect(url_for('show_plate', plateID=request.form['plateID']))
    if file and allowed_file(file.filename):
      measurements = 0
      text = file.read()
      for l in text.splitlines():
        mylist = str(l).split(',')
        name = mylist[0]
        mylist2 = name.split('-')
        location = mylist2[len(mylist2) - 1]
        # if there are only two columns, then column 2 will have the
        # measurements. If there are more than 5 then this is the old
        # format and measurements should be in column 8
        if len(mylist2) > 2:
          if len(mylist) == 2 :
            percent = mylist[1]
          elif len(mylist) > 7 :
            percent = mylist[7]

          if percent != '':
            percent = float(re.findall(r'[-+]?\d*\.\d+|\d+', percent)[0])
            (row, col) = reverseRowColumn(location)

            eprint('Location' + str(row) + ',' + str(col) + ',' + str(percent))
            try:
              db.execute(
                  'INSERT INTO Measurements (PlateID,Row,Column,MeasurementValue) values (?,?,?,?)',
                  [request.form['plateID'], row, col, percent])
            except sqlite3.IntegrityError:
              flash('ERROR: duplicated entries - these measurements have been uploaded previously')
              return redirect(url_for('show_plate', plateID=request.form['plateID']))
            except:
              flash('ERROR: Loading data into database failed. Please contact administrator.')
              return redirect(url_for('show_plate', plateID=request.form['plateID']))
            measurements = measurements + 1
      db.execute('UPDATE Plates SET PlateFinished=1 WHERE PlateID=?',
                 [request.form['plateID']])
      db.commit()
      flash(str(measurements) + ' measurements added.')

  return redirect(url_for('show_plate', plateID=request.form['plateID']))


@app.route('/clearReadings', methods=['POST'])
def clearReadings():
  db = get_db()
  cursor = db.execute('DELETE FROM Measurements WHERE PlateID = ?',
                      [request.form['plateID']])
  result = cursor.rowcount
  flash('Deleted ' + str(result) + ' measurements')
  db.commit()
  return redirect(url_for('show_plate', plateID=request.form['plateID']))


@app.route('/closeReadings', methods=['POST'])
def closeReadings():
  db = get_db()
  db.execute('UPDATE Plates SET PlateFinished=1 WHERE PlateID=?',
             [request.form['plateID']])
  flash('The plate has been closed to further readings')
  db.commit()
  return redirect(url_for('show_plate', plateID=request.form['plateID']))


@app.route('/uncloseReadings', methods=['POST'])
def uncloseReadings():
  db = get_db()
  db.execute('UPDATE Plates SET PlateFinished=0 WHERE PlateID=?',
             [request.form['plateID']])
  flash('The plate has been reopened to further readings')
  db.commit()
  return redirect(url_for('show_plate', plateID=request.form['plateID']))


@app.route('/deletePlate', methods=['POST'])
def deletePlate():
  db = get_db()
  cursor = db.execute('DELETE FROM Plates WHERE PlateID = ?',
                      [request.form['plateID']])
  result = cursor.rowcount
  flash('Deleted ' + str(result) + ' plate')
  db.commit()
  return redirect(url_for('show_plates'))


@app.route('/killQueueProcessor', methods=['POST'])
def killQueueProcessor():
  if not InitCommand:
    global queueProcessor
    if queueProcessor != 'beginning':
      pid = queueProcessor.pid
      queueProcessor.terminate()

      # Check if the process has really terminated & force kill if not.
      try:
        os.kill(pid, 0)
        queueProcessor.kill()
        flash('Forced kill')
      except OSError as e:
        flash('Terminated gracefully')

    return redirect(url_for('view_refreshed'))


@app.route('/restartQueueProcessor', methods=['POST'])
def restartQueueProcessor():
  global queueProcessor
  killQueueProcessor()
  if 'simulate' in request.form:
    queueProcessor = subprocess.Popen(
        ['python', 'queueprocessor.py', 'simulate'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
  else:
    queueProcessor = subprocess.Popen(
        ['python', 'queueprocessor.py', 'control'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
  flash('Restarted')
  return redirect(url_for('view_refreshed'))


def cleanup():
  killQueueProcessor()


def calcExpectedParasitaemas(sqlrows):
  newlist = []
  for row in sqlrows:
    d = dict(zip(row.keys(), row))
    timemeasured = d['timeSampled']
    timenow = time.time()

    if timemeasured is not None:
      timediff = timenow - timemeasured
      timediffhours = timediff / (60 * 60)
      timediffcycles = timediffhours / 27.5
      growthpercycle = 3.5
      expectednow = d['MeasurementValue'] * (growthpercycle**timediffcycles)
      d['expectednow'] = expectednow
      d['timediffhours'] = timediffhours
      newlist.append(d)
  return (newlist)


@app.route('/calcparasitaemia')
def calcpar():
  db = get_db()
  cur = db.execute(
      'SELECT * FROM Cultures INNER JOIN PlatePositions ON Cultures.CultureID = PlatePositions.CultureID INNER JOIN Plates ON Plates.PlateID=PlatePositions.PlateID AND Plates.PlatePurpose=1 INNER JOIN ( SELECT MAX(timeSampled),* FROM Measurements INNER JOIN PlatePositions ON PlatePositions.Row=Measurements.Row AND PlatePositions.Column=Measurements.Column AND PlatePositions.PlateID = Measurements.PlateID GROUP BY CultureID ) latestparasitaemia ON Cultures.CultureID=latestparasitaemia.CultureID'
  )
  entries = cur.fetchall()
  newlist = calcExpectedParasitaemas(entries)
  newlist = sorted(newlist, key=itemgetter('expectednow'), reverse=True)
  return render_template('calcParasitaemia.html', newlist=newlist)


@app.route('/UpdateCommandTimeEstimates')
def updatetime():
  """ This calculates the time taken to do each class of command on average, and stores these values in a new DB

     which are used for time estimation. It also displays some stats, just for
     fun!

    """

  db = get_db()
  cur = db.execute('DROP TABLE IF EXISTS TimeEstimates;')
  command = """
    CREATE TABLE TimeEstimates AS
    SELECT Command, AVG(timeTaken) AS TimeTaken ,COUNT(timeTaken) AS Count, SUM(Volume) AS totalVolume  FROM (SELECT 
    g2.Command,
    (g2.DoneAt - g1.DoneAt) AS timeTaken, g2.Volume AS Volume
FROM
    CommandQueue g1
        INNER JOIN
    CommandQueue g2 ON g2.CommandID = g1.CommandID + 1 )  WHERE timeTaken<90 GROUP BY Command
    """

  cur = db.execute('DROP TABLE IF EXISTS TimeEstimates;')
  cur = db.execute(command)
  cur = db.execute('SELECT * FROM TimeEstimates')
  return render_template('stats.html', results=cur.fetchall())


@app.route('/addPlateForm')
def addPlateForm():
  return render_template('newPlateForm.html')


@app.route('/checkCalibration')
def checkCalibration():
  db = get_db()
  return render_template('checkCalibration.html')

atexit.register(cleanup)

if __name__ == '__main__':
  app.debug = False
  app.run(host='0.0.0.0', port=5000)
