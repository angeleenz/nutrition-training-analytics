import matplotlib
matplotlib.use('Agg')  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import io  # noqa: E402
import base64  # noqa: E402
from .models import DailyNutrition, TrainingSession  # noqa: E402


def get_analytics_graph(user, start_date=None, end_date=None):
    # 1. Fetch Data
    nutrition_qs = DailyNutrition.objects.filter(user=user)
    training_qs = TrainingSession.objects.filter(user=user)

    if start_date:
        nutrition_qs = nutrition_qs.filter(date__gte=start_date)
        training_qs = training_qs.filter(date__gte=start_date)
    if end_date:
        nutrition_qs = nutrition_qs.filter(date__lte=end_date)
        training_qs = training_qs.filter(date__lte=end_date)

    nutrition_vals = nutrition_qs.values('date', 'calories')
    training_vals = training_qs.values('date', 'intensity', 'duration_minutes')

    # 2. To Pandas
    df_nutrition = pd.DataFrame(nutrition_vals)
    df_training = pd.DataFrame(training_vals)

    if df_nutrition.empty and df_training.empty:
        return None

    # Ensure dates are datetime
    if not df_nutrition.empty:
        df_nutrition['date'] = pd.to_datetime(df_nutrition['date'])
    else:
        df_nutrition = pd.DataFrame(columns=['date', 'calories'])

    if not df_training.empty:
        df_training['date'] = pd.to_datetime(df_training['date'])
    else:
        df_training = pd.DataFrame(columns=['date', 'intensity', 'duration_minutes'])

    # 3. Merge
    df = pd.merge(df_nutrition, df_training, on='date', how='outer')
    df = df.sort_values('date').fillna(0)  # Fill missing with 0 for plotting

    # 4. Plot
    fig, ax1 = plt.subplots(figsize=(10, 5))

    # Bar chart for Calories (Axis 1)
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Calories (kcal)', color='tab:blue')
    ax1.bar(df['date'], df['calories'], color='tab:blue', alpha=0.6, label='Calories')
    ax1.tick_params(axis='y', labelcolor='tab:blue')

    # Line chart for Intensity (Axis 2)
    ax2 = ax1.twinx()
    ax2.set_ylabel('Intensity (1-10)', color='tab:red')
    ax2.plot(df['date'], df['intensity'], color='tab:red', marker='o', linewidth=2, label='Intensity')
    ax2.tick_params(axis='y', labelcolor='tab:red')
    ax2.set_ylim(0, 11)

    plt.title('Nutrition Intake vs Training Intensity')
    fig.tight_layout()

    return _fig_to_base64(fig)


def get_macro_pie_chart(user, start_date=None, end_date=None):
    # Fetch Data
    nutrition_qs = DailyNutrition.objects.filter(user=user)
    if start_date:
        nutrition_qs = nutrition_qs.filter(date__gte=start_date)
    if end_date:
        nutrition_qs = nutrition_qs.filter(date__lte=end_date)

    nutrition_vals = nutrition_qs.values('protein', 'fats', 'carbs')
    if not nutrition_vals:
        return None

    df = pd.DataFrame(nutrition_vals)

    # Sum macros
    total_protein = df['protein'].sum()
    total_fats = df['fats'].sum()
    total_carbs = df['carbs'].sum()

    if total_protein + total_fats + total_carbs == 0:
        return None

    labels = ['Protein', 'Fats', 'Carbs']
    sizes = [total_protein, total_fats, total_carbs]
    colors = ['#ff9999', '#66b3ff', '#99ff99']

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    plt.title('Macronutrient Distribution (All Time)')

    return _fig_to_base64(fig)


def get_workout_type_chart(user, start_date=None, end_date=None):
    from django.db.models import Count
    # We need to query WorkoutType usage counts through TrainingSession
    qs = TrainingSession.objects.filter(user=user)
    if start_date:
        qs = qs.filter(date__gte=start_date)
    if end_date:
        qs = qs.filter(date__lte=end_date)

    data = qs.values('workout_types__name').annotate(count=Count('workout_types__name')).order_by('-count')

    if not data:
        return None

    labels = [d['workout_types__name'] for d in data if d['workout_types__name']]
    counts = [d['count'] for d in data if d['workout_types__name']]

    if not labels:
        return None

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(labels, counts, color='teal')
    ax.set_xlabel('Workout Type')
    ax.set_ylabel('Frequency')
    plt.title('Workout Type Frequency')
    plt.xticks(rotation=45)
    fig.tight_layout()

    return _fig_to_base64(fig)


