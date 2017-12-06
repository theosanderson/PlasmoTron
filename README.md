# PlasmoTron
PlasmoTron is a robotic system built on top of the [OpenTrons](https://opentrons.com/) system, to allow semi-automated culture of malaria parasites.

[![PlasmoTron](https://img.youtube.com/vi/9Bxmd0nfG3E-Y/0.jpg)](https://www.youtube.com/watch?v=9Bxmd0nfG3E-Y "PlasmoTron")

Specifically PlasmoTron provides these features:
* a database to store information about all plates currently in culture, and where individual cultures are located on them
* a system to control an OpenTrons robot in order to feed these parasites, split them, and/or take an aliquot to measure parasitaemia by SYBR-green flow cytometry
* the ability to upload the results from a flow cytometer to the database and have them associated with each culture at a specific time.
* an intelligent system to use this parasitaemia data to decide how to split parasites

# Installation

## Pre-requisites

### A working copy of the OpenTrons app

To calibrate the labware to the robot you will to use the OpenTrons app. On a Raspberry Pi this means building from source, which we found relatively challenging. You will have an easier time on other systems, but with a less pleasing form factor. For us this was the most difficult part of the procedure. I gather a non-GUI based calibration system is in the works.

### Python

Your environment should be set up for Python 3.6+, which is required for OpenTrons.

### Flask

We have been using Flask 0.13-dev.

