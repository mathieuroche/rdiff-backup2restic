import os
import shutil
import unittest
import tempfile

import cdte

TEMPDIR = tempfile.mkdtemp('cae_unittest').encode()
ARBO = []

def setUpModule():
    global ARBO
    ARBO = create_arbo(TEMPDIR, 2, 2)

def tearDownModule():
    shutil.rmtree(TEMPDIR)

def create_arbo(root, number_of_elements = 2, depth = 1):

    result = []

    if depth == 0:
        return result

    rep = "répertoire".encode("iso-8859-1")
    fic = "fiçhié".encode("iso-8859-1")

    for i in range(number_of_elements):
        srep = os.path.join(root, b"%s%d" % (rep, i))
        os.mkdir(srep)
        result.append(srep.decode("iso-8859-1").encode('utf8'))
        for i in range(number_of_elements):
            sfic = os.path.join(srep, b"%s%d" % (fic, i))
            with open(sfic, 'w', encoding='utf-8') as filep:
                filep.write("test")
            result.append(sfic.decode("iso-8859-1").encode('utf8'))

        result = result + create_arbo(srep, number_of_elements, depth -1)

    return result

class TestCDTE(unittest.TestCase):
    def test_change_arbo_encoding(self):
        number_of_changes = cdte.change_arbo_encoding(TEMPDIR.decode())
        arbo_changed = []
        for root, dirs, files in os.walk(TEMPDIR):
            for filename in files:
                src = os.path.join(root, filename)
                arbo_changed.append(src)
            for dirname in dirs:
                src = os.path.join(root, dirname)
                arbo_changed.append(src)

        expected_arbo = ARBO

        arbo_changed.sort()
        expected_arbo.sort()

        self.assertListEqual(expected_arbo, arbo_changed)
        self.assertEqual(number_of_changes, 18)

if __name__ == '__main__':
    unittest.main()
