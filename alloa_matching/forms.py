from django import forms
from alloa_matching.models import *

class UploadForm(forms.Form):
    name = forms.CharField(max_length=200, help_text="Course Name")
    min_pref_len = forms.IntegerField(help_text="Minimum Length of Student Preference List")
    max_pref_len = forms.IntegerField(help_text="Maximum Length of Student Preference List")
    students = forms.FileField(widget=forms.FileInput(attrs={'accept': ".csv"}), help_text="students.csv file field")
    projects = forms.FileField(widget=forms.FileInput(attrs={'accept': ".csv"}), help_text="projects.csv file field", required=False)
    academics = forms.FileField(widget=forms.FileInput(attrs={'accept': ".csv"}), help_text="academics.csv file field")
    
    class Meta:
        model=Instance
        fields = ('name','min_pref_len','max_pref_len')

class ProposalForm(forms.Form):
    name = forms.CharField(max_length=200, help_text= "Project Name")
    description = forms.CharField(max_length=1000, help_text="Project Description")
    upper_cap = forms.IntegerField(help_text="Project Upper Capacity")
    lower_cap = forms.IntegerField(help_text="Project Lower Capacity")

    class Meta:
        model=Project
        fields=('name','description','upper_cap','lower_cap')

class AdvisorLevelForm(forms.Form):
    name = forms.CharField(max_length=200, help_text= "Project Name")
    level = forms.ChoiceField(choices=((1, "Expert Knowledge"), (2, "High Knowledge"), (3, "Good Knowledge")),required=True)

    class Meta:
        model=AdvisorLevel
        fields=('level')
