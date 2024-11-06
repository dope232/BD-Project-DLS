import random
import time
from services.main import BaseService

class WorkoutService(BaseService):
    def __init__(self):
        super().__init__("WorkoutService")

    def log_exercise_tracking(self):
        # Randomly decide to log an ERROR for tracking failure
        if random.choice([True, False]):
            self.log_event(
                "ERROR",
                "Error tracking exercise session",
                {"error_details": {"error_code": "E101", "error_message": "Failed to track exercise"}}
            )
        else:
            self.log_event("INFO", "Tracking exercise session")

    def log_set_completion(self):
        # Simulate a WARN if set completion time exceeds a threshold
        completion_time_ms = random.randint(2000, 8000)  # Random completion time
        threshold_time_ms = 5000
        if completion_time_ms > threshold_time_ms or random.choice([True, False]):
            self.log_event(
                "WARN",
                "Set completion time exceeded threshold",
                {"response_time_ms": completion_time_ms, "threshold_limit_ms": threshold_time_ms}
            )
        else:
            self.log_event("INFO", "Set completed")

    def log_rest_period(self):
        # Occasionally log a warning if rest period is unusually long
        rest_duration = random.randint(1000, 10000)  # Random rest duration
        if rest_duration > 8000 or random.choice([True, False]):
            self.log_event(
                "WARN",
                "Rest period exceeded recommended duration",
                {"rest_duration_ms": rest_duration}
            )
        else:
            self.log_event("INFO", "Rest period started")

    def log_personal_record(self):
        # Randomly simulate an ERROR on personal record achievement
        if random.choice([True, False]):
            self.log_event(
                "ERROR",
                "Failed to save personal record",
                {"error_details": {"error_code": "PR500", "error_message": "Database save error"}}
            )
        else:
            self.log_event("INFO", "New personal record achieved")

    def run_logs(self):
        # Call each log method at intervals for testing
        while True:
            self.log_exercise_tracking()
            self.log_set_completion()
            self.log_rest_period()
            self.log_personal_record()
            time.sleep(5)  # Adjust sleep as needed to control log frequency

# Example usage
if __name__ == "__main__":
    workout_service = WorkoutService()
    workout_service.run_logs()  