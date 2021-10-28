from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Instance(models.Model):
    name = models.CharField(max_length=200, unique=True, blank=False)
    level = models.IntegerField(default=0, blank=False)

    def __str__(self):
        return self.name

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    matric_number = models.CharField(max_length=8, unique=True, blank=False)
    instance = models.ForeignKey(Instance, on_delete=models.CASCADE)
    upper_cap = models.IntegerField(default=1, blank=False)
    lower_cap = models.IntegerField(default=0, blank=False)

    def __str__(self):
        return self.matric_number

class Admin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    super_admin = models.BooleanField(blank=False, default=False)

    def __str__(self):
        return self.user.get_full_name()

class Manager(models.Model):
    admin = models.ForeignKey(Admin, on_delete=models.CASCADE)
    instance = models.ForeignKey(Instance, on_delete=models.CASCADE)

    def __str__(self):
        return self.admin + " managing " + self.instance

class Academic(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    staff_id = models.CharField(max_length=6, unique=True, blank=False)
    instance = models.ForeignKey(Instance, on_delete=models.CASCADE)
    upper_cap = models.IntegerField(default=1, blank=False)
    lower_cap = models.IntegerField(default=0, blank=False)

    def __str__(self):
        return self.user.get_full_name()

class Project(models.Model):
    name = models.CharField(max_length=200, blank=False)
    description = models.CharField(max_length=1000, blank=False)
    upper_cap = models.IntegerField(default=1, blank=False)
    lower_cap = models.IntegerField(default=0, blank=False)
    instance = models.ForeignKey(Instance, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Choice(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    rank = models.IntegerField(default=1, blank=False)

    def __str__(self):
        return self.student + " ranks " + self.project + " rank " + self.rank

class AdvisorLevel(models.Model):
    academic = models.ForeignKey(Academic, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    level = models.IntegerField(choices=((1, "Expert Knowledge"), (2, "High Knowledge"), (3, "Good Knowledge")), default=1, blank=False)
    
    def __str__(self):
        return self.assignee + " can mentor " + self.project + " with " + self.level

class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    academic = models.ForeignKey(Academic, on_delete=models.CASCADE)

    def __str__(self):
        return self.student + " assigned to " + self.project + " supervised by " + self.academic

