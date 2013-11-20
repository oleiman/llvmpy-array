#!/usr/bin/env python

import ceph as ceph
import numpy as np

np.save("a1", 
        [
         [1,1,1,1,1,1,1],
         [1,1,1,1,1,1,1],
         [1,1,1,1,1,1,1],
         [1,1,1,1,1,1,1]
        ] * 100)
np.save("a2",
        [
         [
          [2,2],
          [2,2]
         ],
         [
          [2,2],
          [2,2]
         ],
         [
          [2,2],
          [2,2]
         ]
        ])

def add(x,y):
    return x + y

def mul(x,y):
    return x * y

ceph.Array.config('/home/oren/code/ceph-private/src/ceph.conf')

a = ceph.Array("bar", "a1.npy")
a.write()
a.fold(add, 0)

print ceph.Array.execute()

b = ceph.Array("baz", "a2.npy")
b.write()

b.fold(mul, 2)

print ceph.Array.execute()


