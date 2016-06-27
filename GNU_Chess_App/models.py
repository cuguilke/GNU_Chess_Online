from django.db import models

from django.contrib.auth.models import User
# Create your models here.
 
class Chess_User(models.Model):
	class Meta:
		unique_together = (('user_id','username'),) 
	username = models.CharField(max_length=20) 
	user_id = models.IntegerField()
 
