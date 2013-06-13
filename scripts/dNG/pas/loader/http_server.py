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
from dNG.pas.net.http import Server as AbstractHttpServer
from dNG.pas.plugins.hooks import Hooks

class HttpServer(Cli):
#
	"""
"HttpServer" is responsible to start an HTTP aware server.

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
		self.log_handler = None
		"""
The log_handler is called whenever debug messages should be logged or errors
happened.
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

		Cli.register_run_callback(self.callback_run)
	#

	def callback_exit(self):
	#
		"""
Callback for application exit.

:since: v0.1.00
		"""

		Hooks.call("dNG.pas.status.shutdown")
		self.stop()
	#

	def callback_run(self, args):
	#
		"""
Callback for initialisation.

:since: v1.0.0
		"""

		Settings.read_file("{0}/settings/pas_global.json".format(Settings.get("path_data")))
		Settings.read_file("{0}/settings/pas_core.json".format(Settings.get("path_data")), True)
		Settings.read_file("{0}/settings/pas_http_server.json".format(Settings.get("path_data")), True)
		if (args.additional_settings != None): Settings.read_file(args.additional_settings, True)

		if (args.stop):
		#
			client = BusClient("pas_http")
			client.request("dNG.pas.status.stop")
			client.disconnect()
		#
		else:
		#
			self.cache_instance = NamedLoader.get_singleton("dNG.pas.data.Cache", False)
			self.log_handler = NamedLoader.get_singleton("dNG.pas.data.logging.LogHandler", False)

			if (self.log_handler != None):
			#
				Hooks.set_log_handler(self.log_handler)
				NamedLoader.set_log_handler(self.log_handler)
				self.log_handler.debug("#echo(__FILEPATH__)# -http_server.callback_run(args)- (#echo(__LINE__)#)")
			#

			Cli.register_shutdown_callback(self.callback_exit)

			Hooks.load("http")
			Hooks.register("dNG.pas.status.getUptime", self.get_uptime)
			Hooks.register("dNG.pas.status.stop", self.stop)
			self.time_started = time()

			http_server = AbstractHttpServer.get_instance()
			self.server = BusServer("pas_http")

			if (http_server != None):
			#
				Hooks.register("dNG.pas.status.startup", http_server.start)
				Hooks.register("dNG.pas.status.shutdown", http_server.stop)

				Hooks.call("dNG.pas.status.startup")
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

			if (self.log_handler != None): self.log_handler.info("pas.http.core stopped listening")
		#

		if (self.cache_instance != None): self.cache_instance.return_instance()
		if (self.log_handler != None): self.log_handler.return_instance()

		return last_return
	#

	def get_time_started (self):
	#
		"""
Returns the time (timestamp) this service had been initialized.

:since: v1.0.0
		"""

		return self.time_started
	#

	def get_uptime (self, params = None, last_return = None):
	#
		"""
Returns the time (timestamp) this service had been initialized.

:param params: Parameter specified
:param last_return: The return value from the last hook called.

:return: (int) Unix timestamp; None if unknown
:since:  v0.1.00
		"""

		return floor(self.get_time_started())
	#
#

##j## EOF