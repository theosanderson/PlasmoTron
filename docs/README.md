# PlasmoTron
PlasmoTron is a robotic system built on top of the [OpenTrons](https://opentrons.com/) system, to allow semi-automated culture of malaria parasites.

[![PlasmoTron](https://img.youtube.com/vi/9Bxmd0nfG3E-Y/0.jpg)](https://www.youtube.com/watch?v=9Bxmd0nfG3E-Y "PlasmoTron")

Specifically PlasmoTron provides these features:
* a database to store information about all plates currently in culture, and where individual cultures are located on them
* a system to control an OpenTrons robot in order to feed these parasites, split them, and/or take an aliquot to measure parasitaemia by SYBR-green flow cytometry
* the ability to upload the results from a flow cytometer to the database and have them associated with each culture at a specific time.
* an intelligent system to use this parasitaemia data to decide how to split parasites

# Getting started
The documentation is divided into three sections:

* [Installation](docs/Installation.md) describes the pre-requisites and the set-up of both hardware and software.
* [Deck setup and calibration](docs/DeckSetupAndCalibration.md) describes the initial calibration procedures that are required to teach the robot where you will place your labware.
* The [PlasmoTron tutorial](docs/DeckSetupAndCalibration.md) will explain how, once this initial setup is complete, you can use PlasmoTron to maintain malaria parasites.



