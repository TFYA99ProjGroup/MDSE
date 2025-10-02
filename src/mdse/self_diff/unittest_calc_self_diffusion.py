import sys, unittest
from calc_self_diffusion import calc_self_diff
import numpy



class SelfDTests(unittest.TestCase):

    def test_calc_MSD(self):
        pos = numpy.array([
            [ #Frame 1
                [0,0,1],[0,1,0],[1,0,0]
            ],
            [ #Frame 2
                [0,0,2],[0,2,0],[2,0,0]
            ]
        ])

        D = calc_self_diff(pos,1)

        #What "slow" built in function predicts

        self.assertAlmostEqual(D,0.16666666666666666)




    





if __name__ == "__main__":
    tests = [unittest.TestLoader().loadTestsFromTestCase(SelfDTests)]
    testsuite = unittest.TestSuite(tests)
    result = unittest.TextTestRunner(verbosity=0).run(testsuite)
    sys.exit(not result.wasSuccessful())