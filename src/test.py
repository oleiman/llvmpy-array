# TODO: improve unit tests

import unittest,os,random

from ceph_array import CephArray

class TestCephArray(unittest.TestCase):
    def setUp(self):
        CephArray.config(os.environ['CEPH_CONF'], 'test')
        self.test_oid_1 = "test%d" % random.getrandbits(64)
        self.test_oid_2 = "test%d" % random.getrandbits(64)

    def testWrite(self):
        a = CephArray(self.test_oid_1, "a1.npy")
        a.write()
        result = CephArray.execute()
        self.assertEqual(0, result[0]['return'])
        self.assertEqual(self.test_oid_1, result[0]['oid'])

    def testWriteAndFold(self):
        def add(x, y):
            return x + y
        a = CephArray(self.test_oid_2, "a1.npy")
        a.write()
        a.fold(add, 0)
        a.fold(add, 15)
        result = CephArray.execute()
        self.assertEqual(0, result[0]['return'])
        self.assertEqual(280000, result[1]['return'])
        self.assertEqual(280015, result[2]['return'])
        
if __name__ == '__main__':
    unittest.main()
