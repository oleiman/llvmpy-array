#!/usr/bin/env python

import ceph as ceph
import numpy as np

np.save("a1", 
        [
         [1,1,1,1,1,1,1],
         [1,1,1,1,1,1,1],
         [1,1,1,1,1,1,1],
         [1,1,1,1,1,1,1]
        ])
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

add = lambda x,y: x + y
mul = lambda x,y: x * y

a = ceph.CephArray.from_npy_file("foo", "a1.npy")
a.write()

b = ceph.CephArray.from_npy_file("bar", "a2.npy")
b.write()

a.fold(add, 0, "sum")
b.fold(mul, 1, "mul")

ceph.CephArray.execute()


