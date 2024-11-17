import random
from main import BaseService
import time
import schedule
from datetime import datetime
class UserManagementService(BaseService):
    def __init__(self):
        super().__init__("UserManagementService")

    
    def send_registration_log(self):
        registration_log = {
            "node_id": self.node_id,
            "message_type": "REGISTRATION",
            "service_name": self.service_name,
            "timestamp": datetime.now().isoformat(),
        }

        self.log_event("INFO", "Service registered", registration_log)


    def create_user(self, username):
        # Randomly simulate a successful or failed user creation
        if random.choice([True, False]):
            self.log_event(
                "ERROR",
                f"Error creating user '{username}'",
                {"error_details": {"error_code": "400", "error_message": "Username already exists"}}
            )
        else:
            self.log_event("INFO", f"User '{username}' created successfully.")

    def login_user(self, username):
        # Simulate different outcomes for login (INFO, WARN, ERROR)
        outcome = random.choice(['success', 'warn', 'error'])
        if outcome == 'warn':
            self.log_event(
                "WARN",
                f"Slow response time for user '{username}' login",
                {"response_time_ms": 3500, "threshold_limit_ms": 3000}
            )
        elif outcome == 'error':
            self.log_event(
                "ERROR",
                f"Login failed for user '{username}'",
                {"error_details": {"error_code": "401", "error_message": "Invalid credentials"}}
            )
        else:
            self.log_event("INFO", f"User '{username}' logged in successfully.")

    def logout_user(self, username):
        # Randomly simulate successful or failed logout
        if random.choice([True, False]):
            self.log_event(
                "ERROR",
                f"Failed to log out user '{username}'",
                {"error_details": {"error_code": "501", "error_message": "Session timeout"}}
            )
        else:
            self.log_event("INFO", f"User '{username}' logged out successfully.")

    def update_user_credentials(self, username, new_data):
        # Simulate different outcomes for updating credentials (INFO, WARN, ERROR)
        outcome = random.choice(['success', 'warn', 'error'])
        if outcome == 'warn':
            self.log_event(
                "WARN",
                f"Updating credentials for user '{username}' took longer than expected",
                {"response_time_ms": 4500, "threshold_limit_ms": 4000}
            )
        elif outcome == 'error':
            self.log_event(
                "ERROR",
                f"Error updating credentials for user '{username}'",
                {"error_details": {"error_code": "500", "error_message": "Database update failure"}}
            )
        else:
            self.log_event("INFO", f"User '{username}' credentials updated successfully.")

    def simulate_user_operations(self):
        # Call each operation to test logging for various user actions
        username = "john_doe"
        self.create_user(username)

        for _ in range(3):
            action = random.choice(['login', 'logout', 'update'])
            if action == 'login':
                self.login_user(username)
            elif action == 'logout':
                self.logout_user(username)
            elif action == 'update':
                self.update_user_credentials(username, {"password": "new_hashed_password"})

    def run_service(self):
        # Send initial registration log
        self.send_registration_log()
        
        # Run heartbeat and user operations for testing
        while True:
            schedule.run_pending()  # Handle scheduled heartbeats
            self.simulate_user_operations()  # Execute user operations with logs
            time.sleep(10)  # Adjust sleep as needed

# Example usage
if __name__ == "__main__":
    user_service = UserManagementService()
    user_service.run_service()
