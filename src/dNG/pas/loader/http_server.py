# -*- coding: utf-8 -*-
##j## BOF

"""
direct PAS
Python Application Services
----------------------------------------------------------------------------
(C) direct Netware Group - All rights reserved
https://www.direct-netware.de/redirect?pas;http;loader

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
https://www.direct-netware.de/redirect?licenses;gpl
----------------------------------------------------------------------------
#echo(pasHttpLoaderVersion)#
#echo(__FILEPATH__)#
"""

from argparse import ArgumentParser
from time import time

from dNG.pas.data.settings import Settings
from dNG.pas.loader.cli import Cli
from dNG.pas.module.named_loader import NamedLoader
from dNG.pas.net.bus.client import Client as BusClient
from dNG.pas.net.bus.server import Server as BusServer
from dNG.pas.net.http.server_implementation import ServerImplementation as _HttpServer
from dNG.pas.plugins.hook import Hook
from .bus_mixin import BusMixin

class HttpServer(Cli, BusMixin):
#
	"""
"HttpServer" provides the command line for an HTTP aware server.

:author:     direct Netware Group
:copyright:  (C) direct Netware Group - All rights reserved
:package:    pas.http
:subpackage: loader
:since:      v0.1.00
:license:    https://www.direct-netware.de/redirect?licenses;gpl
             GNU General Public License 2
	"""

	# pylint: disable=unused-argument

	def __init__(self):
	#
		"""
Constructor __init__(HttpServer)

:since: v0.1.00
		"""

		Cli.__init__(self)
		BusMixin.__init__(self)

		self.cache_instance = None
		"""
Cache instance
		"""
		self.server = None
		"""
Server thread
		"""

		self.arg_parser = ArgumentParser()
		self.arg_parser.add_argument("--additionalSettings", action = "store", type = str, dest = "additional_settings")
		self.arg_parser.add_argument("--reloadPlugins", action = "store_true", dest = "reload_plugins")
		self.arg_parser.add_argument("--stop", action = "store_true", dest = "stop")

		Cli.register_run_callback(self._on_run)
		Cli.register_shutdown_callback(self._on_shutdown)
	#

	def _on_run(self, args):
	#
		"""
Callback for execution.

:param args: Parsed command line arguments

:since: v0.1.00
		"""

		Settings.read_file("{0}/settings/pas_global.json".format(Settings.get("path_data")))
		Settings.read_file("{0}/settings/pas_core.json".format(Settings.get("path_data")), True)
		Settings.read_file("{0}/settings/pas_http.json".format(Settings.get("path_data")), True)
		if (args.additional_settings is not None): Settings.read_file(args.additional_settings, True)

		if (args.reload_plugins):
		#
			client = BusClient("pas_http_bus")
			client.request("dNG.pas.Plugins.reload")
		#
		elif (args.stop):
		#
			client = BusClient("pas_http_bus")

			pid = client.request("dNG.pas.Status.getOSPid")
			client.request("dNG.pas.Status.stop")

			self._wait_for_os_pid(pid)
		#
		else:
		#
			self.cache_instance = NamedLoader.get_singleton("dNG.pas.data.cache.Content", False)
			if (self.cache_instance is not None): Settings.set_cache_instance(self.cache_instance)

			self.log_handler = NamedLoader.get_singleton("dNG.pas.data.logging.LogHandler", False)

			if (self.log_handler is not None):
			#
				Hook.set_log_handler(self.log_handler)
				NamedLoader.set_log_handler(self.log_handler)
			#

			Hook.load("http")
			Hook.register("dNG.pas.Status.getOSPid", self.get_os_pid)
			Hook.register("dNG.pas.Status.getTimeStarted", self.get_time_started)
			Hook.register("dNG.pas.Status.getUptime", self.get_uptime)
			Hook.register("dNG.pas.Status.stop", self.stop)
			self._set_time_started(time())

			http_server = _HttpServer.get_instance()
			self.server = BusServer("pas_http_bus")

			if (http_server is not None):
			#
				Hook.register("dNG.pas.Status.onStartup", http_server.start)
				Hook.register("dNG.pas.Status.onShutdown", http_server.stop)

				if (self.log_handler is not None): self.log_handler.info("pas.http starts listening", context = "pas_http_site")
				Hook.call("dNG.pas.Status.onStartup")

				self.set_mainloop(self.server.run)
			#
		#
	#

	def _on_shutdown(self):
	#
		"""
Callback for shutdown.

:since: v0.1.00
		"""

		Hook.call("dNG.pas.Status.onShutdown")

		if (self.cache_instance is not None): self.cache_instance.disable()
		Hook.free()
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

		if (self.server is not None):
		#
			self.server.stop()
			self.server = None

			if (self.log_handler is not None): self.log_handler.info("pas.http stopped listening", context = "pas_http_site")
		#

		return last_return
	#
#

##j## EOF