# venus-signalk-tank-service

__venus-signalk-tank-service__ represents Signal K tanks as D-Bus
services, injecting tank data from Signal K into Venus OS and 
enabling its display on the Venus GUI.

This is useful because it provides a work-around for Venus' broken
native support for multi-channel CAN/N2K tank sensor devices like
the Maretron FPM100 and the Garnet SeeLevel.

Although designed to address Venus' problem with multi-channel tank
sensors, the project will, of course, inject any Signal K tank data
into Venus and so make it available to devices like the CCGX.

![CCGX tank display](venus.png)

## Background

Support for tank monitoring in Venus OS is fundamentally broken.
The low-level code implementing CAN/N2K tank data recovery assumes
one tank sensor device per physical tank and generates a D-Bus
tank service for each sensor device based on this false understanding.

Consequently, a tank service in Venus that represesents a multi-channel
tank sensor device is chaotically updated with data from all the tank
sensors that are connected to the multi-channel device resulting in a
GUI rendering of the data that is unintelligible.

Somewhere in this broken-ness Venus discards tank sensor instance
numbers making disaggregation of the garbled composite data at best
problematic and, for non-trivial tank installations, infeasible.

Even so, there have been a number of attempts at implementing fixes
and work-arounds in Venus based on the association of fluid type and
tank level: an assumption which holds only if an installation has a
single tank of each fluid type.

If you have a multi-channel tank sensor on CAN/N2K and you have only
one tank of each fluid type, then look at @kwindrem's
[tank repeater](https://github.com/kwindrem/SeeLevel-N2K-Victron-VenusOS)
project for a display fix that does not involve Signal K.

## This project

__venus-signalk-tank-service__ recovers tank data from a specified
Signal K server, generating and updating one D-Bus service per tank.

Data is recovered from Signal K over HTTP and the Signal K server can
be running remotely over ethernet or locally on the Venus host.

A number of tweaks are made to the Venus GUI mainly to disable the display
of tank data deriving from now redundant Venus CAN/N2K services.
Some of the changes made by @kwindrem are also applied because they enable
a more meaningful display of data from multiple tanks than the stock Venus
GUI.

### Installation

1. If you are installing on a CCGX, make sure that root access is
   enabled.
   
2. Install __venus-signalk-tank-service__ by logging into your Venus
   device and issuing the following commands.
   ```
   $> cd /data
   $> wget wget https://github.com/preeve9534/venus-signalk-tank-service/archive/main.tar.gz
   $> tar -xzf main.tar.gz
   $> rm main.tar.gz
   $> cd venus-signalk-tank-service-main
   ```

3. Open ```tankservice.py``` in a text editor and change the
   values of SIGNALK_SERVER and maybe SIGNALK_TANKS to suit your needs.

   SIGNALK_SERVER specifies the hostname/IP-address and port
   number of your Signal K server.
   Use ```SIGNALK_SERVER = '127.0.0.1:3000'``` if Signal K is
   running on its default port on the Venus host.
   
   SIGNALK_TANKS specifies which tanks on SIGNALK_SERVER should
   be maintained as Venus services.
   Setting ```SIGNALK_TANKS = []``` will cause all the tanks
   available on SIGNALK_SERVER to be automatically processed.
   
   If you want to process just some tanks or you want to adjust the
   value Signal K returns for tank capacity, then you must specify the
   tanks you want to process. For example:
   ```
   SIGNALK_TANKS = [
        { 'path': 'tanks/wasteWater/0', 'factor': 1000.0 },
        { 'path': 'tanks/freshWater/1' },
        { 'path': 'tanks/freshWater/2' },
        { 'path': 'tanks/fuel/3' },
        { 'path': 'tanks/fuel/4' }
   ]
   ```
   
   Use the *path* string property to specify the self-relative Signal K
   path of a tank to be processed and, optionally, specify a decimal
   *factor* property which will be applied as a multiplier to the capacity
   value returned by Signal K.
   This latter correction can be useful if a tank sensor has been
   configured in a way that does not return tank capacity in the litre
   units required by Venus.
   
4. Run ```tankservice.py``` and check that it outputs details of the tanks
   it is configuring. My system has five tanks and I see:
   ```
   $> ./signalktankservice.py 
   INFO:root:registered ourselves on D-Bus as com.victronenergy.tank.signalktank_192_168_1_2_3000_5_0
   INFO:root:registered ourselves on D-Bus as com.victronenergy.tank.signalktank_192_168_1_2_3000_1_1
   INFO:root:registered ourselves on D-Bus as com.victronenergy.tank.signalktank_192_168_1_2_3000_1_2
   INFO:root:registered ourselves on D-Bus as com.victronenergy.tank.signalktank_192_168_1_2_3000_0_3
   INFO:root:registered ourselves on D-Bus as com.victronenergy.tank.signalktank_192_168_1_2_3000_0_4
   ```
   If the output isn't what you expect, then check the tank data
   is actually available in Signal K and make sure that the values
   you supplied for SIGNALK_SERVER and SIGNALK_TANKS are correct.

5. With ```tankservice.py``` running you should see your configured tanks
   displaying on the Venus GUI.
   Note that if you have a faulty multi-channel tank sensor on your
   CAN/N2K bus then it will also show up at this point, but it should
   disappear at the next step!
   Stop the program using 'ctrl-C'.

6. Run ```setup``` to make ```tankservice.py``` execute automatically when
   Venus boots and to tweak @kwindrem's GUI files so that acknowledge our
   HIDE_PRODUCT_ID setting.
   ```
   $> ./setup
   ```
   This script adds a line to ```/data/rc.local``` (creating the file if it
   is absent).
   The change persists over OS updates.
   
9. Finally, reboot Venus.
   ```
   $> reboot
   ```

## Acknowledgements

Thanks to @kwindrem for making this a whole lot easier than it might have
been by designing his repeater software in a way which meant others could
leverage it.

Thanks to @mvader at Victron for being honest about the likelihood of a
manufacturer fix and and so motivating me (after four years of complaining!)
to take a different approach to getting tank data on my CCGX.

## Author

Paul Reeve \<<preeve@pdjr.eu>\>
