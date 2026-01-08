from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import DailyNutrition, TrainingSession


class StyledFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': (
                    'mt-1 block w-full rounded-md border-gray-300 shadow-sm '
                    'focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border p-2'
                )
            })


class DailyNutritionForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = DailyNutrition
        fields = ['date', 'calories', 'protein', 'fats', 'carbs', 'water_intake']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }


class TrainingSessionForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = TrainingSession
        fields = ['date', 'duration_minutes', 'calories_burned', 'average_heartrate', 'workout_types', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'workout_types': forms.CheckboxSelectMultiple(attrs={'class': 'space-y-2'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # CheckboxSelectMultiple needs different styling usually
        if 'workout_types' in self.fields:
            self.fields['workout_types'].widget.attrs.update({'class': 'grid grid-cols-2 gap-2'})


class SignUpForm(StyledFormMixin, UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'autocomplete': 'username'})
        # UserCreationForm usually has just username, password 1 and 2.
        # But we access them by name if possible, or just apply to all PasswordInputs
        for field_name, field in self.fields.items():
            if field.widget.__class__.__name__ == 'PasswordInput':
                field.widget.attrs.update({'autocomplete': 'new-password'})


class LoginForm(StyledFormMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'autocomplete': 'username'})
        self.fields['password'].widget.attrs.update({'autocomplete': 'current-password'})
