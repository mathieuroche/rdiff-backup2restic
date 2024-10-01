#!/usr/bin/env python3
import os
import shutil
import subprocess
import tempfile
import unittest

import rb2r

TEMPDIR = tempfile.mkdtemp("rb2r_unittest")
RESTIC_PASSWORDFILE = os.path.join(TEMPDIR, "restic-passwordfile")
RDIFF_DIR_WITH_UTF = os.path.join(TEMPDIR, "rdiff1_dir")
RDIFF_DIR_WITH_ISO = os.path.join(TEMPDIR, "rdiff2_dir")
DATA_DIR_WITH_UTF = os.path.join(TEMPDIR, "data1_dir")
DATA_DIR_WITH_ISO = os.path.join(TEMPDIR, "data2_dir")


def build_rsync(data_dir, rdiffrepo_dir, filename=b"data"):
    # first rdiff-backup increment
    testdata = data_dir.encode("utf-8")
    os.mkdir(testdata)
    with open(os.path.join(testdata, filename), "w", encoding="utf-8") as filep:
        filep.write("first")

    subprocess.check_call(
        ["faketime", "2015-10-01 08:00:00", "rdiff-backup", testdata, rdiffrepo_dir]
    )

    # second rdiff-backup increment
    with open(os.path.join(testdata, filename), "w", encoding="utf-8") as filep:
        filep.write("second")

    subprocess.check_call(
        ["faketime", "2015-10-01 09:00:00", "rdiff-backup", testdata, rdiffrepo_dir]
    )


def setUpModule():
    print("Creating fixture...")
    os.environ["TMPDIR"] = TEMPDIR

    with open(RESTIC_PASSWORDFILE, "w", encoding="utf-8") as filep:
        filep.write("mdp")

    build_rsync(DATA_DIR_WITH_UTF, RDIFF_DIR_WITH_UTF)

    build_rsync(DATA_DIR_WITH_ISO, RDIFF_DIR_WITH_ISO, "éçè".encode("iso-8859-1"))

    print("OK")


def tearDownModule():
    shutil.rmtree(TEMPDIR)


