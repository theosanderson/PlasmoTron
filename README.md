# PlasmoTron
PlasmoTron is a robotic system built on top of the [OpenTrons](https://opentrons.com/) system, to allow semi-automated culture of malaria parasites.

[![PlasmoTron](https://img.youtube.com/vi/9Bxmd0nfG3E-Y/0.jpg)](https://www.youtube.com/watch?v=9Bxmd0nfG3E-Y "PlasmoTron")

Specifically PlasmoTron provides these features:
* a database to store information about all plates currently in culture, and where individual cultures are located on them
* a system to control an OpenTrons robot in order to feed these parasites, split them, and/or take an aliquot to measure parasitaemia by SYBR-green flow cytometry
* the ability to upload the results from a flow cytometer to the database and have them associated with each culture at a specific time.
* an intelligent system to use this parasitaemia data to decide how to split parasites

# Installation

## Prerequisites

### Suggested hardware

#### Liquid handler

We have an OT-One S Hood, sitting permanantly in a tissue culture hood. We would suggest that you get familar with calibrating and operating the OpenTrons robot using conventional protocols before you begin to try to establish PlasmoTron, because familiarity with how the robot works under the hood will be helpful.

#### Server / robot handling computer

PlasmoTron is intended to run on a dedicated computer, which will control the robot. This computer needs to be near enough the robot to connect by USB. It should also be networked to the internet or an intranet so that users can access their culture information remotely. It is furthermore helpful if the computer can be directly controlled (mouse, keyboard, screen), especially in the event of a network outage. The computer does not need to be powerful.

Our solution is to use a $40 Raspberry Pi computer, with an integrated touch screen, which is mounted to the tissue culture hood. The USB and power cables to the robot are run directly into the hood through the gasket seal (which we resealed with some Sugru). Many similar alternatives would be possible, including an i86 based tablet PC.


### A working OpenTrons robot in a tissue culture hood

To calibrate the labware to the robot you will to use the OpenTrons app. On a Raspberry Pi this means building from source, which we found relatively challenging. You will have an easier time on other systems, but with a less pleasing form factor. For us this was the most difficult part of the procedure. I gather a non-GUI based calibration system is in the works.

### Python

Your environment should be set up for Python 3.6+, which is required for OpenTrons.

### Flask

We have been using Flask 0.13-dev.

