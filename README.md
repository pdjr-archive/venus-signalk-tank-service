# venus-signalk-tank-service

__venus-signalk-tank-service__ implements a solution for displaying
tank data derived from multi-channel tank sensors like the Maretron
FPM100 and the Garnet SeeLevel on a Venus OS device like the Victron
CCGX.

## Background

Support for tank monitoring in Venus OS is fundamentally broken.
Inexplicably, Victron's low-level code ignores CAN/N2K tank instance
numbers, substituting them with the sensor device's own instance
number.
Since the Victron strategy is to associate each tank sensor with a
dbus service, the consequence is that data from multiple tanks appears
in Venus as a single dbus service.
In the absence of any tank instance numbers, disaggregation of the
composite data is at best problematic and for non-trivial tank
installations infeasible.

Even so, there have been a number of attempts at implementing fixes
and work-arounds in Venus, mostly relying on the spurious association
of fluid type and tank level which allows the disaggregation of the
composite data if one allows no more than one tank of any fluid type.
kwindrem's
("repeater")[https://github.com/kwindrem/SeeLevel-N2K-Victron-VenusOS]
project follows this approach by:

1. disaggregating the garbled data and creating one dbus service for
   each identified tank, and
2. tweaking the Venus GUI so that data from the new dbus services is
   displayed nicely and data from the garbled, original, service is
   ignored.

## This project

__venus-signalk-tank-service__ borrows kwindrem's GUI modifications,
ignores Venus' broken tank handling and instead recovers tank data
from a Signal K server, generates one dbus service per tank and in
so doing makes it available to Venus in a way that can be picked up
and rendered on a CCGX or similar display.

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
   first prompts with 'a' (Activate) and subsequent prompts with 'y'.
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
$> cd venus-signalk-tank-service
```

4. Open signalktankservice.py in a text editor and change the value
   of SIGNALK_SERVER and SIGNALK_TANKS to suit your needs.

5. Run signalktankservice.py and check that it outputs details of the
   tanks it is configuring. My system has five tanks and I see:
   ```
   $> ./signalktankservice.py 
   INFO:root:registered ourselves on D-Bus as com.victronenergy.tank.signalk_tank_0
   INFO:root:registered ourselves on D-Bus as com.victronenergy.tank.signalk_tank_1
   INFO:root:registered ourselves on D-Bus as com.victronenergy.tank.signalk_tank_2
   INFO:root:registered ourselves on D-Bus as com.victronenergy.tank.signalk_tank_3
   INFO:root:registered ourselves on D-Bus as com.victronenergy.tank.signalk_tank_4
   ```
   If the output isn't what you expect, then check the tank data
   available in Signal K and make sure that the values you supplied
   for SIGNALK_SERVER and SIGNALK_TANKS are correct.

6. With ```signalktankservice.py``` running you should see your
   configured tanks displaying on the Venus GUI.

7. Run ```setup``` to make ```signalktankservice.py``` execute
   automatically when Venus boots.



to the
   two questions relating to GUI changes.

2. 

#
# The code here uses the GUI enhancements implemented by kwindrem in
# the project mentioned above.
#
# 1. Install the GUI enhancements from kwindrem's project.
# 2. Copy this program into  
