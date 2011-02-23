from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import get_language

class ChallengeList(models.Model):
    name = models.CharField(max_length=200, unique=True)
    owner = models.OneToOneField(User, db_index=True, unique=True, related_name="challenge_list")
    deadline = models.DateTimeField(blank=True, null=True)

class Category(models.Model):
    name_en = models.CharField(max_length=200)
    name_fr = models.CharField(max_length=200)
    color = models.CharField(max_length=10)
    def get_name(self):
        
    name = property(get_name)

class Challenge(models.Model):
    challenge_list = models.ForeignKey(ChallengeList, db_index=True, related_name="challenges")
    description = models.CharField(max_length=200)
    category = models.ForeignKey(Category, db_index=True, blank=True, null=True)
    progress = models.PositiveSmallIntegerField(default=0)
    
