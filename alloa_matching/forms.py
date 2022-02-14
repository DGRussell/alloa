from django import forms
from alloa_matching.models import *

class UploadForm(forms.Form):
    name = forms.CharField(max_length=200, help_text="Course Name")
    level = forms.IntegerField(help_text="Course Level")
    students = forms.FileField(widget=forms.FileInput(attrs={'accept': ".csv"}), help_text="students.csv file field")
    projects = forms.FileField(widget=forms.FileInput(attrs={'accept': ".csv"}), help_text="projects.csv file field", required=False)
    academics = forms.FileField(widget=forms.FileInput(attrs={'accept': ".csv"}), help_text="academics.csv file field")
    
    class Meta:
        model=Instance
        fields = ('name','level',)

class ProposalForm(forms.Form):
    name = forms.CharField(max_length=200, help_text= "Project Name")
    description = forms.CharField(max_length=1000, help_text="Project Description")
    upper_cap = forms.IntegerField(help_text="Project Upper Capacity")
    lower_cap = forms.IntegerField(help_text="Project Lower Capacity")

    class Meta:
        model=Project
        fields=('name','description','upper_cap','lower_cap')
