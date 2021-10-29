from django import forms
from alloa_matching.models import *

class UploadForm(forms.Form):
    name = forms.CharField(max_length=200, help_text="Course Name")
    level = forms.IntegerField(help_text="Course Level")
    students = forms.FileField(widget=forms.FileInput(attrs={'accept': ".csv"}), help_text="students.csv file field")
    projects = forms.FileField(widget=forms.FileInput(attrs={'accept': ".csv"}), help_text="projects.csv file field")
    academics = forms.FileField(widget=forms.FileInput(attrs={'accept': ".csv"}), help_text="academics.csv file field")
    
    class Meta:
        model=Instance
        fields = ('name','level',)