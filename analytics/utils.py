import matplotlib
matplotlib.use('Agg')  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import numpy as np # noqa: E402
import io  # noqa: E402
import base64  # noqa: E402
from .models import DailyNutrition, TrainingSession  # noqa: E402

def _apply_preprocessing(df, cols, smoothing=0, remove_outliers=False):
    """
    Helper to apply smoothing and outlier removal to a Pandas DataFrame.
    """
    if df.empty:
        return df
    
    # Copy to avoid SettingWithCopy warnings
    df = df.copy()

    # 1. Outlier Removal (Z-Score method, simple threshold of 2.0)
    if remove_outliers:
        for col in cols:
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                mean = df[col].mean()
                std = df[col].std()
                if std > 0:
                    # Keep rows within 2 standard deviations
                    df = df[(df[col] >= mean - 2*std) & (df[col] <= mean + 2*std)]
    
    # 2. Smoothing (Rolling Average)
    if smoothing > 1:
        # Ensure sorted by date
        if 'date' in df.columns:
            df = df.sort_values('date')
        
        for col in cols:
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].rolling(window=smoothing, min_periods=1).mean()

    return df


def get_analytics_graph(user, start_date=None, end_date=None, activity_id=None, smoothing=0, remove_outliers=False):
    # 1. Fetch Data
    nutrition_qs = DailyNutrition.objects.filter(user=user)
    training_qs = TrainingSession.objects.filter(user=user)

    if start_date:
        nutrition_qs = nutrition_qs.filter(date__gte=start_date)
        training_qs = training_qs.filter(date__gte=start_date)
    if end_date:
        nutrition_qs = nutrition_qs.filter(date__lte=end_date)
        training_qs = training_qs.filter(date__lte=end_date)
    
    if activity_id and activity_id != 'all':
        training_qs = training_qs.filter(workout_types__id=activity_id)

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
        
        # Preprocessing for Training Data ONLY
        # We don't usually smooth nutrition in this view, but could. Let's smooth training.
        df_training = _apply_preprocessing(
            df_training, 
            cols=['intensity', 'duration_minutes'], 
            smoothing=smoothing, 
            remove_outliers=remove_outliers
        )
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

    title = 'Nutrition vs Intensity'
    if activity_id and activity_id != 'all':
        title += ' (Filtered)'
    if smoothing > 0:
        title += f' [Smooth: {smoothing}]'
    
    plt.title(title)
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


def get_tei_history_chart(user, start_date=None, end_date=None, activity_id=None, smoothing=0, remove_outliers=False):
    qs = TrainingSession.objects.filter(user=user).order_by('date')
    if start_date:
        qs = qs.filter(date__gte=start_date)
    if end_date:
        qs = qs.filter(date__lte=end_date)
    if activity_id and activity_id != 'all':
        qs = qs.filter(workout_types__id=activity_id)

    if not qs.exists():
        return None

    data = []
    for t in qs:
        # Re-calc TEI here to be safe or fetch if stored
        # TEI = (Calories Burned + (Avg HR * Duration / 10)) / 100
        cals = t.calories_burned or 0
        hr = t.average_heartrate or 0
        dur = t.duration_minutes or 0
        tei = (cals + (hr * dur / 10.0)) / 100.0
        data.append({'date': t.date, 'tei': tei})
    
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])

    # Preprocessing
    df = _apply_preprocessing(df, cols=['tei'], smoothing=smoothing, remove_outliers=remove_outliers)

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(df['date'], df['tei'], marker='o', linestyle='-', color='purple', label='TEI')
    
    # Trend line
    if len(df) > 1:
        import numpy as np
        # Use numerical index for trend calculation
        x = np.arange(len(df))
        y = df['tei'].values
        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)
        ax.plot(df['date'], p(x), "r--", alpha=0.6, label='Trend')

    ax.set_ylabel('TEI Score')
    ax.set_title('Training Effectiveness Index Over Time')
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()

    return _fig_to_base64(fig)


