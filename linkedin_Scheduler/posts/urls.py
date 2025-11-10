"""
URL configuration for linkdin_posts project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from . import views
urlpatterns = [
    path('', views.home, name='home'),
    path('schedule/', views.schedule_post, name='schedule_post'),
    path('api/posts/', views.api_get_scheduled_posts, name='api_posts'),
    path('api/delete-post/', views.api_delete_post, name='api_delete_post'),
    path('api/update-post/', views.api_update_post, name='api_update_post'),
    path('api/reschedule-post/', views.api_reschedule_post, name='api_reschedule_post'),
    path('api/stats/', views.api_get_stats, name='api_stats'),
]
