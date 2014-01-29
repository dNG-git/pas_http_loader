# -*- coding: utf-8 -*-
##j## BOF

"""
dNG.pas.loader.HttpServer
"""
"""n// NOTE
----------------------------------------------------------------------------
direct PAS
Python Application Services
----------------------------------------------------------------------------
(C) direct Netware Group - All rights reserved
http://www.direct-netware.de/redirect.py?pas;http;loader

The following license agreement remains valid unless any additions or
changes are being made by direct Netware Group in a written form.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation; either version 2 of the License, or (at your
option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
more details.

You should have received a copy of the GNU General Public License along with
this program; if not, write to the Free Software Foundation, Inc.,
59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
----------------------------------------------------------------------------
http://www.direct-netware.de/redirect.py?licenses;gpl
----------------------------------------------------------------------------
#echo(pasHttpLoaderVersion)#
#echo(__FILEPATH__)#
----------------------------------------------------------------------------
NOTE_END //n"""

from argparse import ArgumentParser
from math import floor
from time import time

from dNG.pas.data.settings import Settings
from dNG.pas.loader.cli import Cli
from dNG.pas.module.named_loader import NamedLoader
from dNG.pas.net.bus.client import Client as BusClient
from dNG.pas.net.bus.server import Server as BusServer
from dNG.pas.net.http import Server as _HttpServer
from dNG.pas.plugins.hooks import Hooks

class HttpServer(Cli):
#
	"""
"HttpServer" provides the command line for an HTTP aware server.

:author:     direct Netware Group
:copyright:  (C) direct Netware Group - All rights reserved
:package:    pas.http
:subpackage: core
:since:      v0.1.00
:license:    http://www.direct-netware.de/redirect.py?licenses;gpl
             GNU General Public License 2
	"""

	def __init__(self):
	#
		"""
Constructor __init__(HttpServer)

:since: v0.1.00
		"""

		Cli.__init__(self)

		self.cache_instance = None
		"""
Cache instance
		"""
		self.server = None
		"""
Server thread
		"""
		self.time_started = None
		"""
Timestamp of service initialisation
		"""

		self.arg_parser = ArgumentParser()
		self.arg_parser.add_argument("--additionalSettings", action = "store", type = str, dest = "additional_settings")
		self.arg_parser.add_argument("--stop", action = "store_true", dest = "stop")

		Cli.register_run_callback(self._callback_run)
		Cli.register_shutdown_callback(self._callback_exit)
	#

	def _callback_exit(self):
	#
		"""
Callback for application exit.

:since: v0.1.00
		"""

		if (self.server != None): self.stop()
		Hooks.call("dNG.pas.Status.shutdown")

		if (self.cache_instance != None): self.cache_instance.disable()
		Hooks.free()
		if (self.log_handler != None): self.log_handler.info("pas.http.core stopped listening")
	#

	def _callback_run(self, args):
	#
		"""
Callback for initialisation.

:param args: Parsed command line arguments

:since: v1.0.0
		"""

		Settings.read_file("{0}/settings/pas_global.json".format(Settings.get("path_data")))
		Settings.read_file("{0}/settings/pas_core.json".format(Settings.get("path_data")), True)
		Settings.read_file("{0}/settings/pas_http.json".format(Settings.get("path_data")), True)
		if (args.additional_settings != None): Settings.read_file(args.additional_settings, True)

		if (args.stop):
		#
			client = BusClient("pas_http_bus")
			client.request("dNG.pas.Status.stop")
			client.disconnect()
		#
		else:
		#
			self.cache_instance = NamedLoader.get_singleton("dNG.pas.data.Cache", False)
			if (self.cache_instance != None): Settings.set_cache_instance(self.cache_instance)

			self.log_handler = NamedLoader.get_singleton("dNG.pas.data.logging.LogHandler", False)

			if (self.log_handler != None):
			#
				Hooks.set_log_handler(self.log_handler)
				NamedLoader.set_log_handler(self.log_handler)
				self.log_handler.debug("#echo(__FILEPATH__)# -HttpServer._callback_run(args)- (#echo(__LINE__)#)")
			#

			Hooks.load("http")
			Hooks.register("dNG.pas.Status.getTimeStarted", self.get_time_started)
			Hooks.register("dNG.pas.Status.getUptime", self.get_uptime)
			Hooks.register("dNG.pas.Status.stop", self.stop)
			self.time_started = int(time())

			http_server = _HttpServer.get_instance()
			self.server = BusServer("pas_http_bus")

			if (http_server != None):
			#
				Hooks.register("dNG.pas.Status.startup", http_server.start)
				Hooks.register("dNG.pas.Status.shutdown", http_server.stop)

				Hooks.call("dNG.pas.Status.startup")
				self.set_mainloop(self.server.run)
			#
		#
	#

	def stop(self, params = None, last_return = None):
	#
		"""
Stops the running server instance.

:param params: Parameter specified
:param last_return: The return value from the last hook called.

:return: (None) None to stop communication after this call
:since:  v0.1.00
		"""

		if (self.server != None):
		#
			self.server.stop()
			self.server = None
		#

		return last_return
	#

	def get_time_started(self, params = None, last_return = None):
	#
		"""
Returns the time (timestamp) this service had been initialized.

:param params: Parameter specified
:param last_return: The return value from the last hook called.

:return: (int) Unix timestamp
:since:  v1.0.0
		"""

		return self.time_started
	#

	def get_uptime(self, params = None, last_return = None):
	#
		"""
Returns the time in seconds since this service had been initialized.

:param params: Parameter specified
:param last_return: The return value from the last hook called.

:return: (int) Uptime in seconds
:since:  v0.1.00
		"""

		return int(floor(time() - self.time_started))
	#
#

##j## EOF