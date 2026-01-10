import random
from django.core.management.base import BaseCommand
from analytics.models import TrainingSession, DailyNutrition
from django.contrib.auth import get_user_model
from datetime import timedelta, date

class Command(BaseCommand):
    help = 'Seeds database with realistic dummy analytics data'

    def handle(self, *args, **options):
        # 1. Update existing Training Sessions
        sessions = TrainingSession.objects.all()
        self.stdout.write(f"Updating {sessions.count()} training sessions...")
        
        for s in sessions:
            if s.average_heartrate == 0 or s.calories_burned == 0:
                # Realistic HR: 110-165 bpm
                s.average_heartrate = random.randint(110, 165)
                
                # Realistic Calorie Burn: ~5-12 kcal/min depending on intensity
                # If intensity exists, use it as a factor
                intensity_factor = s.intensity if s.intensity > 0 else 5
                kcal_per_min = 4 + (intensity_factor * 0.8) + random.uniform(-1, 2)
                
                s.calories_burned = int(s.duration_minutes * kcal_per_min)
                s.save()
        
        self.stdout.write(self.style.SUCCESS('Successfully updated training sessions.'))
        
        # 2. Add more data (History) if count is low
        User = get_user_model()
        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.WARNING("No user found. Skipping history generation."))
            return

        current_count = TrainingSession.objects.filter(user=user).count()
        if current_count < 20: 
            self.stdout.write("Generating historical data for last 60 days...")
            today = date.today()
            
            # Generate 30 sessions over last 60 days
            for i in range(30):
                d = today - timedelta(days=random.randint(1, 60))
                # Check if exists
                if not TrainingSession.objects.filter(user=user, date=d).exists():
                    duration = random.choice([30, 45, 60, 75, 90])
                    hr = random.randint(115, 160)
                    intensity = int((hr - 60) / 10) # Crude logic
                    cals = int(duration * (intensity * 1.2 + 3))

                    session = TrainingSession.objects.create(
                        user=user,
                        date=d,
                        # workout_types is M2M, set later if needed
                        duration_minutes=duration,
                        intensity=intensity,
                        calories_burned=cals,
                        average_heartrate=hr
                    )
                     # Also add nutrition for that day
                    if not DailyNutrition.objects.filter(user=user, date=d).exists():
                         DailyNutrition.objects.create(
                             user=user,
                             date=d,
                             calories=random.randint(1800, 3200),
                             protein=random.randint(100, 200),
                             carbs=random.randint(200, 400),
                             fats=random.randint(50, 100)
                         )

            self.stdout.write(self.style.SUCCESS('Added historical data.'))
