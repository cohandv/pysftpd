#!/usr/bin/python -tt
# -*- coding: ascii -*-
# Copyright (c) 2007, 2008  Dwayne C. Litzenberger <dlitz@dlitz.net>
#
# This file is part of PySFTPd.
#
# PySFTPd is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# PySFTPd is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import ConfigParser
import paramiko
import base64
from LocalConfiguration import LocalConfiguration
from S3Storage import S3Storage
from LocalStorage import LocalStorage

class ConfigurationError(Exception):
    pass

class Configuration(object):

    def __init__(self, conffile_path):
        self.conffile_path = conffile_path
        self.load()

    def load(self):
        cfgSection = 'pysftpd'

        # Read the main configuration file
        config = ConfigParser.RawConfigParser()
        if not config.read(self.conffile_path):
            raise ConfigurationError("Unable to load configuration file %r" % (self.conffile_path,))

        # Read bind address
        listen_host = config.get(cfgSection, 'listen_host')
        listen_port = config.getint(cfgSection, 'listen_port')
        self.bind_address = (listen_host, listen_port)

        # Load host keys
        host_keys = []
        for optname in config.options(cfgSection):
            if optname != "host_key" and not optname.startswith("host_key."):
                continue
            filename = config.get(cfgSection, optname)
            try:
                host_key = paramiko.RSAKey.from_private_key_file(filename=filename)
            except paramiko.SSHException:
                host_key = paramiko.DSSKey.from_private_key_file(filename=filename)
            host_keys.append(host_key)
            host_key = None # erase reference to host key
        if not host_keys:
            raise ConfigurationError("config file %r does not specify any host key" % (self.conffile_path,))
        self.host_keys = host_keys

        # Storage type
        storage_type = config.get(cfgSection, 'storage_type')
        if storage_type.lower() == "local":
            self.storage_type = LocalStorage
        elif storage_type.lower() == "s3":
            self.storage_type = S3Storage
        else:
            raise ConfigurationError("Unrecognized %s storage type. use local or s3" % (storage_type,))

        # Load the authentication auth_provider
        auth_provider = config.get(cfgSection, 'auth_provider')
        if auth_provider.lower() == 'api':
            raise ConfigurationError("auth provider %s is not YET valid, use local" % (auth_provider))
        elif auth_provider.lower() == 'local':
            self.users = LocalConfiguration().getUsers(config.get(cfgSection, 'auth_local'),config.get(cfgSection, 's3_bucket'))
        else:
            raise ConfigurationError("auth provider %s is not valid, use api or local" % (auth_provider))

# vim:set ts=4 sw=4 sts=4 expandtab:
