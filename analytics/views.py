from django.shortcuts import render, get_object_or_404
from django.db.models import Avg, Count
from .models import DailyNutrition, TrainingSession
from .utils import get_analytics_graph

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

def training_list(request):
    sessions = TrainingSession.objects.all()
    return render(request, 'analytics/training_list.html', {'sessions': sessions})

def training_detail(request, pk):
    session = get_object_or_404(TrainingSession, pk=pk)
    return render(request, 'analytics/training_detail.html', {'session': session})

