from django.contrib import admin
from alloa_matching.models import *
# Register your models here.

class InstanceAdmin(admin.ModelAdmin):
    list_display = ('name','level','stage')
class StudentAdmin(admin.ModelAdmin):
    list_display = ('instance','user_profile','upper_cap','lower_cap')
class AdminSquared(admin.ModelAdmin):
    list_display = ('user_profile','super_admin')
class ManagerAdmin(admin.ModelAdmin):
    list_display = ('instance','admin')
class AcademicAdmin(admin.ModelAdmin):
    list_display = ('instance','user_profile','upper_cap','lower_cap')
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('instance','name','description','upper_cap','lower_cap')
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ('student','project','rank')
class ALevelAdmin(admin.ModelAdmin):
    list_display = ('academic','project','level')
class ResultAdmin(admin.ModelAdmin):
    list_display = ('student','academic','project')

admin.site.register(Instance, InstanceAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(Admin, AdminSquared)
admin.site.register(Manager, ManagerAdmin)
admin.site.register(Academic, AcademicAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Choice, ChoiceAdmin)
admin.site.register(AdvisorLevel, ALevelAdmin)
admin.site.register(Result, ResultAdmin)