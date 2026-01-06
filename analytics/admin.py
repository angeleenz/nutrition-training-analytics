from django.contrib import admin
from .models import WorkoutType, DailyNutrition, TrainingSession


@admin.register(WorkoutType)
class WorkoutTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'calories_burn_rate')
    search_fields = ('name',)


@admin.register(DailyNutrition)
class DailyNutritionAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'calories', 'protein', 'fats', 'carbs')
    list_filter = ('date', 'user')
    search_fields = ('user__username',)


@admin.register(TrainingSession)
class TrainingSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'duration_minutes', 'intensity')
    list_filter = ('date', 'intensity')
    search_fields = ('user__username', 'notes')
    filter_horizontal = ('workout_types',)

