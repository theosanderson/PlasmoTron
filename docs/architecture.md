# PlasmoTron architecture

PlasmoTron is designed to provide a simple interface that allows cultures of parasites in plates to be tracked, fed, measured and split. There are some "core philosophies" underpinning the design.

 - The user should not need to know what cultures are on their plates, and where they are in the wells of the plate
 - A full record should be kept of all operations performed on a culture without any need for user intervention
 - The application should be sufficiently modular to allow the potential for use with multiple robotic platforms

# The three component parts of PlasmoTron

## The database
At the heart of PlasmoTron is an SQL database. (Currently SQLite though MySQL or similar would be a better solution). The database schema is set-out in *model.sql* and summarised below.

|Table|Purpose  | Notes |
|--|--|--|
|Cultures|Stores a record of each culture.| At the moment the only properties Cultures have is a name, although in future they could have information on planned Drug selection, and other properties.|
|Plates|Stores a record of each microplate.| The idea is that these should be physical microplates. There is a bit of data for each plate: its name; its *class* which in this case means its geometry, 96 well or 24 well; its purpose, which is either culturing parasites or measuring parasitaemia; and whether it is in current use or archived.|
|PlatePositions|Each record links a *culture* to a specific well (*row* and *column*) on a specific *plate*| This records where cultures are on culture plates, and also where they have been aliquotted on measurement plates (a *timeSampled* field records when they were aliquotted).|
|Measurements|When a measurement plate is read on the flow cytometer, each well (*row* and *column*) of the measurement *plate* is assigned a measurement *value* in this table.| SQL can then be used to link these back to the cultures they represent.|
|CommandQueue|This table holds raw commands to the robot. These have little semantic meaning, they say things like "Aspirate 200ul from well A1" without further information.|Once a command is executed, the command's record is updated to record when it was executed. In addition, some commands have an *onExecute* string. This is an SQL command which is run on the database after completion. These commands are able to update other tables to provide semantic meaning - e.g. after taking an aliquot the onExecute command will add an entry to PlatePositions reflecting this aliquot.|
|Actions|This table records actions taken on cultures, with semantic meanings.| E.g. "feed" or "split"|
|PlateClasses|This is a basic lookup table which records geometries for each plate class||
|MachineStatusProperties|This is used to record basic properties that need to be persisted over time. |E.g. how many tips have been used of the current box.|

## The web application
The only way in which a user interacts with this database is via the PlasmoTron web app, which is written in the Flask framework and hosted directly from the server running the robot. This app does all of the heavy-lifting at present. For instance in the app you can click on a plate to see the cultures present on it. You can then use the interface to ask to "Feed" the plate. The app will populate the CommandQueue with the raw commands to the robot needed to carry out this action. 

## The queue-processor
So that the web-application can run alongside commands going to the robot, the actual control of the robot is carried out by a separate Python script, *queueprocessor.py* which is run as a subprocess by the web application. The intent is that this script should not need any "knowledge" of the broader set up of an experiment. It consists of a very simply loop:

 1. Check the CommandQueue table for any raw commands that have not yet been completed
 2. If there is a command, carry it out
 3. Once it is carried out, update the CommandQueue to report the time it was completed and then execute the *onExecute* string on the database.
 4. Repeat.