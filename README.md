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

initialview

If so, you should be all set in terms of installation.

## Deck set up and calibration

This Flask app is essentially a replacement for the OpenTrons interface. In regular use you will not need to use the OpenTrons app. However you do need to use the app one more time -- to set up the layout you will use for culture.

If you have already experimented with running some protocols in OpenTrons (which you really should have before starting this!) you will be aware of how to perform calibration. First lets check you are happy with the deck setup.

Using an editor of your choice, open queueprocess.py in the plasmotron directory.

Find the section where the deck layout is defined.

Let's have a look at one of those lines:

```{python}
equipment['TubMedia']=containers.load('epmotion30', "D1","TubMedia")
```
The bit on the left-hand-side defines that this is a new piece of equipment called "TubMedia". That name is hardcoded into other parts of the programme so you don't want to change it. There are two parts you can safely change. One is the first argument of the load function, which specifies the geometry of this container on the deck.

OpenTrons has a whole lot of [built-in containers](http://docs.opentrons.com/containers.html). You can see them all [here](https://andysigler.github.io/ot-api-containerviz/). You can also add your own as we did at the top with:

```{python}
containers.create("24corning",grid=(4,6),spacing=(19.304,19.304),diameter=16.26,depth=18) #24-well plate
```

Going back to the definition of TubMedia, the other part we can change is "D1". You can decide where on the deck you want any particular item to go. The key items are as follows:

* Tipbox Where the pipette goes to collect a new tip
* Trash This is defined as a point in space, which should be over your trash container (the bigger the better)
* CulturePlate This is the primary position where you will put a culture plate to be fed, or split.
* AliquotPlate This is where a 96-well measurement plate will be placed to collect aliquots of the culture for measurement.
* CulturePlate2 Sometimes we want to split from one plate into another. This is the location we will put the second plate at. It can be the same position in the deck as the AliquotPlate
* TubMedia,TubBlood, TubSybr These are tubs where we will get the media, blood and SYBR-green respectively. We use EpMotion 30ml reservoirs for these, but you can customise as you want.

Do edit this file to suit your preferences.

When you are done, save it.

Now we are ready to calibrate. Load up the OpenTrons app. Press *Click to upload* and navigate to the plasmotron directory. Open the queueprocessor.py file.

If any sort of error occurs you have probably introduced an error while modifying the Deck Setup. You may want to revert to the [original file](https://github.com/theosanderson/plasmotron/blob/master/queueprocessor.py) and slowly make changes until you find the source of the problem.

But hopefully no errors occur and you are presented with a screen something like this:

 calibration

Now proceed to calibrate as described in the [OpenTrons documentation](https://support.opentrons.com/getting-started/software-setup/calibrating-the-deck), until every item of equipment you need to use has a green tick. 

We're now ready to close the OpenTrons app and open up the web application. If the calibration is correct we will never need the OpenTrons app again.

### Create and populate your first plate

So once again it is
```
cd plasmotron
flask run
```

And send your browser to http://127.0.0.1:5000/

Note that if you have connected your device to the network you can also access this from a remote computer using http://[server's IP address here]:5000/

Regardless, you should get to

initialview

To start off click on *Create new culture plate*. 

Give your plate a name, and specify its geometry.

platecreation

Press Create plate and you will be returned to the home-page where you will see your first cultureplate listed.

step3

Click on the plate.

step4

Here you can see the current cultures on the plate (there aren't any!)

Add one by typing in a name and pressing add.

step5

There is our first culture. You can add more. You'll notice by default that the cultures are added sequentially going top-to-bottom and then left-to-right. But you can also place a culture wherever you want. Just click on a well and the next culture will be placed in that custom position instead.

step6

Now we have our first plate!

It is probably useful to actually physically set up this plate, or maybe to start with just some water (or food colouring) in a plate. Fill the same wells you have indicated with 1ml of liquid.







