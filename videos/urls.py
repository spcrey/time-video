from django.urls import path

from . import views

app_name = 'videos'
urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload, name='upload'),
    path('collection/', views.collection, name='collection'),
    path('history/', views.history, name='history'),
    path('process/', views.process, name='process'),
    path('user_login/', views.user_login, name='user_login'),
    path('user_logout/', views.user_logout, name='user_logout'),
    path('add_collection/<int:video_id>/', views.add_collection, name='add_collection'),
    path('del_collection/<int:video_id>/', views.del_collection, name='del_collection'),
    path('detail/<int:video_id>/', views.detail, name='detail'),
    path('download/<int:video_id>/', views.download, name='download'),
    path('template/', views.template, name='template'),
]
