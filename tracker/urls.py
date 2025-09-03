
from django.urls import path
from . import views

urlpatterns = [
    # The root URL of your site
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('log/', views.log_activity, name="log_activity"),
]