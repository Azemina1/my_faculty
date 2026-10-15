

from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('canteen/', views.canteen_view, name='canteen'),
    path('exams/', views.exams_view, name='exams'),
    path('financial/', views.financial_view, name='financial'),
]