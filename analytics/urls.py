from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('nutrition/', views.nutrition_list, name='nutrition-list'),
    path('nutrition/<int:pk>/', views.nutrition_detail, name='nutrition-detail'),
    path('training/', views.training_list, name='training-list'),
    path('training/<int:pk>/', views.training_detail, name='training-detail'),
    path('nutrition/create/', views.nutrition_create, name='nutrition-create'),
    path('nutrition/<int:pk>/update/', views.nutrition_update, name='nutrition-update'),
    path('training/create/', views.training_create, name='training-create'),
    path('training/<int:pk>/update/', views.training_update, name='training-update'),
    path('nutrition/<int:pk>/delete/', views.nutrition_delete, name='nutrition-delete'),
    path('training/<int:pk>/delete/', views.training_delete, name='training-delete'),
]
