#!/usr/bin/env python

########################################################################
# Copyright 2021 Paul Reeve <preeve@pdjr.eu>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you
# may not use this file except in compliance with the License. You may
# obtain a copy of the License at
#
#	 http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

import gobject
import platform
import argparse
import logging
import sys
import os
import dbus
import httplib
import json

sys.path.insert(1, os.path.join(os.path.dirname(__file__), './ext/velib_python'))
from vedbus import VeDbusService
from settingsdevice import SettingsDevice

########################################################################
# START OF USER CONFIGURATION
########################################################################

# The Signal K server to poll for tank data.
#
SIGNALK_SERVER = '192.168.1.2:3000'

# The tanks to be processed (specify an empty array to process all
# tanks on SIGNALK_SERVER.
#
SIGNALK_TANKS = [
	{ 'path': 'tanks/wasteWater/0' },
	{ 'path': 'tanks/freshWater/1' },
	{ 'path': 'tanks/freshWater/2' },
	{ 'path': 'tanks/fuel/3' },
	{ 'path': 'tanks/fuel/4' }
]

# The frequency in ms at which to update tank data.
#
UPDATE_INTERVAL = 10000

########################################################################
# END OF USER CONFIGURATION
########################################################################

APPLICATION_SERVICE_NAME = 'signalk'
VERSION='1.2.0'

SIGNALK_SELF_PATH='/signalk/v1/api/vessels/self'
SIGNALK_TO_N2K_FLUID_TYPES = { 'fuel': 0, 'freshWater': 1, 'greyWater': 2, 'liveWell': 3, 'Oil': 4, 'wasteWater': 5 }
SIGNALK_TANK_PATH_TO_SERVICE = {}
SETTINGS_ROOT = '/Settings/Devices'

class SystemBus(dbus.bus.BusConnection):
	def __new__(cls):
		return dbus.bus.BusConnection.__new__(cls, dbus.bus.BusConnection.TYPE_SYSTEM)

class SessionBus(dbus.bus.BusConnection):
	def __new__(cls):
		return dbus.bus.BusConnection.__new__(cls, dbus.bus.BusConnection.TYPE_SESSION)

def dbusconnection():
	return SessionBus() if 'DBUS_SESSION_BUS_ADDRESS' in os.environ else SystemBus()

# SignalkTank implements a DBUS service for a single tank. This rather
# crummy implementation strategy is forced on us by the very broken
# venus.os tank monitoring implementation. 

class SignalkTank:
	def __init__(self, n2kfluidtype, n2ktankinstance, paths, productname='Signal K tank', connection='Signal K tank service'):
		self._dbus = dbusconnection();
                self._servicename = '%s_%s_%s_%s' % (APPLICATION_SERVICE_NAME, SIGNALK_SERVER.replace('.','_').replace(':','_'), str(n2kfluidtype), str(n2ktankinstance))
		self._dbusservicename = 'com.victronenergy.tank.%s' % self._servicename
		self._paths = paths

                # Process settings and recover our VRM instance number
		appsettingspath = '%s/%s' % (SETTINGS_ROOT, APPLICATION_SERVICE_NAME)
                servicesettingspath = '%s/%s' % (SETTINGS_ROOT, self._servicename)
		proposedclassdeviceinstance = '%s:%s' % ('tank', n2ktankinstance)
		SETTINGS = {
			'instance':   [servicesettingspath + '/ClassAndVrmInstance', proposedclassdeviceinstance, 0, 0],
			'customname': [servicesettingspath + '/CustomName', '', 0, 0]
		}
                self._settings = SettingsDevice(self._dbus, SETTINGS, self._handlesettingschanged)

		self._dbusservice = VeDbusService(self._dbusservicename, self._dbus)
		self._dbusservice.add_path('/Mgmt/ProcessName', __file__)
		self._dbusservice.add_path('/Mgmt/ProcessVersion', VERSION + ' on Python ' + platform.python_version())
		self._dbusservice.add_path('/Mgmt/Connection', 'SignalK ' + self._settings['instance'])

		self._dbusservice.add_path('/DeviceInstance', self._settings['instance'].split(':')[1])
		self._dbusservice.add_path('/ProductId', 0)
		self._dbusservice.add_path('/ProductName', 'SignalK tank interface')
		self._dbusservice.add_path('/FirmwareVersion', 0)
		self._dbusservice.add_path('/HardwareVersion', 0)
		self._dbusservice.add_path('/Connected', 1)
 
		for path, settings in self._paths.iteritems():
			self._dbusservice.add_path(path, settings['initial'], writeable=True, onchangecallback=self._handlechangedvalue)

	def _handlesettingschanged(self, name, old, new):
		return
	

	def _update(self, currentLevel):
		self._dbusservice['/Level'] = (currentLevel * 100)
		self._dbusservice['/Remaining'] = (self._dbusservice['/Capacity'] * currentLevel)

	def _handlechangedvalue(self, path, value):
		logging.debug("someone else updated %s to %s" % (path, value))
		return True # accept the change

