from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import get_language, ugettext_lazy as _

class ChallengeList(models.Model):
    name = models.CharField(max_length=200, unique=True)
    owner = models.OneToOneField(User, db_index=True, unique=True, related_name="challenge_list")
    friends = models.ManyToManyField("self", symmetrical=False) 
    def __unicode__(self):
        return self.name

class Category(models.Model):
    name_en = models.CharField(max_length=200)
    name_fr = models.CharField(max_length=200)
    name = property(
        lambda self:getattr(self, "name_"+get_language(), self.name_en),
        lambda self, value:setattr(self, "name_"+get_language(), value)
    )
    red = models.PositiveSmallIntegerField()
    green = models.PositiveSmallIntegerField()
    blue = models.PositiveSmallIntegerField()
    def __unicode__(self):
        return self.name

class Challenge(models.Model):
    description = models.CharField(_("description"), max_length=200, unique=True)
    category = models.ForeignKey(Category, verbose_name=_("category"), db_index=True, blank=True, null=True, on_delete=models.SET_NULL)
    language = models.CharField(max_length=10, null=True, db_index=True)
    def __unicode__(self):
        return repr((
            self.id,
            self.description,
            self.category,
            self.language,
        ))

class ChallengeInstance(models.Model):
    challenge_list = models.ForeignKey(ChallengeList, db_index=True, related_name="challenges")
    challenge = models.ForeignKey(Challenge, db_index=True, related_name="instances")
    progress = models.PositiveSmallIntegerField(default=0)
    due_date = models.DateField(blank=True, null=True, db_index=True)
    origin = models.ForeignKey("self", verbose_name=_("origin"), blank=True, null=True, db_index=True, on_delete=models.SET_NULL) 
    def __unicode__(self):
        return repr((
            self.id,
            self.challenge_list,
            self.challenge,
            self.progress,
            self.due_date,
        ))
