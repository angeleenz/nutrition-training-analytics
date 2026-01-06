import matplotlib
matplotlib.use('Agg')  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import io  # noqa: E402
import base64  # noqa: E402
from .models import DailyNutrition, TrainingSession  # noqa: E402


def get_analytics_graph():
    # 1. Fetch Data
    nutrition_qs = DailyNutrition.objects.all().values('date', 'calories')
    training_qs = TrainingSession.objects.all().values('date', 'intensity', 'duration_minutes')

    # 2. To Pandas
    df_nutrition = pd.DataFrame(nutrition_qs)
    df_training = pd.DataFrame(training_qs)

    if df_nutrition.empty or df_training.empty:
        return None

    # Ensure dates are datetime
    df_nutrition['date'] = pd.to_datetime(df_nutrition['date'])
    df_training['date'] = pd.to_datetime(df_training['date'])

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

    # 5. Save to Base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close(fig)  # Close plot to free memory

    graphic = base64.b64encode(image_png)
    graphic = graphic.decode('utf-8')

    return graphic

