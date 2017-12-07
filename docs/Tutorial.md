[Home](/) - [Installation](Installation.md) - [PlasmoTron tutorial](DeckSetupAndCalibration.md)  - [PlasmoTron tutorial](Tutorial.md) 

##

### Create and populate your first plate

So once again it is
```
cd plasmotron
flask run
```

And send your browser to http://127.0.0.1:5000/

Note that if you have connected your device to the network you can also access this from a remote computer at http://[server's IP address here]:5000/

Regardless, you should get to

<p align="center">
<img src="docs/images/initialview.png" width=500/></p>

To start off click on *Create new culture plate*. 

Give your plate a name ("tutorial plate"?), and specify its geometry (for this one use a 24-well).

<p align="center">
<img src="docs/images/platecreation.png" width=500/></p>

Press **Create plate** and you will be returned to the home-page where you will see your first cultureplate listed.

<p align="center">
<img src="docs/images/step3.png" width=500/></p>
 
Click on the plate. Here you can see the current cultures on the plate (there aren't any!)

<p align="center">
<img src="docs/images/step4.png" width=500/></p>



Add one by typing in a name and pressing add.

<p align="center">
<img src="docs/images/step5.png" width=500/></p>

There is our first culture. You can add more. You will notice by default that the cultures are added sequentially going top-to-bottom and then left-to-right. But you can also place a culture wherever you want - just click on a well before pressing *Add culture* and the next culture will be placed in that custom position instead.

<p align="center">
<img src="docs/images/step6.png" width=500/></p>

So we now have our first plate!

It is probably useful to actually physically set up this plate, so that you can carry out the next steps. Manually pipette 1 ml into each well of the plate that you indicated was filled.

Safety warning: use PlasmoTron entirely at your own risk. Robots, and biological material both pose hazards. The OpenTrons system does not have any interlocking device so do not approach the robot while it is operating. In this initial set up phase it would be prudent to use food-colouring instead of biological materials (culture) until you are confident that things are working as you intended.


### Feed your plate

Now we have a physical plate, and a virtual representation of it in the database. We're ready to use the robot to maintain our plate. Place the culture plate in the calibrated location on the deck. Also set up a full tip box (P1000 tips in this case), and your media reservoir.

When you go to the plate's page you will see options at the bottom to process the plate. Choose "Feed", by this we mean removing spent media and replacing with fresh media. You can now press "Plan plate processing".

The server will now calculate all of the commands it needs to send to the robot in order to feed the cultures on your plate. They are stored in a CommandQueue. You can see the current state of the queue at any point by pressing "Robot controller" in the top right hand corner.

First start the queue runner process by pressing "Start" on the right hand side. (The robot will home at this point.) Then Start the queue by pressing "Run queue on the left hand side". The robot should begin to move.

If anything goes wrong press Kill in the QueueRunner section. The fastest way to stop the robot is to disconnect its power supply.

### Measure your plate

Some days you will be content just to feed a plate, but other days you will want to assess its parasitaemia. In the PlasmoTron approach means taking a small aliquot of the culture into a separate 96 well plate that will be measured by flow cytometry (although adaptation to a SYBR-green assay or high-content microscopy are likely possible). 


[If you actually want to measure parasitaemia in this stage you will need to set up a fresh plate with parasites in the same wells, and let it settle.]


Again place your culture plate in the prime position. This time put a 96 well plate in the second plate position.

You need two reservoirs this time, one for SYBR-Green (premixed to 2X concentration in PBS) and one for media.

[Then make a new measurement plate and choose feed and aliquot]

The robot will dispense SYBR green across the measurement plate and then begin work on the culture plate.

The robot will remove spent media, replace with fresh media and then resuspend the mixture. It will then take 20ul of the mixture into the 96 well plate.











