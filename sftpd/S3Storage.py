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

import paramiko
import boto3
import datetime
import posix
from dateutil.tz import tzutc

class S3Storage(paramiko.SFTPServerInterface):

    def __init__(self, server, getUserFunc):
        self.bucket = getUserFunc().bucket
        self.username = getUserFunc().username
        self.homeDirectory = getUserFunc().homeDirectory
        self.s3 = boto3.client('s3')

    def _local_path(self, sftp_path):
        """Return the local path given an SFTP path.  Raise an exception if the path is illegal."""
        return "%s/%s" % (self.bucket,sftp_path)

    def getStat(self, file):
        try:
            _time = (file['LastModified'].replace(tzinfo=None) - datetime.datetime.utcfromtimestamp(0)).total_seconds() * 1000.0
            return paramiko.SFTPAttributes.from_stat(posix.stat_result((33188, 0, 0, 1, 0, 0, file['Size'], _time, _time, _time)), file['Key'])
        except Exception as e:
            print(e)
            raise

    def list_folder(self, sftp_path):
        retval = []
        kwargs = {'Bucket': self.bucket, 'Prefix': '%s/%s'%(self.username, self.homeDirectory)}
        while True:
            try:
                resp = self.s3.list_objects_v2(**kwargs)
                for obj in resp['Contents']:
                    retval.append(self.getStat(obj))
                kwargs['ContinuationToken'] = resp['NextContinuationToken']
            except KeyError:
                break
        return retval

    def stat(self, sftp_path):
        print('stat')
        print(sftp_path)
        retval = []
        kwargs = {'Bucket': self.bucket, 'Prefix': '%s/%s%s'%(self.username, self.homeDirectory,sftp_path)}
        try:
            resp = self.s3.list_objects_v2(**kwargs)
            obj = self.getStat(resp['Contents'][0])
            print(obj)
            return obj
        except:
            return

    def lstat(self, sftp_path):
        print('lstat')
        return self.stat(sftp_path)

    def open(self, sftp_path, flags, attr):
        print('open')
        local_path = self._local_path(sftp_path)
        if (flags & os.O_WRONLY) or (flags & os.O_RDWR):
            return paramiko.SFTP_PERMISSION_DENIED
        h = paramiko.SFTPHandle()
        h.readfile = open(local_path, "rb")
        return h

# vim:set ts=4 sw=4 sts=4 expandtab:
