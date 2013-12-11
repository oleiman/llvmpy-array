#!/usr/bin/env python

from ceph_array import CephArray
import numpy as np

def add(x,y):
    return x + y

def mul(x,y):
    return x * y

CephArray.config('/home/oren/code/ceph-private/src/ceph.conf', 'some_pool')

a = CephArray("test", "a1.npy")
a.write()
# a = CephArray("foobarbazqux37")
a.fold(add, 0)

b = CephArray("baz", "a2.npy")
b.write()

b.fold(mul, 2)

print CephArray.execute()

