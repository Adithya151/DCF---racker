
from django.urls import path
from . import views

urlpatterns = [
    # The root URL of your site
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('log/', views.log_activity, name="log_activity"),
    path('reset/', views.reset_dashboard, name='reset_dashboard'),
    
    path('set_dashboard_flag/', views.set_dashboard_flag, name='set_dashboard_flag'),
]