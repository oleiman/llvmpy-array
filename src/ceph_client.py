#!/usr/bin/env python

from ceph import Array
import numpy as np

def add(x,y):
    return x + y

def mul(x,y):
    return x * y

Array.config('/home/oren/code/ceph-private/src/ceph.conf')


a = Array("foobarbazqux37", "a1.npy")
a.write()
# a = Array("someobject")
a.fold(add, 0)

b = Array("baz", "a2.npy")
b.write()

b.fold(mul, 2)

print Array.execute()

