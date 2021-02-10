# venus-signalk-tank-service

__venus-signalk-tank-service__ implements a solution for displaying
tank data derived from multi-channel tank sensors like the Maretron
FPM100 and the Garnet SeeLevel on a Venus OS device like the Victron
CCGX.

## Background

Support for tank monitoring in Venus OS is fundamentally broken.
The low-level code implementing CAN/N2K tank data recovery assumes
one tank sensor device per physical tank and generates a dbus
tank service besed on this assumption.

For multi-channel tank sensor devices Venus discards individual
tank sensor instance numbers and consolidates data from all tank
sensors under the tank device instance number, leading to a single
dbus tank service delivering data from multiple tanks.

The absence of any tank sensor instance numbers means that
disaggregation of the composite data is at best problematic and, for
non-trivial tank installations, infeasible.

Even so, there have been a number of attempts at implementing fixes
and work-arounds in Venus.
Mostly these rely on the spurious association of fluid type and tank
level which only allows the disaggregation of the composite data if
one allows no more than one tank of any fluid type.
kwindrem's
[tank repeater](https://github.com/kwindrem/SeeLevel-N2K-Victron-VenusOS)
project follows this approach by:

1. disaggregating the garbled data and creating a dbus service for
   each unique fluid type, and
2. tweaking the Venus GUI so that data from the new dbus services is
   displayed nicely and data from the garbled, original, service is
   ignored.

## This project

__venus-signalk-tank-service__ borrows kwindrem's GUI modifications,
ignores Venus' broken tank handling, and instead recovers tank data
from a Signal K server, generating and updating one dbus service per
tank.
Once tha data is on dbus it becomes available to Venus in a way that
can be picked up and rendered on a CCGX or similar display.

Data is recovered from Signal K over HTTP and the Signal K server can
be running on the local network or even on the Venus host.

Pretty rendering of the tank data on a CCGX or whatever depends upon
kwindrem's GUI tweaks.

### Installation

1. If you are installing on a CCGX, make sure that root access is
   enabled.
   
2. Install kwindrem's repeater project by following his instructions
   at the above link.
   
   When you run the repeater project setup script, respond to the
   first prompt with 'a' (Activate) and subsequent prompts with 'y'.
   This will activate kwindrem's repeater (we don't need this) and
   install his GUI changes (we do need these).
   
   Run the repeater project setup script again, responding to the
   first prompt with 'd' (Disable) and subsequent prompts with 'y'.
   This will disable kwindrem's repeater, but leave his GUI changes
   in place.
   
3. Install __venus-signalk-tank-service__ by logging into your Venus
   device and issuing the following commands.
   ```
   $> cd /data
   $> wget wget https://github.com/preeve9534/venus-signalk-tank-service/archive/main.zip
   $> unzip main.zip
   $> rm main.zip
   $> cd venus-signalk-tank-service
   ```

4. Open ```signalktankservice.py``` in a text editor and change the
   values of SIGNALK_SERVER and SIGNALK_TANKS to suit your needs.

   SIGNALK_SERVER should specify the hostname/IP address and port
   number of your Signal K server.
   Use ```SIGNALK_SERVER = '127.0.0.1:3000'``` if Signal K is
   running on its defaultt port on the Venus host.
   
   If you set ```SIGNALK_TANKS = []``` then all the tanks available
   on SIGNALK_HOST will be automatically recovered.
   Alternatively, you can specify particular tanks via their 'self'
   relative Signal K path.
   For example:
   ```
   SIGNALK_TANKS = [
        { 'path': 'tanks/wasteWater/0' },
        { 'path': 'tanks/freshWater/1' },
        { 'path': 'tanks/freshWater/2' },
        { 'path': 'tanks/fuel/3' },
        { 'path': 'tanks/fuel/4' }
   ]
   ```

5. Run ```signalktankservice.py``` and check that it outputs details of
   the tanks it is configuring. My system has five tanks and I see:
   ```
   $> ./signalktankservice.py 
   INFO:root:registered ourselves on D-Bus as com.victronenergy.tank.signalk_tank_0
   INFO:root:registered ourselves on D-Bus as com.victronenergy.tank.signalk_tank_1
   INFO:root:registered ourselves on D-Bus as com.victronenergy.tank.signalk_tank_2
   INFO:root:registered ourselves on D-Bus as com.victronenergy.tank.signalk_tank_3
   INFO:root:registered ourselves on D-Bus as com.victronenergy.tank.signalk_tank_4
   ```
   If the output isn't what you expect, then check the tank data
   is actually available in Signal K and make sure that the values
   you supplied for SIGNALK_SERVER and SIGNALK_TANKS are correct.

6. With ```signalktankservice.py``` running you should see your
   configured tanks displaying on the Venus GUI.
   Stop the program using 'ctrl-C'.

7. Run ```setup``` to make ```signalktankservice.py``` execute
   automatically when Venus boots.
   ```
   $> ./setup
   ```
   Note that you will need to run ```setup``` again after a Venus OS update
   on a CCGX or other similar device.

## Acnowledgements

Thanks to kwindrem for making this a whole lot easier than it might have
been by designing his repeater software in a way which meant I could
leverage it.

Thanks to Vicron for finally saying 'don't expect [multi-channel] tank
support anytime soon' and motivating me to take a different approach to
getting tank data on my CCGX.
