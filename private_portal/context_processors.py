from .models import DashboardSettings, Photo, Video, Post, Blog, Todo
from django.contrib.auth import get_user_model
from django.db import connection

def dashboard_settings(request):
    """
    Context processor to inject DashboardSettings into all templates.
    """
    settings = DashboardSettings.objects.first()
    return {
        'dashboard_settings': settings
    }

def admin_stats(request):
    """
    Provides real-time stats for the Mission Control Dashboard.
    """
    User = get_user_model()
    # Basic metrics
    users_count = User.objects.count()
    total_content = (
        Photo.objects.count() + 
        Video.objects.count() + 
        Post.objects.count() + 
        Blog.objects.count() + 
        Todo.objects.count()
    )
    
    # Mock uptime (simplified)
    uptime = "99.98%" 
    
    return {
        'sys_users': users_count,
        'sys_content': total_content,
        'sys_uptime': uptime,
        'sys_queries': len(connection.queries) if connection.queries else "24ms"
    }
