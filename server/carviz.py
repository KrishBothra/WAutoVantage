import numpy as np
import cv2
import time
import threading 
import queue

class Ball:
    """
    Simulates a size 7 Basket ball(75cm circumference ~12cm radius) under gravity, bouncing off the walls of the window.
    All units: position in px (cm), velocity in px/s (cm/s), acceleration in px/s^2 (cm/s^2), timestep dt (s).
    All colisions are perfectly elastic by default i.e. there are no losses. chnage coeff_of_restitution for realistic simulation.
    computes timestep dt for state update, in seconds, based on the fps required (currently set to 60).  
    """
    def __init__(self, radius=12, window_width=640, window_height=480, gravity=980, initial_velocity=(1000.0, 1000.0)):
        self.radius = radius
        self.w = window_width
        self.h = window_height
        self.gravity = gravity
        # Starting position and velocity 
        self.pos = np.array([self.w / 2, self.h / 2], dtype=float) 
        self.vel = np.array(initial_velocity, dtype=float)

    def update(self, dt, coeff_of_restitution=1.0):
        """
        update position and velocity over timestep dt,
        applying gravity and bouncing off the walls.
        """
        self.vel[1] += self.gravity * dt
        self.pos += self.vel * dt

        # check for collision with top/bottom walls
        if self.pos[1] - self.radius < 0:
            self.pos[1] = self.radius
            self.vel[1] *= -coeff_of_restitution
        elif self.pos[1] + self.radius > self.h:
            self.pos[1] = self.h - self.radius
            self.vel[1] *= -coeff_of_restitution
        
        # check for collision with left/right walls
        if self.pos[0] - self.radius < 0:
            self.pos[0] = self.radius
            self.vel[0] *= -coeff_of_restitution
        elif self.pos[0] + self.radius > self.w:
            self.pos[0] = self.w - self.radius
            self.vel[0] *= -coeff_of_restitution

    def draw(self, frame):
        """
        Render the ball on the frame.
        """
        center = (int(round(self.pos[0])), int(round(self.pos[1])))
        cv2.circle(frame, center, self.radius, (0, 120, 255), -1)

        return center

class CarVisualizer:
    def __init__(self, width=640, height=480, fps=60, gravity=980, velocity=(1000.0, 1000.0), restitution=0.98):
        self.width = width
        self.height = height
        self.fps = fps
        self.gravity = gravity
        self.initial_velocity = velocity
        self.restitution = restitution
        self.current_center = None
        self.frame_interval = 1.0 / fps
        self.running = False
        self.thread = None
        self.queue = queue.Queue(maxsize=10)

    def start(self):
        """
        Start sim thread
        """
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()

    def stop(self):
        """
        Stops sim thread
        """
        if self.running:
            self.running = False
            self.thread.join()

    def _run(self):
        """
        Main simulation fucntion that calls for physics update and pushes frames to queue based on fps
        """
        ball = Ball(radius=12, window_width=self.width, window_height=self.height,
                    gravity=self.gravity, initial_velocity=self.initial_velocity)
        # Env Setup
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        prev_time = time.perf_counter()

        while self.running:
            loop_start = time.perf_counter()
            #elapsed time since last physics update
            dt = loop_start - prev_time
            dt = min(self.frame_interval, dt) # in case of compute lag, cap to avoid errorous behavious

            frame.fill(0)  # Reset Env for new frame
            ball.update(dt, coeff_of_restitution=self.restitution)
            self.current_center = ball.draw(frame)

            # Push frame into queue
            try:
                self.queue.put_nowait(frame.copy())
            except queue.Full:
                try:
                    self.queue.get_nowait()
                except queue.Empty:
                    pass
                self.queue.put_nowait(frame.copy())
            prev_time = loop_start

            loop_end = time.perf_counter()
            sleep_time = self.frame_interval - (loop_end - loop_start)
            if sleep_time > 0:
                time.sleep(sleep_time)

