from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

# model: DoubleVideo, including two kinds of videos, LR and HR

class DoubleVideo(models.Model):

    user_id = models.IntegerField(default=0)
    upload_time = models.DateTimeField('uploading time')
    is_collection = models.BooleanField(default=False)
    name = models.CharField(max_length=50)

    # low resolution video path
    lr_video_path = models.CharField(max_length=150)

    # high resolution video path
    hr_video_path = models.CharField(max_length=150)
    
