"""
state_estimator.py

2D Kalman-filter based state estimator for a tracked drone.

State:
    [x, y, vx, vy]

Where:
    x, y   = position
    vx, vy = velocity
"""

import numpy as np
from filterpy.kalman import KalmanFilter


class StateEstimator:
    """Estimate drone position and velocity using a Kalman filter."""

    def __init__(self, dt=1 / 30):
        """
        Parameters
        ----------
        dt : float
            Time between measurements in seconds.
        """

        self.dt = float(dt)

        # -------------------------------------------------
        # Create Kalman filter
        # -------------------------------------------------

        self.kf = KalmanFilter(dim_x=4, dim_z=2)

        # State:
        # [x, y, vx, vy]
        self.kf.x = np.zeros((4, 1))

        # -------------------------------------------------
        # State transition matrix
        # -------------------------------------------------

        self.kf.F = np.array([
            [1, 0, self.dt, 0],
            [0, 1, 0, self.dt],
            [0, 0, 1,       0],
            [0, 0, 0,       1]
        ], dtype=float)

        # -------------------------------------------------
        # Measurement matrix
        #
        # Camera measurement gives:
        # [x, y]
        # -------------------------------------------------

        self.kf.H = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0]
        ], dtype=float)

        # -------------------------------------------------
        # Measurement noise
        # -------------------------------------------------

        self.kf.R = np.array([
            [5.0, 0.0],
            [0.0, 5.0]
        ], dtype=float)

        # -------------------------------------------------
        # Process noise
        # -------------------------------------------------

        self.kf.Q = np.eye(4) * 0.01

        # -------------------------------------------------
        # Initial uncertainty
        # -------------------------------------------------

        self.kf.P = np.eye(4) * 10.0

        self.initialized = False

    # =================================================
    # INITIALIZE
    # =================================================

    def initialize(self, x, y):
        """
        Initialize the estimator with the first
        detected drone position.
        """

        self.kf.x = np.array([
            [float(x)],
            [float(y)],
            [0.0],
            [0.0]
        ])

        self.initialized = True

    # =================================================
    # UPDATE TIME STEP
    # =================================================

    def set_dt(self, dt):
        """
        Update the time step.

        This is useful when the camera FPS changes.
        """

        if dt <= 0:
            raise ValueError("dt must be greater than 0.")

        self.dt = float(dt)

        self.kf.F = np.array([
            [1, 0, self.dt, 0],
            [0, 1, 0, self.dt],
            [0, 0, 1,       0],
            [0, 0, 0,       1]
        ], dtype=float)

    # =================================================
    # PREDICT
    # =================================================

    def predict(self):
        """
        Predict the next drone state.

        Returns
        -------
        dict
            Estimated position and velocity.
        """

        if not self.initialized:
            raise RuntimeError(
                "StateEstimator must be initialized before predict()."
            )

        self.kf.predict()

        return self.get_state()

    # =================================================
    # UPDATE POSITION
    # =================================================

    def update_position(self, x, y):
        """
        Update the filter using a camera position measurement.

        Parameters
        ----------
        x, y : float
            Drone center position in pixels.
        """

        if not self.initialized:
            self.initialize(x, y)
            return self.get_state()

        measurement = np.array([
            [float(x)],
            [float(y)]
        ])

        # H is already configured for [x, y].
        self.kf.update(measurement)

        return self.get_state()

    # =================================================
    # UPDATE POSITION + VELOCITY
    # =================================================

    def update_position_velocity(self, x, y, vx, vy):
        """
        Update the filter using position AND velocity.

        Parameters
        ----------
        x, y : float
            Drone position.

        vx, vy : float
            Drone velocity.
        """

        if not self.initialized:
            self.kf.x = np.array([
                [float(x)],
                [float(y)],
                [float(vx)],
                [float(vy)]
            ])

            self.initialized = True

            return self.get_state()

        # -------------------------------------------------
        # Temporarily use a 4-dimensional measurement
        #
        # z = [x, y, vx, vy]
        # -------------------------------------------------

        original_H = self.kf.H.copy()
        original_R = self.kf.R.copy()
        original_dim_z = self.kf.dim_z

        self.kf.dim_z = 4

        self.kf.H = np.eye(4)

        self.kf.R = np.eye(4) * 5.0

        measurement = np.array([
            [float(x)],
            [float(y)],
            [float(vx)],
            [float(vy)]
        ])

        self.kf.update(measurement)

        # -------------------------------------------------
        # Restore normal camera-position measurement mode
        # -------------------------------------------------

        self.kf.dim_z = original_dim_z
        self.kf.H = original_H
        self.kf.R = original_R

        return self.get_state()

    # =================================================
    # GET STATE
    # =================================================

    def get_state(self):
        """
        Return current estimated state.
        """

        return {
            "position": [
                float(self.kf.x[0, 0]),
                float(self.kf.x[1, 0])
            ],
            "velocity": [
                float(self.kf.x[2, 0]),
                float(self.kf.x[3, 0])
            ]
        }


# =====================================================
# TEST
# =====================================================

if __name__ == "__main__":

    estimator = StateEstimator(dt=1 / 30)

    # First detection
    print("Initializing...")
    print(estimator.update_position(100, 200))

    # Simulated tracking
    for i in range(5):

        prediction = estimator.predict()

        print(f"\nPrediction {i + 1}:")
        print(prediction)

        measurement_x = 100 + (i + 1) * 5
        measurement_y = 200 + (i + 1) * 2

        updated = estimator.update_position(
            measurement_x,
            measurement_y
        )

        print("Updated:")
        print(updated)

    # Test position + velocity update
    print("\nTesting position + velocity update:")

    result = estimator.update_position_velocity(
        x=130,
        y=212,
        vx=5,
        vy=2
    )

    print(result)