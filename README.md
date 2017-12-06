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

While PlasmoTron could be adapted to other robotic systems this will require a little work.

#### Server / robot handling computer

PlasmoTron is intended to run on a dedicated computer, which will control the robot and also host the web app and database that stores culture information. This computer needs to be near enough the robot to connect by USB. It should also be networked to the internet or an intranet so that users can access their culture information remotely. It is furthermore helpful if the computer can be directly controlled (mouse, keyboard, screen), especially in the event of a network outage. The computer does not need to be powerful.

The approach we ourselves use is to use a $40 Raspberry Pi computer, with an integrated touch screen, which is mounted to the tissue culture hood. The USB and power cables to the robot are run directly into the hood through the gasket seal (which we resealed with some Sugru). Many similar alternatives would be possible, including an i86 based tablet PC.


### Software

#### OpenTrons app
To calibrate the positions of labware on your robot you will need to install the [OpenTrons app](https://opentrons.com/ot-app) This is trivial for many systems. For a Raspberry Pi it is rather more complex as you will need to [install from source](https://github.com/Opentrons/opentrons), but this is beyond the scope of these instructions.

If you have gone down the Raspberry Pi touchscreen approach, you may want to [connect remotely over VNC](https://www.raspberrypi.org/documentation/remote-access/vnc/) for calibration to allow a larger screen size.

#### Dependencies

##### Python

Your environment should be set to use Python 3.6+, which is required for OpenTrons.
##### OpenTrons API
You need to install [the OpenTrons API](http://docs.opentrons.com/writing.html#jupyter-notebook) which provides a package to allow the use of the OpenTrons robot in arbitrary Python scripts.

```
pip install --upgrade opentrons 
```
##### Flask
[Flask](http://flask.pocoo.org/) is the lightweight web server on which PlasmoTron runs. It is a prerequisite for PlasmoTron. We have been using Flask 0.13-dev.

## Installation
```
git clone https://github.com/theosanderson/plasmotron.git
```
