from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Instance(models.Model):
    name = models.CharField(max_length=200, unique=True, blank=False)
    min_pref_len = models.PositiveIntegerField(default=0, blank=False)
    max_pref_len = models.PositiveIntegerField(default=0, blank=False)
    stage_choices = (
        ('N','New'),
        ('P','Project Proposal'),
        ('L','Advisor Ranking Levels'),
        ('S','Student Preference Collection'),
        ('C','Closed'),
        ('R','Results Available')
    )
    stage = models.CharField(max_length=1,choices=stage_choices,default='N')

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=2,choices=(("ST","Student"),("AC","Academic"),("AD","Admin")), default="ST")
    unique_id = models.CharField(max_length=8, unique=True, blank=False)

    def __str__(self):
        return self.user.get_full_name()

class Student(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    instance = models.ForeignKey(Instance, on_delete=models.CASCADE)
    upper_cap = models.PositiveIntegerField(default=1, blank=False)
    lower_cap = models.PositiveIntegerField(default=0, blank=False)

    def __str__(self):
        return self.user_profile.user.get_full_name()

class Admin(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    super_admin = models.BooleanField(blank=False, default=False)

    def __str__(self):
        return self.user_profile.user.get_full_name()

class Manager(models.Model):
    admin = models.ForeignKey(Admin, on_delete=models.CASCADE)
    instance = models.ForeignKey(Instance, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.admin) + " managing " + str(self.instance)

class Academic(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    instance = models.ForeignKey(Instance, on_delete=models.CASCADE)
    upper_cap = models.PositiveIntegerField(default=1, blank=False)
    lower_cap = models.PositiveIntegerField(default=0, blank=False)

    def __str__(self):
        return self.user_profile.user.get_full_name()

class Project(models.Model):
    name = models.CharField(max_length=200, blank=False)
    description = models.CharField(max_length=1000, blank=False)
    upper_cap = models.PositiveIntegerField(default=1, blank=False)
    lower_cap = models.PositiveIntegerField(default=0, blank=False)
    instance = models.ForeignKey(Instance, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Choice(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    rank = models.PositiveIntegerField(default=1, blank=False)

    def __str__(self):
        return str(self.student) + " ranks " + str(self.project) + " their choice number " + str(self.rank)

class AdvisorLevel(models.Model):
    academic = models.ForeignKey(Academic, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    level = models.PositiveIntegerField(choices=((1, "Expert Knowledge"), (2, "High Knowledge"), (3, "Good Knowledge")), default=1, blank=False)
    
    def __str__(self):
        return str(self.academic) + " can mentor " + str(self.project) + " at level " + str(self.level)

class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    academic = models.ForeignKey(Academic, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.student) + " assigned to " + str(self.project) + " supervised by " + str(self.academic)

