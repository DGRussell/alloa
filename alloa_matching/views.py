from django.shortcuts import render
from django import template
from django.contrib import messages
from django.template import Context
from django.template.loader import render_to_string, get_template
from django.conf import settings
from alloa_matching.models import *
from alloa_matching.forms import *
from typing import List, Optional
from alloa_matching.costs import spa_cost
from alloa_matching.graph_builder import GraphBuilder
from alloa_matching.files import Line, FileReader

# Create your views here.
def index(request):
    return render(request, 'alloa_matching/index.html')

def home(request):
    context_dict = {} 
    context_dict["instances"] = Instance.objects.all()
    return render(request, 'alloa_matching/home.html',context=context_dict)

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
            instance = Instance.objects.get_or_create(name=form.cleaned_data.get("name"),level=form.cleaned_data.get("level"),stage="C")[0]
            instance.save()

            # For each academic make them a user and an academic profile
            for i in range(len(academics)):
                user = User.objects.get_or_create(username=academics[i]["Staff ID"], first_name=academics[i]["Supervisor Firstname"],last_name=academics[i]["Supervisor Surname"],email=academics[i]["Staff ID"]+"@glasgow.ac.uk",password="TestPassword")[0]
                user.save()
                user_profile = UserProfile.objects.get_or_create(user=user,user_type="Academic",unique_id=academics[i]["Staff ID"])[0]
                user_profile.save()
                academic = Academic.objects.get_or_create(user_profile=user_profile,instance=instance,upper_cap=int(academics[i]["Supervisor Upper Capacity"]),lower_cap=int(academics[i]["Supervisor Lower Capacity"]))[0]
                academic.save()

            # For each project create the project model and the Advisor Level for each of the choices 
            for i in range(len(projects)):
                project = Project.objects.get_or_create(instance=instance,name=projects[i]["Project"],upper_cap=int(projects[i]["Project Upper Capacity"]),lower_cap=int(projects[i]["Project Lower Capacity"]),description="Test add")[0]
                print(projects[i])
                if projects[i]["Choice 1"] != '':
                    user = User.objects.get(username=projects[i]["Choice 1"])
                    user_profile = UserProfile.objects.get(user=user)
                    academic = Academic.objects.get(user_profile=user_profile)
                    alevel = AdvisorLevel.objects.get_or_create(project=project, academic=academic, level=1)[0]
                    alevel.save()
                if projects[i]["Choice 2"] != '':
                    user = User.objects.get(username=projects[i]["Choice 2"])
                    user_profile = UserProfile.objects.get(user=user)
                    academic = Academic.objects.get(user_profile=user_profile)
                    alevel = AdvisorLevel.objects.get_or_create(project=project, academic=academic, level=2)[0]
                    alevel.save()
                if projects[i]["Choice 3"] != '':
                    user = User.objects.get(username=projects[i]["Choice 3"])
                    user_profile = UserProfile.objects.get(user=user)
                    academic = Academic.objects.get(user_profile=user_profile)
                    alevel = AdvisorLevel.objects.get_or_create(project=project, academic=academic, level=3)[0]
                    alevel.save()
            # For each student create a user and student object, then create their project ranking objects
            for i in range(len(students)):
                # full_name = students[i]["Student Name"]
                # split_name = full_name.split(" ")
                # if len(split_name) > 2:
                #     first_name = split_name.pop(0)
                #     last_name = ' '.join(split_name)
                # else:
                #     first_name = split_name[0]
                #     last_name = split_name[1]
                first_name = students[i]["Student Firstname"]
                last_name = students[i]["Student Surname"]
                matric = students[i]["Matric Number"]
                user = User.objects.get_or_create(username=matric,first_name=first_name,last_name=last_name,email=matric+"@student.gla.ac.uk",password="TestPass1")[0]
                user.save()
                user_profile = UserProfile.objects.get_or_create(user=user,user_type="Student",unique_id=matric)[0]
                user_profile.save()
                student = Student.objects.get_or_create(user_profile=user_profile,instance=instance,upper_cap=students[i]["Student Upper Capacity"],lower_cap=students[i]["Student Lower Capacity"])[0]
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

def compute_matching(request, instance_id):

    context_dict = {}
    instance = Instance.objects.get(id=instance_id)
    print(instance.stage)
    if instance.stage == "C":
        data_objects = []
        quoting = 3

        # Student retrieval
        level = 1
        students = Student.objects.filter(instance=instance_id)
        file_data = FileReader(randomise=False,level=level,quoting=quoting)
        for student in students:
            line = [student.user_profile.unique_id,str(student.lower_cap),str(student.upper_cap)]
            choices = Choice.objects.filter(student=student)
            for choice in choices:
                line.append(choice.project.name)
            file_data.file_content.append(Line(line))
        data_objects.append(file_data)

        # Project retrieval
        level = 2
        projects = Project.objects.filter(instance=instance_id)
        file_data = FileReader(randomise=False,level=level,quoting=quoting)
        for project in projects:
            advisor_levels = AdvisorLevel.objects.filter(project=project)
            line = [project.name,str(project.lower_cap),str(project.upper_cap)]
            for level in advisor_levels:
                line.append(level.academic.user_profile.unique_id)
            file_data.file_content.append(Line(line))
        data_objects.append(file_data)

        # Academic retrieval
        level = 3
        academics = Academic.objects.filter(instance=instance_id)
        file_data = FileReader(randomise=False,level=level,quoting=quoting)
        for academic in academics:
            line = [academic.user_profile.unique_id,str(academic.lower_cap),str(academic.upper_cap)]
            file_data.file_content.append(Line(line))
        data_objects.append(file_data)

        graph_builder = GraphBuilder(data_objects, spa_cost)
        graph = graph_builder.build_graph()

        graph.populate_all_edges()
        graph.compute_flow()
        graph.simplify_flow()
        graph.allocate()

        first_level_agent_names = [x.raw_name for x in data_objects[0].file_content]

        allocation = parse_graph(graph,first_level_agent_names)

        results = []
        for assignment in allocation[1:]:
            student_user_profile = UserProfile.objects.get(unique_id=assignment[0])
            student = Student.objects.get(user_profile=student_user_profile)

            if assignment[1] != None:
                project = Project.objects.get(name=assignment[1])

                academic_user_profile = UserProfile.objects.get(unique_id=assignment[2])
                academic = Academic.objects.get(user_profile=academic_user_profile)

                result = Result(student=student,project=project,academic=academic)
                result.save()
                results.append(result)
            else:
                unmatched.append(student)

        instance.stage="R"
        instance.save()
    
    else:
        students = Student.objects.filter(instance=instance)
        results = []
        unmatched = []
        for student in students:
            if Result.objects.filter(student=student).exists():
                result = Result.objects.get(student=student)
                results.append(result)
            else:
                unmatched.append(student)

    context_dict["instance"] = instance
    context_dict["results"] = results
    context_dict["unmatched"] = unmatched
    return render(request, 'alloa_matching/compute_matching.html',context=context_dict)

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

def parse_graph(graph,first_level_agent_names):

        if not graph.first_level_agents:
            return

        allocation = graph.allocation

        first_agent = graph.first_level_agents[0]
        num_of_agents = len(allocation[first_agent]) // 2 + 1
        name_columns, rank_columns = [], []
        for i in range(num_of_agents):
            name_columns.append(f'Level {i + 1} Agent Name')
            rank_columns.append(f'Level {i + 1} Agent Rank')
        column_names = ['Level 1 Agent Name'] + name_columns + rank_columns

        number_of_columns = len(column_names)

        rows = []

        for agent in graph.first_level_agents:
            row = [agent.name]
            row.extend(
                datum.agent.name for datum in allocation[agent]
            )
            row.extend(
                datum.rank for datum in allocation[agent]
            )

            # Extend row to correct length in case agent is not allocated.
            row.extend(None for _ in range(number_of_columns - len(row)))

            rows.append(row)

        # Sort so the output CSV file has the same order as the input CSV file
        # for first level agents.
        def _key(_row):
            return first_level_agent_names.index(_row[0])

        rows = sorted(rows, key=_key)
        output_rows = [column_names] + rows
        return output_rows 