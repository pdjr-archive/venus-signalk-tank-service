# venus-signalk-tank-service

__venus-signalk-tank-service__ represents Signal K tanks as Venus
tank services, enabling, amongst other things, their display on the
Venus GUI.

This is useful because it provides a work-around for Venus' broken
native support for CAN connected multi-channel tank sensor devices
like the Maretron FPM100 and the Garnet SeeLevel.

Although designed to address Venus' problem with multi-channel tank
sensors, the project will, of course, inject any Signal K tank data
into Venus and so make it available to devices like the CCGX.

![CCGX tank display](venus.png)

## Overview

__venus-signalk-tank-service__ recovers tank data from a specified
Signal K server over HTTP and generates one Venus service for each
reported tank.
The Signal K server can, of course, be running on a remote computer
or on the local Venus host.

The Venus GUI can be tweaked to prevent display of tank data deriving
from the now redundant 'socketcan' services.

Some GUI enhancements derived from the work of Kevin Windrem can be
applied to enable a more functional display of tank data than is
possible with the stock Venus GUI.
These enhancements are available for Venus devices which retain default
Victron installation hostnames of 'ccgx' and 'einstein': if your device
has a different hostname then you will need to provide a soft link in
the project 'gui' directory which maps your hostname to either 'ccgx'
or 'einstein'. 

### Installation

1. Make sure that you have enabled root access to your Venus device.
   
2. Install __venus-signalk-tank-service__ by logging into your Venus
   device and issuing the following commands.
   ```
   $> cd /data
   $> wget wget https://github.com/preeve9534/venus-signalk-tank-service/archive/main.tar.gz
   $> tar -xzf main.tar.gz
   $> rm main.tar.gz
   $> cd venus-signalk-tank-service-main
   ```

3. Open ```signalktank.py``` in a text editor and change the
   values of SIGNALK_SERVER and SIGNALK_TANKS to suit your needs.

   SIGNALK_SERVER specifies the hostname/IP-address and port
   number of your Signal K server.
   Use ```SIGNALK_SERVER = '127.0.0.1:3000'``` if Signal K is
   running on its default port on the Venus host.
   
   SIGNALK_TANKS specifies which tanks on SIGNALK_SERVER should
   be maintained as Venus services.
   Setting ```SIGNALK_TANKS = []``` will cause all the tanks
   available on SIGNALK_SERVER to be automatically processed.
   
   If you want to process just some tanks then you must specify the
   tanks you want to process. For example:
   ```
   SIGNALK_TANKS = [
        { 'path': 'tanks/wasteWater/0' },
        { 'path': 'tanks/freshWater/1' },
        { 'path': 'tanks/freshWater/2' },
        { 'path': 'tanks/fuel/3' },
        { 'path': 'tanks/fuel/4' }
   ]
   ```
   
   Use the *path* string property to specify the self-relative Signal K
   path of each tank for which you wish to create a Venus service.
   
4. Run ```signalktank.py``` and check that it outputs details of the
   tanks it is configuring.
   My system has five tanks and I see:
   ```
   $> ./signalktank.py 
   INFO:root:registered ourselves on D-Bus as com.victronenergy.tank.signalk_192_168_1_2_3000_5_0
   INFO:root:registered ourselves on D-Bus as com.victronenergy.tank.signalk_192_168_1_2_3000_1_1
   INFO:root:registered ourselves on D-Bus as com.victronenergy.tank.signalk_192_168_1_2_3000_1_2
   INFO:root:registered ourselves on D-Bus as com.victronenergy.tank.signalk_192_168_1_2_3000_0_3
   INFO:root:registered ourselves on D-Bus as com.victronenergy.tank.signalk_192_168_1_2_3000_0_4
   ```
   If the output isn't what you expect, then check that the tank data
   is actually available in Signal K and make sure that the values you
   supplied for SIGNALK_SERVER and SIGNALK_TANKS are correct.

6. Terminate ```signalktank.py``` and run ```setup``` to review and
   confirm some trivial system modifications designed to tweak the
   Venus GUI interface and make ```signalktank.py``` execute
   automatically when Venus boots.
   All the actions taken by setup are reversible.
   ```
   ^C
   $> ./setup
   ...
   ```
   
7. Finally, reboot Venus.
   ```
   $> reboot
   ```

## Acknowledgements

Thanks to Kevin Windrem for making this a whole lot easier than it
might have been by reworking the Venus GUI mobile interface so
nicely and in such a way that others can leverage it.

Thanks to @mvader at Victron for being honest about the likelihood of a
manufacturer fix for Venus' problem with multi-channel tank sensors and
so motivating me (after four years of complaining!) to take a different
approach to getting tank data on my CCGX.

## Author

Paul Reeve \<<preeve@pdjr.eu>\>
