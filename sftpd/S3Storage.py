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
import posixpath
import boto3

class S3Storage(paramiko.SFTPServerInterface):

    def __init__(self, server, getUserFunc):
        self.bucket = getUserFunc().bucket
        self.username = getUserFunc().username
        self.s3 = boto3.resource('s3')

    def _local_path(self, sftp_path):
        """Return the local path given an SFTP path.  Raise an exception if the path is illegal."""
        return "%s/%s" % (self.bucket,sftp_path)

    def list_folder(self, sftp_path):
        print('List')
        retval = []
        kwargs = {'Bucket': self.bucket, 'Prefix': '/%s'%(self.username)}
        print(kwargs)
        while True:
            try:
                print(self.s3)
                resp = self.s3.list_objects_v2(**kwargs)
                print(resp)
                retval.extend(resp['Contents'])
                kwargs['ContinuationToken'] = resp['NextContinuationToken']
            except KeyError:
                break
        return retval

    def stat(self, sftp_path):
        print('stat')
        return paramiko.SFTPAttributes.from_stat("-rw-r--r--   1 503      0               0 22 Mar 16:47 "+sftp_path)

    def lstat(self, sftp_path):
        print('lstat')
        return paramiko.SFTPAttributes.from_stat("-rw-r--r--   1 503      0               0 22 Mar 16:47 "+sftp_path)

    def open(self, sftp_path, flags, attr):
        local_path = self._local_path(sftp_path)
        if (flags & os.O_WRONLY) or (flags & os.O_RDWR):
            return paramiko.SFTP_PERMISSION_DENIED
        h = paramiko.SFTPHandle()
        h.readfile = open(local_path, "rb")
        return h

# vim:set ts=4 sw=4 sts=4 expandtab:
