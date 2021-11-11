from django.shortcuts import render
from django import template
from django.contrib import messages
from django.template import Context
from django.template.loader import render_to_string, get_template
from django.conf import settings
from alloa_matching.models import *
from alloa_matching.forms import *
from typing import List, Optional

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

            # Create a new instance for uploaded files - need to add to form to name the instance and give the instance level
            instance = Instance.objects.get_or_create(name=form.cleaned_data.get("name"),level=form.cleaned_data.get("level"))[0]
            instance.save()

            # For each academic make them a user and an academic profile
            for i in range(len(academics)):
                user = User.objects.get_or_create(username=academics[i]["Supervisor"], first_name=academics[i]["Supervisor"],last_name=academics[i]["Supervisor"],email=academics[i]["Supervisor"]+"@test.com",password="TestPassword")[0]
                user.save()
                academic = Academic.objects.get_or_create(user=user,staff_id=(str(i)+"test"),instance=instance,upper_cap=int(academics[i]["Supervisor Upper Capacity"]),lower_cap=int(academics[i]["Supervisor Lower Capacity"]))[0]
                academic.save()

            # For each project create the project model and the Advisor Level for each of the choices 
            for i in range(len(projects)):
                project = Project.objects.get_or_create(instance=instance,name=projects[i]["Project"],upper_cap=int(projects[i]["Project Upper Capacity"]),lower_cap=int(projects[i]["Project Lower Capacity"]),description="Test add")[0]
                if projects[i]["Choice 1"] != '':
                    user = User.objects.get(username=projects[i]["Choice 1"])
                    academic = Academic.objects.get(user=user)
                    alevel = AdvisorLevel.objects.get_or_create(project=project, academic=academic, level=1)[0]
                    alevel.save()
                if projects[i]["Choice 2"] != '':
                    user = User.objects.get(username=projects[i]["Choice 2"])
                    academic = Academic.objects.get(user=user)
                    alevel = AdvisorLevel.objects.get_or_create(project=project, academic=academic, level=2)[0]
                    alevel.save()
                if projects[i]["Choice 3"] != '':
                    user = User.objects.get(username=projects[i]["Choice 3"])
                    academic = Academic.objects.get(user=user)
                    alevel = AdvisorLevel.objects.get_or_create(project=project, academic=academic, level=3)[0]
                    alevel.save()
            # For each student create a user and student object, then create their project ranking objects
            for i in range(len(students)):
                full_name = students[i]["Student Name"]
                split_name = full_name.split(" ")
                if len(split_name) > 2:
                    first_name = split_name.pop(0)
                    last_name = ' '.join(split_name)
                else:
                    first_name = split_name[0]
                    last_name = split_name[1]
                user = User.objects.get_or_create(username=str(i)+first_name,first_name=first_name,last_name=last_name,email=first_name+"@test.com",password="TestPass1")[0]
                user.save()
                student = Student.objects.get_or_create(user=user,matric_number=str(i),instance=instance,upper_cap=students[i]["Student Upper Capacity"],lower_cap=students[i]["Student Lower Capacity"])[0]
                student.save()
                for j in range(7):
                    project = Project.objects.get(name=students[i]["Choice "+str(j+1)])
                    choice = Choice.objects.get_or_create(student=student,project=project,rank=j+1)[0]
                    choice.save()
            
            context_dict["uploaded"] = "Upload Successful - check the admin portal"
    else:
        form=UploadForm()
    context_dict['form'] = form
    return render(request, 'alloa_matching/upload.html',context=context_dict)

def compute_matching(request):
    context_dict = {}
    data_objects = []
    quoting = 3

    # Project retrieval
    level = 2
    projects = Project.objects.filter(instance=4)
    file_data = File(randomise=False,level=level,quoting=quoting)
    for project in projects:
        advisor_levels = AdvisorLevel.objects.filter(project=project)
        line = [project.name,str(project.lower_cap),str(project.upper_cap)]
        for level in advisor_levels:
            line.append(level.academic.user.first_name)
        file_data.file_content.append(Line(line))
    data_objects.append(file_data)

    # Academic retrieval
    level = 3
    academics = Academic.objects.filter(instance=4)
    file_data = File(randomise=False,level=level,quoting=quoting)
    for academic in academics:
        line = [academic.user.first_name,str(academic.lower_cap),str(academic.upper_cap)]
        file_data.file_content.append(Line(line))
    data_objects.append(file_data)

    # Student retrieval
    level = 1
    students = Student.objects.filter(instance=4)
    file_data = File(randomise=False,level=level,quoting=quoting)
    for student in students:
        line = [student.user.get_full_name(),str(student.lower_cap),str(student.upper_cap)]
        choices = Choice.objects.filter(student=student)
        for choice in choices:
            line.append(choice.project.name)
        file_data.file_content.append(Line(line))
    data_objects.append(file_data)

    print(data_objects)
    context_dict["data_objects"] = data_objects
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
        if len(data) > 1:
            for i in range(len(data)):
                individual[headings[i].replace("\r","")] = data[i].replace("\r","")
            group.append(individual) 
    return group

class Line:
    """Represents a line of data read from input CSV file."""
    def __init__(self, line: List[str]) -> None:
        self.line = [x.strip() for x in line]
        self.raw_name = line[0]
        self.capacities = [int(x) for x in self.line[1:3]]
        self.raw_preferences = self.line[3:]

    def __eq__(self, other) -> bool:
        return self.line == other.line

    def __repr__(self) -> str:
        return "line" + str(self.raw_name)

class File:
    """Contains data parsed from input CSV file."""
    def __init__(
        self,
        delimiter: str = ',',
        level: Optional[int] = None,
        randomise: bool = False,
        quoting: int = 3,
    ) -> None:
        self.randomise = randomise
        self.delimiter = delimiter
        self.quoting = quoting
        self.level = level

        self.file_content = []
        
        def __repr__(self):
            return 'LEVEL_' + str(self.level) + '_DATA'