def get_correlation_charts(user, start_date=None, end_date=None, activity_id=None, smoothing=0, remove_outliers=False):
    # Fetch Data
    nut_qs = DailyNutrition.objects.filter(user=user)
    train_qs = TrainingSession.objects.filter(user=user)

    if start_date:
        nut_qs = nut_qs.filter(date__gte=start_date)
        train_qs = train_qs.filter(date__gte=start_date)
    if end_date:
        nut_qs = nut_qs.filter(date__lte=end_date)
        train_qs = train_qs.filter(date__lte=end_date)
    
    if activity_id and activity_id != 'all':
        train_qs = train_qs.filter(workout_types__id=activity_id)
    
    # Check if Empty
    if not nut_qs.exists() or not train_qs.exists():
        return None

    df_nut = pd.DataFrame(nut_qs.values('date', 'calories', 'protein', 'fats', 'carbs'))
    df_train = pd.DataFrame(train_qs.values(
        'date', 'duration_minutes', 'average_heartrate', 'calories_burned', 'intensity'
    ))

    # Calculate TEI
    df_train['calories_burned'] = df_train['calories_burned'].fillna(0)
    df_train['average_heartrate'] = df_train['average_heartrate'].fillna(0)
    df_train['duration_minutes'] = df_train['duration_minutes'].fillna(0)
    df_train['tei'] = (
        df_train['calories_burned'] + (df_train['average_heartrate'] * df_train['duration_minutes'] / 10.0)
    ) / 100.0

    # Preprocessing
    df_train = _apply_preprocessing(
        df_train, 
        cols=['tei', 'calories_burned', 'intensity'], 
        smoothing=smoothing, 
        remove_outliers=remove_outliers
    )

    # Merge
    df_nut['date'] = pd.to_datetime(df_nut['date'])
    df_train['date'] = pd.to_datetime(df_train['date'])
    df = pd.merge(df_nut, df_train, on='date', how='inner')

    if len(df) < 5:
        # Not enough data for meaningful scatter plot
        return None

    # We will create 2 scatter plots side-by-side
    # 1. Protein vs TEI
    # 2. Carbs vs Intensity (or Calories Burned)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))

    # Plot 1: Protein vs TEI
    ax1.scatter(df['protein'], df['tei'], color='purple', alpha=0.7)
    ax1.set_xlabel('Protein Intake (g)')
    ax1.set_ylabel('Training Effectiveness (TEI)')
    ax1.set_title('Protein vs TEI')
    
    # Trendline 1
    if len(df) > 1:
        import numpy as np
        z = np.polyfit(df['protein'], df['tei'], 1)
        p = np.poly1d(z)
        ax1.plot(df['protein'], p(df['protein']), "r--", alpha=0.5)

    # Plot 2: Carbs vs Calories Burned
    ax2.scatter(df['carbs'], df['calories_burned'], color='orange', alpha=0.7)
    ax2.set_xlabel('Carbs Intake (g)')
    ax2.set_ylabel('Calories Burned (kcal)')
    ax2.set_title('Carbs vs Energy Output')

    # Trendline 2
    if len(df) > 1:
        z = np.polyfit(df['carbs'], df['calories_burned'], 1)
        p = np.poly1d(z)
        ax2.plot(df['carbs'], p(df['carbs']), "b--", alpha=0.5)

    fig.tight_layout()
    return _fig_to_base64(fig)


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
    # Handle NaNs effectively
    df_train['calories_burned'] = df_train['calories_burned'].fillna(0)
    df_train['average_heartrate'] = df_train['average_heartrate'].fillna(0)
    df_train['duration_minutes'] = df_train['duration_minutes'].fillna(0)

    df_train['tei'] = (
        df_train['calories_burned'] + (df_train['average_heartrate'] * df_train['duration_minutes'] / 10.0)
    ) / 100.0
    stats['avg_tei'] = round(df_train['tei'].mean(), 1) # 1 decimal place

    # Smart Stats: Trend
    if len(df_train) > 2:
        import numpy as np
        try:
            # Sort just in case
            df_curr = df_train.sort_values('date')
            y = df_curr['tei'].values
            x = np.arange(len(y))
            slope, intercept = np.polyfit(x, y, 1)
            
            if slope > 0.05:
                stats['tei_trend'] = "Rising 📈"
                stats['tei_advice'] = "Great job! Your training efficiency is improving."
            elif slope < -0.05:
                stats['tei_trend'] = "Falling 📉"
                stats['tei_advice'] = "Intensity might be dropping. Try increasing heart rate or duration."
            else:
                stats['tei_trend'] = "Stable ➡️"
                stats['tei_advice'] = "Consistent performance. Try mixing up workout types to break plateaus."
            
            # Smart Prediction
            # Predict calories for next 60 min session based on avg intensity
            avg_intensity_factor = df_curr['calories_burned'].sum() / (df_curr['duration_minutes'].sum() or 1)
            predicted_cals = int(60 * avg_intensity_factor)
            stats['prediction'] = f"Estimated burn for 1h workout: ~{predicted_cals} kcal"
            
        except Exception:
            stats['tei_trend'] = "Calculating..."

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
