from django import forms

class UploadForm(forms.Form):
    students = forms.FileField(widget=forms.FileInput(attrs={'accept': ".csv"}), help_text="students.csv file field")
    projects = forms.FileField(widget=forms.FileInput(attrs={'accept': ".csv"}), help_text="projects.csv file field")
    academics = forms.FileField(widget=forms.FileInput(attrs={'accept': ".csv"}), help_text="academics.csv file field")