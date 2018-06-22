[Home](/) - [Installation](Installation.md) - Deck setup and calibration - [PlasmoTron tutorial](Tutorial.md) 

## Deck set up and calibration

#Deck set-up

The deck layout is defined in `equipment.py` in the PlasmoTron folder.


<p align="center">
<img src="images/decklayout.png"/></p>

Let's have a look at one of those lines:

```{python}
equipment['TubMedia']=containers.load('epmotion30', "D1","TubMedia")
```
The bit on the left-hand-side defines that this is a new piece of equipment called `"TubMedia"`. That name is hardcoded into other parts of the programme so you don't want to change it. There are two parts you can safely change. One is the second argument of the load function, currently `"D1"` which specifies where on the deck the container is to be found. Feel free to change these values as you wish.

The other part we could change is `"epmotion30"`. This defines the type of container that is being used which determines its geometry.

OpenTrons has a whole lot of [built-in containers](http://docs.opentrons.com/containers.html). You can see them all [here](https://andysigler.github.io/ot-api-containerviz/). You can also add your own containers, which we did in this case at the top with:

```{python}
containers.create("24corning", grid=(4,6), spacing=(19.304,19.304), diameter=16.26,depth=18) #24-well plate
```

It is important that the deck layout section defines these key components:

* **Tipbox** Where the pipette goes to collect a new tip
* **Trash** This is defined as a point in space, which should be over your trash container (the bigger the better)
* **CulturePlate** This is the primary position where you will put a culture plate to be fed, or split.
* **AliquotPlate** This is where a 96-well measurement plate will be placed to collect aliquots of the culture for measurement.
* **CulturePlate2** Sometimes we want to split from one plate into another. This is the location we will put the second plate at. It can be the same position in the deck as the AliquotPlate
* **TubMedia**,**TubBlood**, **TubSybr** These are tubs where we will get the media, blood and SYBR-green respectively. We use EpMotion 30ml reservoirs for these, but you can customise as you want. (TubSybr actually isn't important if you are happy to pre-load your Sybr-Green plates without using the robot.)

This file can be left as it is or edited to suit your preferences.

#Small culture hoods
[To add section on transposed tip rack here]

#Calibration
Now we are ready to calibrate.

Close the PlasmoTron server and in a new terminal run:

```
source PlasmoTronPyEnv/bin/activate
cd PlasmoTron
python calibrate.py

```

If you have already practiced calibrating with the GUI app you will know what to do. Place the pipette in the bottom left well/tip of each container, and calibrate the plunger positions for the pipette.


Next up you can get to grips with PlasmoTron itself in the [tutorial](Tutorial.md).
