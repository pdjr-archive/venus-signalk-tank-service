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

########################################################################
# START OF USER CONFIGURATION
########################################################################

# Change this value to specify your Signal K server.

SIGNALK_SERVER = '192.168.1.2:3000'

# Specify an empty array and all tank paths on the Signal K server
# will be automatically acquired. Otherwise, specify the tanks you
# want to handle like this.

SIGNALK_TANKS = [
	{ 'path': 'tanks/wasteWater/0' },
	{ 'path': 'tanks/freshWater/1' },
	{ 'path': 'tanks/freshWater/2' },
	{ 'path': 'tanks/fuel/3' },
	{ 'path': 'tanks/fuel/4' }
]

# The frequency in ms at which to update tank data.

UPDATE_INTERVAL = 10000

########################################################################
# END OF USER CONFIGURATION
########################################################################

SIGNALK_SELF_PATH='/signalk/v1/api/vessels/self'
SIGNALK_TO_N2K_FLUID_TYPES = { 'fuel': 0, 'freshWater': 1, 'greyWater': 2, 'liveWell': 3, 'Oil': 4, 'wasteWater': 5 }
SIGNALK_TANK_PATH_TO_SERVICE = {}

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
	def __init__(self, servicename, paths, deviceinstance, productname='Signal K tank', connection='Signal K tank service'):
		self._dbus = dbusconnection();
		self._dbusservice = VeDbusService(servicename, self._dbus)
		self._paths = paths

		self._dbusservice.add_path('/Mgmt/ProcessName', __file__)
		self._dbusservice.add_path('/Mgmt/ProcessVersion', 'Unkown version, and running on Python ' + platform.python_version())
		self._dbusservice.add_path('/Mgmt/Connection', 'SignalK' + str(deviceinstance))

		self._dbusservice.add_path('/DeviceInstance', deviceinstance)
		self._dbusservice.add_path('/ProductId', 0)
		self._dbusservice.add_path('/ProductName', 'SignalK tank interface')
		self._dbusservice.add_path('/FirmwareVersion', 0)
		self._dbusservice.add_path('/HardwareVersion', 0)
		self._dbusservice.add_path('/Connected', 1)
 
		for path, settings in self._paths.iteritems():
			self._dbusservice.add_path(path, settings['initial'], writeable=True, onchangecallback=self._handlechangedvalue)

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
			[ dummy, fluidtype, instance ] = tank['path'].split('/')
			http = httplib.HTTPConnection(SIGNALK_SERVER)
			http.request('GET', SIGNALK_SELF_PATH + '/' + tank['path'])
			res = http.getresponse()
			if res.status == 200:
				jsondata = json.loads(res.read())
				fluidType = SIGNALK_TO_N2K_FLUID_TYPES[fluidtype]
				capacity = jsondata['capacity']['value']
				serviceName = 'com.victronenergy.tank.signalk_tank_' + fluidType + '_' + instance
				service = SignalkTank(
					servicename=serviceName,
					deviceinstance=int(instance),
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