def _fig_to_base64(fig):
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close(fig)  # Close plot to free memory

    graphic = base64.b64encode(image_png)
    graphic = graphic.decode('utf-8')
    return graphic



def calculate_streaks(user):
    from datetime import date, timedelta

    # Get all dates user trained
    dates = list(TrainingSession.objects.filter(user=user).values_list('date', flat=True).order_by('date').distinct())

    if not dates:
        return {'current': 0, 'longest': 0}

    # Longest Streak
    longest_streak = 1
    current_temp = 1

    for i in range(1, len(dates)):
        if dates[i] == dates[i-1] + timedelta(days=1):
            current_temp += 1
        else:
            longest_streak = max(longest_streak, current_temp)
            current_temp = 1
    longest_streak = max(longest_streak, current_temp)

    # Current Streak
    today = date.today()
    current_streak = 0

    # Check if streak includes today or ended yesterday
    if today in dates:
        current_streak = 1
        check_date = today - timedelta(days=1)
    elif (today - timedelta(days=1)) in dates:
        current_streak = 1
        check_date = today - timedelta(days=2)
    else:
        # Streak broken
        return {'current': 0, 'longest': longest_streak}

    while check_date in dates:
        current_streak += 1
        check_date -= timedelta(days=1)

    return {'current': current_streak, 'longest': longest_streak}
def get_advanced_stats(user, start_date=None, end_date=None):
    # Nutrition Data
    nut_qs = DailyNutrition.objects.filter(user=user)
    train_qs = TrainingSession.objects.filter(user=user)

    if start_date:
        nut_qs = nut_qs.filter(date__gte=start_date)
        train_qs = train_qs.filter(date__gte=start_date)
    if end_date:
        nut_qs = nut_qs.filter(date__lte=end_date)
        train_qs = train_qs.filter(date__lte=end_date)

    df_nut = pd.DataFrame(nut_qs.values('date', 'calories', 'protein', 'fats', 'carbs'))
    df_train = pd.DataFrame(train_qs.values(
        'date', 'duration_minutes', 'average_heartrate', 'calories_burned', 'intensity'
    ))

    stats = {
        'avg_tei': 0,
        'correlation_matrix': None,
        'msg': 'No sufficient data'
    }

    if df_train.empty:
        return stats

    # Calculate TEI per session
    # TEI = (Calories Burned + (Avg HR * Duration / 10)) / 100
    # Note: Just a heuristic index
    df_train['tei'] = (
        df_train['calories_burned'] + (df_train['average_heartrate'] * df_train['duration_minutes'] / 10.0)
    ) / 100.0
    stats['avg_tei'] = round(df_train['tei'].mean(), 2)

    if df_nut.empty:
        return stats

    # Merge for Correlation
    # Ensure dates are datetime
    df_nut['date'] = pd.to_datetime(df_nut['date'])
    df_train['date'] = pd.to_datetime(df_train['date'])

    df_merged = pd.merge(df_nut, df_train, on='date', how='inner')

    if len(df_merged) < 3:
        stats['msg'] = "Need at least 3 overlapping days of data for correlation."
        return stats

    # Correlation Analysis
    # We want corr(Nutrition vs Efficacy)
    # Efficacy metrics: tei, intensity, calories_burned
    # Nutrition metrics: calories, protein, carbs, fats

    focus_cols = ['calories', 'protein', 'carbs', 'fats', 'tei', 'intensity', 'calories_burned']
    # Filter only existing columns
    focus_cols = [c for c in focus_cols if c in df_merged.columns]

    corr_matrix = df_merged[focus_cols].corr()

    # Formatting for template: List of (Nutrient, WorkMetric, Value)
    correlations = []
    nutrients = ['calories', 'protein', 'carbs', 'fats']
    targets = ['tei', 'calories_burned']

    for nut in nutrients:
        for targ in targets:
            if nut in corr_matrix.columns and targ in corr_matrix.columns:
                val = corr_matrix.loc[nut, targ]
                if not pd.isna(val):
                    correlations.append({
                        'nutrient': nut.title(),
                        'metric': 'TEI' if targ == 'tei' else 'Cals Burned',
                        'value': round(val, 2)
                    })

    stats['correlations'] = correlations
    stats['msg'] = 'Success'

    return stats
