import random 
import time 
from main import BaseService



class NutritionService(BaseService):
    def __init__(self):
        super().__init__("NutritionService")



    def calorie_logged(self):

        calorie_target = random.randint(2000, 3000) #calories per day
        calorie_intake = random.randint(500, 5000)
        if calorie_intake > calorie_target:
            self.log_event(
                "WARN",
                "Calorie intake exceeded daily target",
                {"calorie_intake": calorie_intake, "calorie_target": calorie_target}
            )
        else:
            self.log_event("INFO", "Calorie intake logged")


    def tracking_meal(self):
            
            if random.choice([1,10]) == 5:
                self.log_event(
                    "ERROR",
                    "Error tracking meal",
                    {"error_details": {"error_code": "ME100", "error_message": "Failed to track meal"}}
                )
            else:
                self.log_event("INFO", "Meal tracked")
    
    def log_water_intake(self):
         
        water_target = random.randint(2000, 3000) #ml per day
        water_intake = random.randint(500, 5000)
        if water_intake < water_target:
            self.log_event(
                "WARN",
                "Water intake below daily target",
                {"water_intake": water_intake, "water_target": water_target}
            )
        else:
            self.log_event("INFO", "Water intake logged")
        
    def log_weight(self):
        weight = random.randint(50, 100)
        if weight < 60:
            self.log_event(
                "WARN",
                "Weight below recommended range",
                {"weight": weight, "recommended_range": "60-80 kg"}
            )
        else:
            self.log_event("INFO", "Weight logged")
    
    def log_muscle_mass(self):
        muscle_mass = random.randint(20, 50)
        if muscle_mass < 30:
            self.log_event(
                "WARN",
                "Muscle mass below recommended range",
                {"muscle_mass": muscle_mass, "recommended_range": "30-40 kg"}
            )
        else:
            self.log_event("INFO", "Muscle mass logged")



    def toggle_intermittent_fasting(self):
        if random.choice([True, False]):
            self.log_event(
                "ERROR",
                "Failed to toggle intermittent fasting",
                {"error_details": {"error_code": "IF500", "error_message": "Failed to update fasting status"}}
            )
        else:
            self.log_event("INFO", "Intermittent fasting toggled")


    def send_heartbeat(self):
        return super().send_heartbeat()

    

    def run_logs(self):
        while True:
            self.calorie_logged()
            self.tracking_meal()
            self.log_water_intake()
            self.log_weight()
            self.log_muscle_mass()
            self.toggle_intermittent_fasting()
            time.sleep(5)


if __name__ == "__main__":
    nutrition = NutritionService()
    try:
        nutrition.run_logs()
    except KeyboardInterrupt:
        nutrition.send_heartbeat()




    

#23625786-e27e-41cd-9471-fdbf8c2523d7