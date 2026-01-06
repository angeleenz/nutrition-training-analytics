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
    intensity = models.IntegerField(help_text="Intensity from 1 to 10")
    workout_types = models.ManyToManyField(WorkoutType)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} - {self.date} ({self.duration_minutes} min)"
