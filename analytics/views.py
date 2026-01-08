from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import DailyNutrition, TrainingSession
from .forms import DailyNutritionForm, TrainingSessionForm, SignUpForm
from .utils import (
    get_analytics_graph, get_macro_pie_chart, get_workout_type_chart,
    calculate_streaks, get_advanced_stats
)
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.core.paginator import Paginator


# Auth Views
def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})



def get_active_user(request):
    # Only for temporary public access, fallback to admin
    # Now that we have auth, we should strictly use request.user
    if request.user.is_authenticated:
        return request.user
    # Fallback to first user for guest view (optional, or force login)
    return User.objects.first()

@login_required
def dashboard(request):
    """Overview of recent activity with analytics."""
    user = request.user

    # Date Filtering
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Recent lists with simple pagination for "mini-list" feel
    nutrition_qs = DailyNutrition.objects.filter(user=user).order_by('-date')
    training_qs = TrainingSession.objects.filter(user=user).order_by('-date')

    # Apply filtering to lists if present
    if start_date:
        nutrition_qs = nutrition_qs.filter(date__gte=start_date)
        training_qs = training_qs.filter(date__gte=start_date)
    if end_date:
        nutrition_qs = nutrition_qs.filter(date__lte=end_date)
        training_qs = training_qs.filter(date__lte=end_date)

    # Pagination for dashboard (e.g. 5 items per "page")
    nut_paginator = Paginator(nutrition_qs, 5)
    nut_page_number = request.GET.get('n_page')
    recent_nutrition = nut_paginator.get_page(nut_page_number)

    train_paginator = Paginator(training_qs, 5)
    train_page_number = request.GET.get('t_page')
    recent_training = train_paginator.get_page(train_page_number)

    # Generate Graphs
    graph_main = get_analytics_graph(user, start_date, end_date)
    graph_pie = get_macro_pie_chart(user, start_date, end_date)
    graph_bar = get_workout_type_chart(user, start_date, end_date)

    # Advanced Stats
    streaks = calculate_streaks(user)
    adv_stats = get_advanced_stats(user, start_date, end_date)

    context = {
        'recent_nutrition': recent_nutrition,
        'recent_training': recent_training,
        'analytics_graph': graph_main,
        'graph_pie': graph_pie,
        'graph_bar': graph_bar,
        'streaks': streaks,
        'adv_stats': adv_stats,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'analytics/dashboard.html', context)
@login_required
def nutrition_list(request):
    entries_list = DailyNutrition.objects.filter(user=request.user).order_by('-date')

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        entries_list = entries_list.filter(date__gte=start_date)
    if end_date:
        entries_list = entries_list.filter(date__lte=end_date)

    paginator = Paginator(entries_list, 10)  # 10 per page
    page_number = request.GET.get('page')
    entries = paginator.get_page(page_number)
    return render(request, 'analytics/nutrition_list.html', {
        'entries': entries,
        'start_date': start_date,
        'end_date': end_date
    })


@login_required
def nutrition_detail(request, pk):
    entry = get_object_or_404(DailyNutrition, pk=pk, user=request.user)
    return render(request, 'analytics/nutrition_detail.html', {'entry': entry})



@login_required
def nutrition_create(request):
    if request.method == 'POST':
        form = DailyNutritionForm(request.POST)
        if form.is_valid():
            # Check for existing entry on this date
            date_val = form.cleaned_data['date']
            existing = DailyNutrition.objects.filter(user=request.user, date=date_val).first()
            
            if existing:
                # If Overwrite confirmed
                if 'confirm_overwrite' in request.POST:
                    # Initialize form with POST data and Instance to Trigger Update
                    update_form = DailyNutritionForm(request.POST, instance=existing)
                    if update_form.is_valid():
                        update_form.save()
                        messages.success(request, f'Nutrition log for {date_val} updated successfully.')
                        return redirect('nutrition-list')
                
                # Else show conflict warning
                messages.warning(request, f'A log for {date_val} already exists.')
                return render(request, 'analytics/form.html', {
                    'form': form, 
                    'title': 'Log Nutrition',
                    'conflict': True,
                    'conflict_date': date_val
                })

            nutrition = form.save(commit=False)
            nutrition.user = request.user
            nutrition.save()
            messages.success(request, 'Nutrition log added successfully.')
            return redirect('nutrition-list')
    else:
        # Pre-fill date with today
        from datetime import date
        form = DailyNutritionForm(initial={'date': date.today()})
    return render(request, 'analytics/form.html', {'form': form, 'title': 'Log Nutrition'})


@login_required
def nutrition_update(request, pk):
    entry = get_object_or_404(DailyNutrition, pk=pk, user=request.user)
    if request.method == 'POST':
        form = DailyNutritionForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            messages.success(request, 'Nutrition log updated.')
            return redirect('nutrition-list')
    else:
        form = DailyNutritionForm(instance=entry)
    return render(request, 'analytics/form.html', {'form': form, 'title': 'Edit Nutrition'})
@login_required
def training_list(request):
    sessions_list = TrainingSession.objects.filter(user=request.user).order_by('-date')

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        sessions_list = sessions_list.filter(date__gte=start_date)
    if end_date:
        sessions_list = sessions_list.filter(date__lte=end_date)

    paginator = Paginator(sessions_list, 10)
    page_number = request.GET.get('page')
    sessions = paginator.get_page(page_number)
    return render(request, 'analytics/training_list.html', {
        'sessions': sessions,
        'start_date': start_date,
        'end_date': end_date
    })
@login_required
def training_detail(request, pk):
    session = get_object_or_404(TrainingSession, pk=pk, user=request.user)
    return render(request, 'analytics/training_detail.html', {'session': session})



@login_required
def training_create(request):
    if request.method == 'POST':
        form = TrainingSessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.user = request.user
            session.save()
            form.save_m2m()  # Required for ManyToMany
            messages.success(request, 'Workout logged successfully.')
            return redirect('training-list')
    else:
        form = TrainingSessionForm()
    return render(request, 'analytics/form.html', {'form': form, 'title': 'Log Workout'})


@login_required
def training_update(request, pk):
    session = get_object_or_404(TrainingSession, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TrainingSessionForm(request.POST, instance=session)
        if form.is_valid():
            form.save()
            messages.success(request, 'Workout updated.')
            return redirect('training-list')
    else:
        form = TrainingSessionForm(instance=session)
    return render(request, 'analytics/form.html', {'form': form, 'title': 'Edit Workout'})
