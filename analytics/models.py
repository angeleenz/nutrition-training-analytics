from django.db import models
from django.contrib.auth.models import User


class WorkoutType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    calories_burn_rate = models.FloatField(help_text="Average calories burned per hour")

    def __str__(self):
        return self.name


class DailyNutrition(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    calories = models.IntegerField()
    protein = models.FloatField(help_text="Protein in grams")
    fats = models.FloatField(help_text="Fats in grams")
    carbs = models.FloatField(help_text="Carbohydrates in grams")
    water_intake = models.FloatField(help_text="Water in liters", default=0.0)

    class Meta:
        unique_together = ('user', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} - {self.date}"


class TrainingSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    duration_minutes = models.IntegerField()
    calories_burned = models.IntegerField(default=0, help_text="Total calories burned")
    average_heartrate = models.IntegerField(default=0, help_text="Average heart rate (bpm)")
    intensity = models.IntegerField(help_text="Calculated intensity from 1 to 10", editable=False)
    workout_types = models.ManyToManyField(WorkoutType)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-date']

    def save(self, *args, **kwargs):
        # Calculate intensity based on heuristic
        # Avoid division by zero
        duration = self.duration_minutes if self.duration_minutes > 0 else 1
        
        # Factor 1: Heart Rate (assuming max HR ~190, so 190=100% effort)
        # Contribution: 0-6 points
        hr_score = (self.average_heartrate / 190) * 6
        
        # Factor 2: Caloric Burn Rate (assuming 15 kcal/min is very high intensity)
        # Contribution: 0-4 points
        cal_rate = self.calories_burned / duration
        cal_score = (cal_rate / 15) * 4
        
        calculated_intensity = int(hr_score + cal_score)
        # Clamp to 1-10
        self.intensity = max(1, min(10, calculated_intensity))
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.date} ({self.duration_minutes} min)"