def updateTanks():
	for path in SIGNALK_TANK_PATH_TO_SERVICE:
		http = httplib.HTTPConnection(SIGNALK_SERVER)																   
		http.request('GET', path)													  
		res = http.getresponse()																						
		if res.status == 200:																									   
			currentLevel = json.loads(res.read())	  
			SIGNALK_TANK_PATH_TO_SERVICE[path]._update(currentLevel)
			logging.debug('updateTanks: updating service for %s with %f' % (path, currentLevel))
		http.close()
	return(1)

# This program creates a collection of dbus services each of which
# represents tank data recovered from the configured Signal K
# server.
#
# Each service has a name like com.victronenergy.tank.signalk_tank_n
# where 'n' is the N2K instance number of the tank as reported by
# Signal K. Each service provides dbus data items in a format which
# can be processed and displayed by the CCGX gui.

def main():
	logging.basicConfig(level=logging.INFO)

	from dbus.mainloop.glib import DBusGMainLoop
	DBusGMainLoop(set_as_default=True)

	# If no Signal K tanks are configured, then auto-configure by
	# recovering all available tank paths from the server.
	if not SIGNALK_TANKS:
		http = httplib.HTTPConnection(SIGNALK_SERVER)
		http.request('GET', SIGNALK_SELF_PATH + '/tanks/')
		res = http.getresponse()
		if res.status == 200:
			jsondata = json.loads(res.read())
			for fluidtype in jsondata:
				if fluidtype in N2K_FLUID_TYPES:
					for instance in jsondata[fluidtype]:
						fluidType = SIGNALK_TO_N2K_FLUID_TYPES[fluidtype]
						capacity = jsondata[fluidtype][instance]['capacity']['value']
						SIGNALK_TANK_PATHS.append({ 'path': 'tanks/' + fluidtype + '/' + instance })
						SIGNALK_TANK_PATHS.sort(key=lambda x: x.get('path')[::-1])
		http.close()
		logging.info('%d tanks autoconfigured from the remote server' % len(SIGNALK_TANK_PATHS))

	# For each configured tank path create a service with DBUS values
	# that can be processed by the CCGX interface. 
	if SIGNALK_TANKS:
		for tank in SIGNALK_TANKS:
			if ('path' in tank):
				[ dummy, fluidtype, instance ] = tank['path'].split('/')
				http = httplib.HTTPConnection(SIGNALK_SERVER)
				http.request('GET', SIGNALK_SELF_PATH + '/' + tank['path'])
				res = http.getresponse()
				if res.status == 200:
					jsondata = json.loads(res.read())
					fluidType = SIGNALK_TO_N2K_FLUID_TYPES[fluidtype]
					capacity = jsondata['capacity']['value']
					service = SignalkTank(
						n2kfluidtype=fluidType,
                                        	n2ktankinstance=int(instance),
						paths={
							'/Level': { 'initial': 0 },
							'/FluidType': { 'initial': fluidType },
							'/Capacity': { 'initial': capacity },
							'/Remaining': { 'initial': 0 }
						}
					)
					SIGNALK_TANK_PATH_TO_SERVICE[SIGNALK_SELF_PATH + '/' + tank['path'] + '/currentLevel/value'] = service
				http.close()

		# And finally arrange to update tank data every so often.
		gobject.timeout_add(UPDATE_INTERVAL, updateTanks)

	mainloop = gobject.MainLoop()
	mainloop.run()

if __name__ == "__main__":
	main()

