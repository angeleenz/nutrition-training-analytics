import matplotlib
matplotlib.use('Agg')  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import io  # noqa: E402
import base64  # noqa: E402
from .models import DailyNutrition, TrainingSession  # noqa: E402


def get_analytics_graph(user):
    # 1. Fetch Data
    nutrition_qs = DailyNutrition.objects.filter(user=user).values('date', 'calories')
    training_qs = TrainingSession.objects.filter(user=user).values('date', 'intensity', 'duration_minutes')

    # 2. To Pandas
    df_nutrition = pd.DataFrame(nutrition_qs)
    df_training = pd.DataFrame(training_qs)

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


def get_macro_pie_chart(user):
    # Fetch Data
    nutrition_qs = DailyNutrition.objects.filter(user=user).values('protein', 'fats', 'carbs')
    if not nutrition_qs:
        return None
        
    df = pd.DataFrame(nutrition_qs)
    
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


def get_workout_type_chart(user):
    from django.db.models import Count
    # We need to query WorkoutType usage counts through TrainingSession
    # This is easier via Django ORM directly than pandas merge for M2M
    data = TrainingSession.objects.filter(user=user).values('workout_types__name').annotate(count=Count('workout_types__name')).order_by('-count')
    
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


