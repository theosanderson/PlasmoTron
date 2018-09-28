[Home](/) - Installation - [Deck setup and calibration](DeckSetupAndCalibration.md) - [PlasmoTron tutorial](DeckSetupAndCalibration.md) 


## Prerequisites

### Hardware

#### Liquid handling robot

PlasmoTron is designed for use with OpenTrons OT One-S Hood, installed in a tissue culture hood. 

We would strongly suggest that you get familar with calibrating and operating the OpenTrons robot using conventional protocols before you try to establish PlasmoTron, because familiarity with how the robot works will be helpful. Follow the [full instructions](https://support.opentrons.com/ot-one/getting-started-hardware-setup/unboxing-the-ot-one), which you can do with a personal computer rather than the PlasmoTron-dedicated one.

While PlasmoTron could readily be adapted to other robotic systems (see FAQ) this will require a little work.

#### Computer to control robot and host server

PlasmoTron is intended to run on a dedicated computer, which will both control the robot and also host the web app and database that stores culture information. This computer needs to be near enough the robot to connect by USB. It should also be networked to the internet or an intranet so that users can access their culture information remotely. It may be helpful if the computer can be directly controlled from the tissue culture hood, especially in the event of a network outage. The computer does not need to be powerful.

The approach we initially used was to use a $40 Raspberry Pi computer, with an integrated touch screen, which was mounted to the outside of the tissue culture hood. The USB and power cables to the robot are run directly into the hood through the gasket seal. Many similar alternatives would be possible, including an i86-based tablet PC.

More recently (due only to requirements imposed by our IT department) we have used an alternative approach where a standard desktop without a screen controls the robot. An iPad mounted on the hood connects to this computer over the network for control, which takes place through the web browser.


### Software

#### Operating system
Linux and OSX both work. Theoretically Windows should work too but we haven't tried this.

#### OpenTrons app is no longer required
We have written a customised calibration script so you don't need the OpenTrons app

#### Example installation procedure

##### Pre-requisites

Make sure you have Python3 and `pip3` installed.

##### Create a Python virtual environment

It is probably a good idea to set up a virtual environment to hold all the stuff we need for this system.

```
pip3 install virtualenv
cd ~
python3 -m virtualenv PlasmoTronPyEnv
```


##### Activate the Python virtual environment


```
source PlasmoTronPyEnv/bin/activate
```

##### Install dependencies


```
pip3 install flask
pip3 install opentrons
```


## Installation of PlasmoTron
First clone the latest stable version from GitHub.
```
git clone https://github.com/theosanderson/PlasmoTron.git
```

Now navigate to the PlasmoTron directory:

```
cd PlasmoTron
```

First we need to initialise the database:

```
flask initdb
```


## First test run
Now let's try running the app:
```
python app.py
```
With a bit of luck you will see:
```
(PyEnv) plasmotron@deskpro110605:~/temp/PlasmoTron$ python app.py
 * Serving Flask app "app" (lazy loading)
 * Environment: production
   WARNING: Do not use the development server in a production environment.
   Use a production WSGI server instead.
 * Debug mode: off
 * Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)

 ```

Which means the web server is now running.

Fire up your browser on the machine and go to `http://127.0.0.1:5000/` Hopefully you will see something like this:
<p align="center">
<img src="images/initialview.png" width="400"/></p>

If so, you should be all set in terms of installation, though we still need to calibrate.