class TestRB2R(unittest.TestCase):
    def test_rdiff_parse(self):
        lines = """Found 1 increments:
    increments.2015-09-17T18:44:09+03:00.dir   Thu Sep 17 18:44:09 2015
Current mirror: Thu Sep 17 18:45:04 2015""".split(
            "\n"
        )
        increments = rb2r.parse_rdiff_increments(lines)
        self.assertEqual(len(increments), 2)
        self.assertEqual(increments[0], "2015-09-17T18:44:09")
        self.assertEqual(increments[1], "2015-09-17T18:45:04")

    def test_restic_parse(self):
        lines = """ID        Time                 Host        Tags        Paths
------------------------------------------------------------------------------------
eabbd6d7  2015-09-17 18:44:09  t420                    /tmp/tmp9hkeoq1wrb2a_unittest
bc42bec7  2015-09-17 18:45:04  t420                    /tmp/tmp9hkeoq1wrb2a_unittest
------------------------------------------------------------------------------------
2 snapshots
""".split(
            "\n"
        )
        archives = rb2r.parse_restic_archives(lines)
        self.assertEqual(len(archives), 2)
        self.assertEqual(archives[0], "2015-09-17T18:44:09")
        self.assertEqual(archives[1], "2015-09-17T18:45:04")

    def test_get_increments_to_convert(self):
        increments = ["2015-10-01T08:00:00", "2015-10-01T09:00:00"]
        archives = ["2015-10-01T09:00:00"]
        results = rb2r.get_increments_to_convert(increments, archives)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], "2015-10-01T08:00:00")

    # integration tests below
    def test_parse_rdiff_repo(self):
        increments = rb2r.parse_rdiff_repo(RDIFF_DIR_WITH_UTF)
        self.assertEqual(len(increments), 2)
        # second can wary, depending on how long rdiff-backup takes to start up
        self.assertEqual(increments[0][:16], "2015-10-01T08:00")
        self.assertEqual(increments[1][:16], "2015-10-01T09:00")

    def test_restore_rdiff_increment(self):
        destination_dir = os.path.join(TEMPDIR, "restore")
        rb2r.restore_rdiff_increment(
            RDIFF_DIR_WITH_UTF, destination_dir, "2015-10-01T08:00:00"
        )

        with open(os.path.join(TEMPDIR, "restore", "data"), encoding="utf-8") as filep:
            data = filep.read()

        shutil.rmtree(destination_dir)

        self.assertEqual(data, "first")

    def test_restic_create(self):
        destination_dir = os.path.join(TEMPDIR, "restore")
        rb2r.restore_rdiff_increment(
            RDIFF_DIR_WITH_UTF, destination_dir, "2015-10-01T08:00:00"
        )

        restic_dir = os.path.join(TEMPDIR, "restic")
        subprocess.check_call(
            [
                "restic",
                "init",
                "--password-file",
                RESTIC_PASSWORDFILE,
                "--repo",
                restic_dir,
            ]
        )
        rb2r.restic_create(
            restic_dir, "2015-10-01T08:00:00", destination_dir, RESTIC_PASSWORDFILE
        )

        archives = rb2r.parse_restic_repo(restic_dir, RESTIC_PASSWORDFILE)

        shutil.rmtree(restic_dir)
        shutil.rmtree(destination_dir)

        self.assertEqual(len(archives), 1)
        self.assertEqual(archives[0], "2015-10-01T08:00:00")

    def test_convert_increment(self):
        restic_dir = os.path.join(TEMPDIR, "restic")
        subprocess.check_call(
            [
                "restic",
                "init",
                "--password-file",
                RESTIC_PASSWORDFILE,
                "--repo",
                restic_dir,
            ]
        )

        rb2r.convert_increment(
            RDIFF_DIR_WITH_UTF, restic_dir, RESTIC_PASSWORDFILE, "2015-10-01T08:00:00"
        )

        archives = rb2r.parse_restic_repo(restic_dir, RESTIC_PASSWORDFILE)

        shutil.rmtree(restic_dir)

        self.assertEqual(len(archives), 1)
        self.assertEqual(archives[0], "2015-10-01T08:00:00")

    def test_convert_increment2(self):
        restic_dir = os.path.join(TEMPDIR, "restic2")
        subprocess.check_call(
            [
                "restic",
                "init",
                "--password-file",
                RESTIC_PASSWORDFILE,
                "--repo",
                restic_dir,
            ]
        )

        rb2r.convert_increment(
            RDIFF_DIR_WITH_ISO,
            restic_dir,
            RESTIC_PASSWORDFILE,
            "2015-10-01T08:00:00",
            repair_encoding=True,
            encoding_repaired_tag="pouet",
        )

        archives = rb2r.parse_restic_repo(restic_dir, RESTIC_PASSWORDFILE)

        shutil.rmtree(restic_dir)

        self.assertEqual(len(archives), 2)
        self.assertEqual(archives[0], "2015-10-01T08:00:00")

    def test_convert_increment3(self):
        restic_dir = os.path.join(TEMPDIR, "restic3")
        subprocess.check_call(
            [
                "restic",
                "init",
                "--password-file",
                RESTIC_PASSWORDFILE,
                "--repo",
                restic_dir,
            ]
        )

        rb2r.convert_increment(
            RDIFF_DIR_WITH_UTF,
            restic_dir,
            RESTIC_PASSWORDFILE,
            "2015-10-01T08:00:00",
            repair_encoding=True,
            encoding_repaired_tag="pouet",
        )

        archives = rb2r.parse_restic_repo(restic_dir, RESTIC_PASSWORDFILE)

        shutil.rmtree(restic_dir)

        self.assertEqual(len(archives), 1)
        self.assertEqual(archives[0], "2015-10-01T08:00:00")


if __name__ == "__main__":
    unittest.main()
