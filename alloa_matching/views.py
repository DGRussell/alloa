from django.shortcuts import render
from django import template
from django.contrib import messages
from django.template import Context
from django.template.loader import render_to_string, get_template
from django.conf import settings
from alloa_matching.models import *
from alloa_matching.forms import *

# Create your views here.
def index(request):
    return render(request, 'alloa_matching/index.html')

def upload(request):
    context_dict = {}
    # If files have been uploaded and are valid
    if request.method == 'POST':
        form=UploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Create 3 list of dictionaries using file_read function
            students = file_read(request.FILES["students"])
            projects = file_read(request.FILES["projects"])
            academics = file_read(request.FILES["academics"])
    else:
        form=UploadForm()
    context_dict['form'] = form
    return render(request, 'alloa_matching/upload.html',context=context_dict)

def file_read(csv_file):
    # Decode given file - split up lines and pop headings line
    data = csv_file.read().decode("utf-8")
    lines = data.split("\n")
    headings = lines.pop(0)
    headings = headings.split(",")
    # Save each line in a dictionary and return a list of dictionaries
    group = []
    for line in lines:
        individual = {}
        data = line.split(",")
        for i in range(len(data)):
            individual[headings[i]] = data[i]
        group.append(individual) 
    return group