import sys, unittest
from MSD import calc_MSD
import numpy



class MSDTests(unittest.TestCase):

    def test_calc_MSD(self):
        pos = numpy.array([
            [ #Frame 1
                [0,0,1],[0,1,0],[1,0,0]
            ],
            [ #Frame 2
                [0,0,2],[0,2,0],[2,0,0]
            ]
        ])

        tau_fs, MSD_x, MSD_y, MSD_z = calc_MSD(pos,1)

        #At first frame, has not moved
        self.assertEqual(MSD_x[0],0)
        self.assertEqual(MSD_y[0],0)
        self.assertEqual(MSD_z[0],0)

        #Second frame, moved one distance
        self.assertEqual(MSD_x[1],1/3)
        self.assertEqual(MSD_y[1],1/3)
        self.assertEqual(MSD_z[1],1/3)




    





if __name__ == "__main__":
    tests = [unittest.TestLoader().loadTestsFromTestCase(MSDTests)]
    testsuite = unittest.TestSuite(tests)
    result = unittest.TextTestRunner(verbosity=0).run(testsuite)
    sys.exit(not result.wasSuccessful())