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
import stat
import os

class S3Storage(paramiko.SFTPServerInterface):

    def __init__(self, server, getUserFunc):
        self.bucket = getUserFunc().bucket
        self.username = getUserFunc().username
        self.homeDirectory = getUserFunc().homeDirectory
        self.s3 = boto3.client('s3')

    def removeLeadingSlash(self,sftp_path):
        return sftp_path[1:]

    def removeTrailingSlash(self,sftp_path):
        return sftp_path[:-1]

    def getStat(self, file):
        try:
            _time = (file['LastModified'].replace(tzinfo=None) - datetime.datetime.utcfromtimestamp(0)).total_seconds()
            top_level_filename = file['Key'].replace("%s/%s/"%(self.username, self.homeDirectory),"")
            #This an equivalent to 744
            mode = stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH
            #Stupid hack to detect when a key is a directory instead
            if top_level_filename.endswith('/'):
                top_level_filename = top_level_filename[:-1]
                mode |= stat.S_IFDIR
            else:
                mode |= stat.S_IFREG
            print(posix.stat_result((mode, 0, 0, 1, 0, 0, file['Size'], _time, _time, _time)))
            d = paramiko.SFTPAttributes.from_stat(posix.stat_result((mode, 0, 0, 1, 0, 0, file['Size'], _time, _time, _time)), top_level_filename)
            print(d)
            return d
        except Exception as e:
            print(e)
            raise

    def canonicalize(self, path):
        print ('canonicalize')
        if path == ".":
            out = '/%s/%s'%(self.username, self.homeDirectory)
        elif os.path.isabs(path):
            out = os.path.normpath(path)
        else:
            out = '/%s/%s%s'%(self.username, self.homeDirectory,path)
        print(out)
        return out

    def mkdir(self, sftp_path, attr) :
        print('mkdir')
        tmp_dir = '%s/'%(sftp_path)
        print(tmp_dir)
        response = self.s3.put_object(Bucket=self.bucket,Body='',Key=tmp_dir)
        print(response)
        return paramiko.SFTP_OK

    def list_folder(self, sftp_path):
        retval = []
        prefix = self.removeLeadingSlash(sftp_path)
        kwargs = {'Bucket': self.bucket, 'Prefix': prefix}
        print (kwargs)
        while True:
            try:
                resp = self.s3.list_objects_v2(**kwargs)
                print(resp['Contents'])
                for obj in resp['Contents']:
                    #We do not want the exact same key
                    if self.removeTrailingSlash(obj['Key'].lower()) != prefix.lower():
                        print(obj['Key'].lower())
                        print(prefix.lower())
                        retval.append(self.getStat(obj))
                kwargs['ContinuationToken'] = resp['NextContinuationToken']
            except KeyError:
                break
        return retval

    def stat(self, sftp_path):
        print('stat')
        print(sftp_path)
        retval = []
        #'%s/%s%s'%(self.username, self.homeDirectory,sftp_path)
        prefix = self.removeLeadingSlash(sftp_path)
        kwargs = {'Bucket': self.bucket, 'Prefix': prefix}
        try:
            resp = self.s3.list_objects_v2(**kwargs)
            print(resp['Contents'])
            obj = self.getStat(resp['Contents'][0])
            print(obj)
            return obj
        except:
            return

    def lstat(self, sftp_path):
        return self.stat(sftp_path)

    def open(self, sftp_path, flags, attr):
        print('open')
        try:
            tmp_dir = '/tmp'
            tmp_file = '%s%s'%(tmp_dir,sftp_path)
            if not os.path.isdir(tmp_dir):
                os.makedirs(tmp_dir)
            self.s3.download_file(self.bucket, self.removeLeadingSlash(sftp_path), tmp_file)
            data = open(tmp_file, 'rb')
            h = paramiko.SFTPHandle()
            h.readfile = data
            return h
        except Exception as e:
            print(e)


# vim:set ts=4 sw=4 sts=4 expandtab:
