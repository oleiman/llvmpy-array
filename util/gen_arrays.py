import numpy as np

np.save("a1", 
        [
         [1,1,1,1,1,1,1],
         [1,1,1,1,1,1,1],
         [1,1,1,1,1,1,1],
         [1,1,1,1,1,1,1]
        ] * 10000)

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