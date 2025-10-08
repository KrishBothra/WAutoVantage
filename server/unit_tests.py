import unittest
from ballsim import Ball, BallSimulator
from demo import BallSimVideoTrack
import numpy as np
import asyncio

class TestBall(unittest.TestCase):
    """
    tests basic ball simulation physics
    """

    def test_initial_position(self):
        """
        check if ball starts at center of frame for
        default frame width and height.
        """
        ball = Ball()
        self.assertAlmostEqual(ball.pos[0], 640 / 2, places=5)
        self.assertAlmostEqual(ball.pos[1], 480 / 2, places=5)

    def test_update_freefall(self):
        """
        check freefall under gravity with (0,0) cm/s initial velocity
        and if ball moved down from initial position.
        """
        ball = Ball(initial_velocity = (0.0, 0.0)) 
        initial_pos = ball.pos.copy()
        ball.update(dt=0.1)
        self.assertGreater(ball.pos[1], initial_pos[1])

    def test_update_no_gravity(self):
        """
        check if ball moves without gravity and 
        default velocity of (1000,1000) cm/s  in intended direction.
        """
        ball = Ball(gravity=0) # use default velocity (1000,1000) cm/s
        initial_pos = ball.pos.copy()
        ball.update(dt=0.1)
        self.assertNotEqual(initial_pos[0], ball.pos[0])
        self.assertNotEqual(initial_pos[1], ball.pos[1])

    def test_collision_with_floor(self):
        """
        place ball near bottom, shoot down with velocity (0,1000)cm/s, 
        check after update that ball stays within frame height.
        """
        ball = Ball()
        ball.pos = np.array([320, 467], dtype=float)  # near bottom
        ball.vel = np.array([0, 1000], dtype=float)
        ball.update(dt=0.1, coeff_of_restitution=1.0)
        self.assertLess(ball.pos[1], ball.h)
    
    def test_collision_with_roof(self):
        """
        place ball near top, shoot up with velocity (0,-1000)cm/s, 
        check after update that ball stays above 0.
        """
        ball = Ball()
        ball.pos = np.array([320, 13], dtype=float)  # near top
        ball.vel = np.array([0, -1000], dtype=float)
        ball.update(dt=0.1, coeff_of_restitution=1.0)
        self.assertGreater(ball.pos[1], 0)
    
    def test_collision_with_left_wall(self):
        """
        place ball near left wall, shoot left with velocity (-1000,0)cm/s, 
        check after update that ball stays right of 0.
        """
        ball = Ball()
        ball.pos = np.array([13, 240], dtype=float)  # near left
        ball.vel = np.array([-1000, 0], dtype=float)
        ball.update(dt=0.1, coeff_of_restitution=1.0)
        self.assertGreater(ball.pos[0], 0)

    def test_collision_with_right_wall(self):
        """
        place ball near right wall, shoot right with velocity (1000,0)cm/s, 
        check after update that ball stays inside frame width.
        """
        ball = Ball()
        ball.pos = np.array([627, 240], dtype=float)  # near right
        ball.vel = np.array([1000, 0], dtype=float)
        ball.update(dt=0.1, coeff_of_restitution=1.0)
        self.assertLess(ball.pos[0], ball.w)

class TestBallSimulator(unittest.TestCase):

    def test_simulator_start_stop(self):
        """
        check if BallSimulator correctly starts and stops simulation thread.
        """
        sim = BallSimulator()
        self.assertFalse(sim.running)
        sim.start()
        self.assertTrue(sim.running)
        sim.stop()
        self.assertFalse(sim.running)

    def test_frame_generation(self):
        """
        check if BallSimulator generates at least one frame after short run, 
        & frame should match expected shape and dtype
        """
        sim = BallSimulator()
        sim.start()
        asyncio.run(asyncio.sleep(0.2))
        sim.stop()
        self.assertFalse(sim.queue.empty())
        frame = sim.queue.get()
        self.assertEqual(frame.shape, (sim.height, sim.width, 3))
        self.assertEqual(frame.dtype, np.uint8)

class TestBallSimVideoTrack(unittest.IsolatedAsyncioTestCase):

    async def test_recv_frame(self):
        """
        check if BallSimVideoTrack successfully receives 
        and formats a frame as bgr24 after BallSimulator starts
        """
        sim = BallSimulator()
        sim.start()
        track = BallSimVideoTrack(sim)

        frame = await track.recv()
        self.assertEqual(frame.format.name, "bgr24")

        sim.stop()

if __name__ == '__main__':
    unittest.main()