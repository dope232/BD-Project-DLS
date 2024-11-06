import random
import time
from main import BaseService

class GoalsService(BaseService):
    def __init__(self):
        super().__init__("GoalsService")

    def goals_settings(self):
        goal_months=random.randrange(1,12)
        if(goal_months!=(1 or 3 or 6 or 12)):
            self.log_event(
                "WARN",
                "Please set the Goal as 1 or 3 or 6 or 12 months",
                {"Months":goal_months}
            )
        else:
            self.log_event("INFO", "Calorie intake logged")



    def progress_updates(self):
        curr_progress=0
        milestones = {25, 50, 75, 100}
        curr_streak_goals=0
        reached_milestones = set()
        while(curr_progress<100):
            progress_amt=random.randrange(1,15)
            curr_progress=curr_progress+progress_amt
            if(curr_progress%10==0):
                self.log_event("INFO",f"{curr_progress}% progress reached")
                continue

            for milestone in milestones:
                if curr_progress >= milestone and milestone not in reached_milestones:
                    self.milestone(milestone)
                    reached_milestones.add(milestone)
        if(curr_progress!=100):
            curr_streak_goals=0
            self.streak_tracking(curr_streak_goals)
            self.log_event("WARN",f"100% progress not reached")
        elif curr_progress==100:
            curr_streak_goals+=1
            self.streak_tracking(curr_streak_goals)    


    def milestone(self,milestone):
        self.log_event("INFO", f"Milestone achieved: {milestone}% completed!")


    def streak_tracking(self,goal_streak):
        if goal_streak>0:
            self.log_event("INFO",f"Current Streak: {goal_streak}")
        elif goal_streak==0:
            self.log_event("WARNING","Goal Streak Reset")


    def run_logs(self):
        while True:
            self.goals_settings()
            self.progress_updates()
            time.sleep(5)        


if __name__ == "__main__":
    workout_service = GoalsService()
    workout_service.run_logs() 



