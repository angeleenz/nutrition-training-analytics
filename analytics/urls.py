from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('nutrition/', views.nutrition_list, name='nutrition-list'),
    path('nutrition/<int:pk>/', views.nutrition_detail, name='nutrition-detail'),
    path('training/', views.training_list, name='training-list'),
    path('training/<int:pk>/', views.training_detail, name='training-detail'),
    # Placeholders for future create/update/delete
    path('nutrition/create/', views.dashboard, name='nutrition-create'), # Temporary redirect
    path('nutrition/<int:pk>/update/', views.dashboard, name='nutrition-update'), # Temporary redirect
    path('training/create/', views.dashboard, name='training-create'), # Temporary redirect
    path('training/<int:pk>/update/', views.dashboard, name='training-update'), # Temporary redirect
]
