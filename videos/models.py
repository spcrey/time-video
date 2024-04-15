from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

# model: DoubleVideo, including two kinds of videos, LR and HR

class DoubleVideo(models.Model):
    name = models.CharField(max_length=50)
    create_user_id = models.IntegerField()
    upload_time = models.DateTimeField('uploading time')
    is_collection = models.BooleanField(default=False)
    is_complete = models.BooleanField(default=False)
    lr_video_path = models.CharField(max_length=150)
    hr_video_path = models.CharField(max_length=150)
    image_path = models.CharField(max_length=150)
    
