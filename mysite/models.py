from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    # 添加额外属性
    age = models.PositiveIntegerField(default=0)
    bio = models.TextField(max_length=500, blank=True)