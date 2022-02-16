"""alloa URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.urls import path
from django.urls import include
from django.conf.urls.static import static
from alloa_matching import views
from django.contrib.staticfiles.urls import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('home/', views.home, name='home'),
    path('logout/', views.user_logout, name='logout'),
    path('instance/new/', views.upload, name='upload'),
    path('instance/<int:instance_id>/', views.instance, name='instance'),
    path('instance/<int:instance_id>/stage/<str:new_stage>/', views.set_stage, name='set_stage'),
    path('instance/<int:instance_id>/remove_level/<int:level_id>/', views.remove_level, name='remove_level'),
    path('instance/<int:instance_id>/match/', views.compute_matching, name='compute_matching')
]
