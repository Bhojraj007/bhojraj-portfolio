from django.urls import path
from . import views

app_name = 'public_portal'

urlpatterns = [
    path('', views.home, name='home'),
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog_detail'),
    path('blog/id/<int:pk>/', views.blog_detail_by_id, name='blog_detail_by_id'),
    path('blog/<int:blog_id>/like/', views.blog_like, name='blog_like'),
    path('gallery/', views.gallery, name='gallery'),
    path('ibisap/', views.ibisap, name='ibisap'),
]

