import os
import shutil
import unittest
import tempfile

import cdte

def setUpModule():
    global tempdir
    tempdir = tempfile.mkdtemp('cae_unittest').encode()
    create_arbo(tempdir, 2, 2)

def tearDownModule():
    global tempdir
    shutil.rmtree(tempdir)

def create_arbo(root, nb = 2, depth = 1):
    if depth == 0:
        return 

    depth = depth - 1

    rep = "répertoire".encode("iso-8859-1")
    fic = "fiçhié".encode("iso-8859-1")

    for i in range(nb):
        srep = os.path.join(root, b"%s%d" % (rep, i))
        os.mkdir(srep)
        for i in range(nb):
            sfic = os.path.join(srep, b"%s%d" % (fic, i))
            with open(sfic, 'w') as f:
                f.write("test")
        
        create_arbo(srep, nb, depth)

def list_arbo(root, nb = 2, depth = 1):
    
    result = []

    if depth == 0:
        return []

    depth = depth - 1

    rep = "répertoire".encode("utf-8")
    fic = "fiçhié".encode("utf-8")

    for i in range(nb):
        srep = os.path.join(root, b"%s%d" % (rep, i))
        result.append(srep)
        for i in range(nb):
            sfic = os.path.join(srep, b"%s%d" % (fic, i))
            result.append(sfic)
        
        result = result + list_arbo(srep, nb, depth)
    
    return result

class TestCDTE(unittest.TestCase):
    def test_change_arbo_encoding(self):
        nb = cdte.change_arbo_encoding(tempdir)
        arbo_changed = []
        for root, dirs, files in os.walk(tempdir):
            for filename in files:
                src = os.path.join(root, filename)
                arbo_changed.append(src)
            for dirname in dirs:  
                src = os.path.join(root, dirname)
                arbo_changed.append(src)
        
        expected_arbo = list_arbo(tempdir, 2 , 2)

        arbo_changed.sort()
        expected_arbo.sort()

        self.assertListEqual(expected_arbo, arbo_changed)
        self.assertEqual(nb, 18)

if __name__ == '__main__':
    unittest.main()
