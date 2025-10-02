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
        self.assertAlmostEqual(D,0.16666666666666666)

        #Comparing to built-in painfully slow function
        D_traj = calc_self_diff("test.traj")

        #Takes long time to re-compute
        """
        from ase.md.analysis import DiffusionCoefficient
        test_traj = Trajectory("test.traj")
        dc = DiffusionCoefficient(test_traj,timestep=50)
        D_ase = dc.slopes[0]
        D_ase_tot = numpy.mean(D_ase)
        """
        D_ase_tot = 7.637147636017926e-06

        relative_error = abs(D_traj - D_ase_tot)/D_ase_tot
        self.assertLessEqual(relative_error,0.008)


    





if __name__ == "__main__":
    tests = [unittest.TestLoader().loadTestsFromTestCase(SelfDTests)]
    testsuite = unittest.TestSuite(tests)
    result = unittest.TextTestRunner(verbosity=0).run(testsuite)
    sys.exit(not result.wasSuccessful())