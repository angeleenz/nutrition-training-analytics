from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Avg, Count
from django.contrib import messages
from .models import DailyNutrition, TrainingSession
from .forms import DailyNutritionForm, TrainingSessionForm
from .utils import get_analytics_graph
from django.contrib.auth.models import User

def get_active_user(request):
    # Helper to get a user for dev purposes if not logged in
    if request.user.is_authenticated:
        return request.user
    return User.objects.first()

def dashboard(request):
    """Overview of recent activity with analytics."""
    recent_nutrition = DailyNutrition.objects.all()[:5]
    recent_training = TrainingSession.objects.all()[:5]
    
    # Generate Graph
    graph = get_analytics_graph()
    
    context = {
        'recent_nutrition': recent_nutrition,
        'recent_training': recent_training,
        'analytics_graph': graph
    }
    return render(request, 'analytics/dashboard.html', context)

def nutrition_list(request):
    entries = DailyNutrition.objects.all()
    return render(request, 'analytics/nutrition_list.html', {'entries': entries})

def nutrition_detail(request, pk):
    entry = get_object_or_404(DailyNutrition, pk=pk)
    return render(request, 'analytics/nutrition_detail.html', {'entry': entry})

def nutrition_create(request):
    if request.method == 'POST':
        form = DailyNutritionForm(request.POST)
        if form.is_valid():
            nutrition = form.save(commit=False)
            nutrition.user = get_active_user(request)
            nutrition.save()
            messages.success(request, 'Nutrition log added successfully.')
            return redirect('nutrition-list')
    else:
        form = DailyNutritionForm()
    return render(request, 'analytics/form.html', {'form': form, 'title': 'Log Nutrition'})

def nutrition_update(request, pk):
    entry = get_object_or_404(DailyNutrition, pk=pk)
    if request.method == 'POST':
        form = DailyNutritionForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            messages.success(request, 'Nutrition log updated.')
            return redirect('nutrition-list')
    else:
        form = DailyNutritionForm(instance=entry)
    return render(request, 'analytics/form.html', {'form': form, 'title': 'Edit Nutrition'})

def training_list(request):
    sessions = TrainingSession.objects.all()
    return render(request, 'analytics/training_list.html', {'sessions': sessions})

def training_detail(request, pk):
    session = get_object_or_404(TrainingSession, pk=pk)
    return render(request, 'analytics/training_detail.html', {'session': session})

def training_create(request):
    if request.method == 'POST':
        form = TrainingSessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.user = get_active_user(request)
            session.save()
            form.save_m2m() # Required for ManyToMany
            messages.success(request, 'Workout logged successfully.')
            return redirect('training-list')
    else:
        form = TrainingSessionForm()
    return render(request, 'analytics/form.html', {'form': form, 'title': 'Log Workout'})

def training_update(request, pk):
    session = get_object_or_404(TrainingSession, pk=pk)
    if request.method == 'POST':
        form = TrainingSessionForm(request.POST, instance=session)
        if form.is_valid():
            form.save()
            messages.success(request, 'Workout updated.')
            return redirect('training-list')
    else:
        form = TrainingSessionForm(instance=session)
    return render(request, 'analytics/form.html', {'form': form, 'title': 'Edit Workout'})


