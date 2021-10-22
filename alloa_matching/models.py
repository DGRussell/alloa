from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Instance(models.Model):
    name = models.CharField(max_length=200, unique=True, required=True)
    level = models.IntegerField(default=0, required=True)

    def __str__(self):
        return self.name

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    matric_number = models.CharField(max_length=8, unique=True, required=True)

    def __str__(self):
        return self.matric_number

class Admin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    super_admin = models.BooleanField(blank=False, default=False, required=True)

    def __str__(self):
        return self.user.get_full_name()

class Manager(models.Model):
    admin = models.ForeignKey(Admin, on_delete=models.CASCADE)
    instance = models.ForeignKey(Instance, on_delete=models.CASCADE)

    def __str__(self):
        return self.admin + " managing " + self.instance

class Academic(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    staff_id = models.CharField(max_length=6, unique=True, required=True)

    def __str__(self):
        return self.user.get_full_name()

class Project(models.Model):
    name = models.CharField(max_length=200, required=True)
    description = models.CharField(max_length=1000, required=True)
    upper_cap = models.IntegerField(default=1, required=True)
    lower_cap = models.IntegerField(default=0, required=True)
    instance = models.ForeignKey(Instance, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Enrollee(models.Model):
    instance = models.ForeignKey(Instance, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    upper_cap = models.IntegerField(default=1, required=True)
    lower_cap = models.IntegerField(default=0, required=True)

    def __str__(self):
        return self.student + " taking " + self.instance

class Choice(models.Model):
    enrollee = models.ForeignKey(Enrollee, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    rank = models.IntegerField(default=1, required=True)

    def __str__(self):
        return self.enrolee.student + " ranks " + self.project + " rank " + self.rank

class Assignee(models.Model):
    academic = models.ForeignKey(Academic, on_delete=models.CASCADE)
    instance = models.ForeignKey(Instance, on_delete=models.CASCADE)
    upper_cap = models.IntegerField(default=1, required=True)
    lower_cap = models.IntegerField(default=0, required=True)

    def __str__(self):
        return self.academic + " assigned to " + self.instance

class Supervisor(models.Model):
    assignee = models.ForeignKey(Assignee, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    level = models.IntegerField(choices=((1, "Expert Knowledge"), (2, "High Knowledge"), (3, "Good Knowledge")), default=1, required=True)
    
    def __str__(self):
        return self.assignee + " can mentor " + self.project + " with " + self.level

class Result(models.Model):
    enrollee = models.ForeignKey(Enrollee, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    academic = models.ForeignKey(Academic, on_delete=models.CASCADE)

    def __str__(self):
        return self.student + " assigned to " + self.project + " supervised by " + self.academic

