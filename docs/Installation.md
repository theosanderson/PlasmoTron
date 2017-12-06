[Home](/) - Installation - [Deck setup and calibration](DeckSetupAndCalibration.md) - [PlasmoTron tutorial](DeckSetupAndCalibration.md) 


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

Now navigate to the PlasmoTron directory:

```
cd plasmotron
```

First we need to initialise the database:
```
flask initdb
```


## First test run
Now let's try running the app:
```
flask run
```
With a bit of luck you will see:
```
pi@raspberrypi:~/flask $ flask run
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
 ```

Which means the web server is now running.

Fire up your browser on the machine and go to http://127.0.0.1:5000/ Hopefully you will see something like this:
<p align="center">
<img src="docs/images/initialview.png" width="400"/></p>

If so, you should be all set in terms of installation.


