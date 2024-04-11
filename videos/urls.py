from django.urls import path

from . import views

app_name = 'videos'
urlpatterns = [
    path('', views.index, name='index'),
    path('upload', views.upload, name='upload'),
    path('upload_process', views.upload_process, name='upload_process'),
    path('playing', views.playing, name='playing'),
    path('history', views.history, name='history'),
    path('collection', views.collection, name='collection'),
    path('user_login', views.user_login, name='user_login'),
    path('download', views.download, name='download'),
    path('detail/<int:video_id>/', views.detail, name='detail'),
]

