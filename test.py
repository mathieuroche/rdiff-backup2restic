#!/usr/bin/env python3
import os
import shutil
import subprocess
import tempfile
import unittest

import rb2a

def setUpModule():
    print('Creating fixture...')
    global tempdir, testdata, rdiffrepo, restic_passwordfile
    tempdir = tempfile.mkdtemp('rb2a_unittest')
    os.environ['TMPDIR'] = tempdir

    restic_passwordfile = os.path.join(tempdir, 'password-file')
    with open(restic_passwordfile, 'w') as f:
        f.write('mdp')

    # first rdiff-backup increment
    testdata = os.path.join(tempdir, 'testdata')
    os.mkdir(testdata)
    with open(os.path.join(testdata, 'data'), 'w') as f:
        f.write('first')

    rdiffrepo = os.path.join(tempdir, 'rdiff-repo')
    subprocess.check_call(['faketime', '2015-10-01 08:00:00', 'rdiff-backup', testdata, rdiffrepo])

    # second rdiff-backup increment
    with open(os.path.join(testdata, 'data'), 'w') as f:
        f.write('second')

    subprocess.check_call(['faketime', '2015-10-01 09:00:00', 'rdiff-backup', testdata, rdiffrepo])
    print('OK')

def tearDownModule():
    global tempdir
    shutil.rmtree(tempdir)

class TestRB2A(unittest.TestCase):
    def test_rdiff_parse(self):
        lines = """Found 1 increments:
    increments.2015-09-17T18:44:09+03:00.dir   Thu Sep 17 18:44:09 2015
Current mirror: Thu Sep 17 18:45:04 2015""".split('\n')
        increments = rb2a.parse_rdiff_increments(lines)
        self.assertEqual(len(increments), 2)
        self.assertEqual(increments[0], '2015-09-17T18:44:09')
        self.assertEqual(increments[1], '2015-09-17T18:45:04')

    def test_restic_parse(self):
        lines = """ID        Time                 Host        Tags        Paths
------------------------------------------------------------------------------------
eabbd6d7  2015-09-17 18:44:09  t420                    /tmp/tmp9hkeoq1wrb2a_unittest
bc42bec7  2015-09-17 18:45:04  t420                    /tmp/tmp9hkeoq1wrb2a_unittest
------------------------------------------------------------------------------------
2 snapshots
""".split('\n')
        archives = rb2a.parse_restic_archives(lines)
        self.assertEqual(len(archives), 2)
        self.assertEqual(archives[0], '2015-09-17T18:44:09')
        self.assertEqual(archives[1], '2015-09-17T18:45:04')

    def test_get_increments_to_convert(self):
        increments = ['2015-10-01T08:00:00', '2015-10-01T09:00:00']
        archives = ['2015-10-01T09:00:00']
        results = rb2a.get_increments_to_convert(increments, archives)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], '2015-10-01T08:00:00')

    # integration tests below
    def test_parse_rdiff_repo(self):
        increments = rb2a.parse_rdiff_repo(rdiffrepo)
        self.assertEqual(len(increments), 2)
        # second can wary, depending on how long rdiff-backup takes to start up
        self.assertEqual(increments[0][:16], '2015-10-01T08:00')
        self.assertEqual(increments[1][:16], '2015-10-01T09:00')

    def test_restore_rdiff_increment(self):
        destination_dir = os.path.join(tempdir, 'restore')
        rb2a.restore_rdiff_increment(rdiffrepo, destination_dir, '2015-10-01T08:00:00')

        with open(os.path.join(tempdir, 'restore', 'data')) as f:
            data = f.read()

        shutil.rmtree(destination_dir)

        self.assertEqual(data, 'first')

    def test_restic_create(self):
        destination_dir = os.path.join(tempdir, 'restore')
        rb2a.restore_rdiff_increment(rdiffrepo, destination_dir, '2015-10-01T08:00:00')

        restic_dir = os.path.join(tempdir, 'restic')
        subprocess.check_call(['restic', 'init','--password-file', restic_passwordfile, '--repo', restic_dir])
        rb2a.restic_create(restic_dir, '2015-10-01T08:00:00', destination_dir, restic_passwordfile)

        archives = rb2a.parse_restic_repo(restic_dir, restic_passwordfile)

        shutil.rmtree(restic_dir)
        shutil.rmtree(destination_dir)

        self.assertEqual(len(archives), 1)
        self.assertEqual(archives[0], '2015-10-01T08:00:00')

    def test_convert_increment(self):
        restic_dir = os.path.join(tempdir, 'resic')
        subprocess.check_call(['restic', 'init','--password-file', restic_passwordfile, '--repo', restic_dir])
        
        rb2a.convert_increment(rdiffrepo, restic_dir, restic_passwordfile, '2015-10-01T08:00:00')

        archives = rb2a.parse_restic_repo(restic_dir, restic_passwordfile)

        shutil.rmtree(restic_dir)

        self.assertEqual(len(archives), 1)
        self.assertEqual(archives[0], '2015-10-01T08:00:00')

if __name__ == '__main__':
    unittest.main()
