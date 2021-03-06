#!/usr/bin/env python2.7
# Copyright 2016 Arjun Arkal Rao
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Author : Arjun Arkal Rao
Affiliation : UCSC BME, UCSC Genomics Institute
File : protect/test/test_file_downloads.py
"""
from __future__ import print_function

from protect.common import get_file_from_s3
from protect.test import ProtectTest

from toil.job import Job

import os


class TestFileDownloads(ProtectTest):
    def setUp(self):
        super(TestFileDownloads, self).setUp()
        test_dir = self._createTempDir()
        self.options = Job.Runner.getDefaultOptions(self._getTestJobStorePath())
        self.options.logLevel = 'INFO'
        self.options.workDir = test_dir
        self.options.clean = 'always'

    def test_file_downloads_from_s3(self):
        """
        Test the functionality of get_file_from_s3
        """
        a = Job.wrapJobFn(self._download_files)
        Job.Runner.startToil(a, self.options)

    @staticmethod
    def _download_files(job):
        """
        Attempts to download an unencrypted file, a file encrypted with a key, and a file encrypted
        with a hash of a master key.
        """
        keyfile = os.path.abspath('test.key')
        with open(keyfile, 'w') as k_f:
            k_f.write('protectwillhelpwithimmunotherapy')
        http_base = 'https://s3-us-west-2.amazonaws.com/pimmuno-test-data/CI_test_input/'
        s3_base = 'S3://pimmuno-test-data/CI_test_input/'
        unencrypted = 'unencrypted.file'
        encrypted_with_key = 'encrypted_with_test_key.file'
        encrypted_with_hash = 'encrypted_with_key_hash.file'
        # Download with https schema
        get_file_from_s3(job, http_base + unencrypted, write_to_jobstore=False)
        get_file_from_s3(job, http_base + encrypted_with_key, encryption_key=keyfile,
                         per_file_encryption=False, write_to_jobstore=False)
        get_file_from_s3(job, http_base + encrypted_with_hash, encryption_key=keyfile,
                         write_to_jobstore=False)
        # Download with S3 schema
        get_file_from_s3(job, s3_base + unencrypted, write_to_jobstore=False)
        # Test wrong schema
        try:
            get_file_from_s3(job, 's' + s3_base + encrypted_with_hash, encryption_key=keyfile,
                             write_to_jobstore=False)
        except RuntimeError as err:
            if 'Unexpected url scheme' not in err.message:
                raise
        # Test downloading encrypted file without key
        try:
            get_file_from_s3(job, s3_base + encrypted_with_hash, write_to_jobstore=False)
        except RuntimeError as err:
            if '400' not in err.message:
                raise
        # Test downloading file encrypted with hash using the master (this emulates downloading
        # file with the wrong key)
        try:
            get_file_from_s3(job, s3_base + encrypted_with_hash, encryption_key=keyfile,
                             per_file_encryption=False, write_to_jobstore=False)
        except RuntimeError as err:
            if '403' not in err.message:
                raise
        # Test downloading unencrypted with a key
        try:
            get_file_from_s3(job, s3_base + unencrypted, encryption_key=keyfile,
                             per_file_encryption=False, write_to_jobstore=False)
        except RuntimeError as err:
            if '400' not in err.message:
                raise
        # Test downloading non-existent file
        try:
            get_file_from_s3(job, s3_base + unencrypted + 'xx', write_to_jobstore=False)
        except RuntimeError as err:
            if 'exist on s3?' not in err.message:
                raise


# noinspection PyProtectedMember
_download_files = TestFileDownloads._download_files
