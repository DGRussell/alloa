import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alloa.settings')

import django
django.setup()

from alloa_matching.models import *
from django.contrib.auth.models import User

def clean():
    Instance.objects.all().delete()
    Student.objects.all().delete()
    User.objects.all().delete()
    UserProfile.objects.all().delete()
    Admin.objects.all().delete()
    Result.objects.all().delete()
    Choice.objects.all().delete()
    Project.objects.all().delete()
    AdvisorLevel.objects.all().delete()
    Manager.objects.all().delete()
    Academic.objects.all().delete()
    create_super_user()

def create_super_user():

    user = User(
        username = "douglas",
        email = "douglas@super.user",
        first_name = "douglas",
        last_name = "russell",
    )
    user.set_password("pass")
    user.is_superuser = True
    user.is_staff = True
    user.save()

    return user

if __name__ == '__main__':
    print('\nCleaning')
    clean()
    print('\nFinished')