from django.shortcuts import render, redirect, reverse
from django import template
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.template import Context
from django.template.loader import render_to_string, get_template
from django.conf import settings
from alloa_matching.models import *
from alloa_matching.forms import *
from typing import List, Optional
from alloa_matching.costs import spa_cost
from alloa_matching.graph_builder import GraphBuilder
from alloa_matching.files import Line, FileReader
import copy

# Create your views here.

def index(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)

        if user:
            if user.is_active:
                login(request, user)
                if user.is_superuser:
                    request.session["user_type"] = "SA"
                else:
                    user_profile = UserProfile.objects.get(user=user)
                    request.session["user_type"] = user_profile.user_type
                return redirect(reverse('home'))
        else:
            messages.error(request,'Username or Password Incorrect')
    return render(request, 'alloa_matching/index.html')

@login_required
def user_logout(request):
    """Function to handle User logout"""
    del request.session["user_type"]
    logout(request)
    return redirect(reverse('index'))

@login_required
def home(request):
    context_dict = {} 
    context_dict["instances"] = Instance.objects.all()
    context_dict["user"] = request.user
    context_dict["user_type"] = request.session["user_type"]
    return render(request, 'alloa_matching/home.html',context=context_dict)

@login_required
def upload(request):
    context_dict = {}
    # If files have been uploaded and are valid
    if request.method == 'POST':
        form=UploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Create 2 list of dictionaries using file_read function for students and academics and get their file headers
            students,student_headings = file_read(request.FILES["students"])
            academics,academic_headings = file_read(request.FILES["academics"])

            if request.FILES.get("projects",False):
                # if a projects file has been uploaded, create its dictionary and headings file and calculate the instance type
                projects,project_headings = file_read(request.FILES["projects"])
                instance_type = get_instance_type(student_headings,project_headings)
            else:
                # otherwise instance type can only be a projectless instance
                instance_type="no_projects"

            # Create a new instance for uploaded files
            instance = Instance.objects.get_or_create(name=form.cleaned_data.get("name"),level=form.cleaned_data.get("level"),stage="N")[0]
            instance.save()

            # For each academic make them a user and an academic profile
            for i in range(len(academics)):
                user = User.objects.get_or_create(username=academics[i]["Staff ID"], first_name=academics[i]["Supervisor Firstname"],last_name=academics[i]["Supervisor Surname"],email=academics[i]["Staff ID"]+"@glasgow.ac.uk")[0]
                user.set_password("TestPass1")
                user.save()
                user_profile = UserProfile.objects.get_or_create(user=user,user_type="AC",unique_id=academics[i]["Staff ID"])[0]
                user_profile.save()
                academic = Academic.objects.get_or_create(user_profile=user_profile,instance=instance,upper_cap=int(academics[i]["Supervisor Upper Capacity"]),lower_cap=int(academics[i]["Supervisor Lower Capacity"]))[0]
                academic.save()

            # if projects uploaded - For each project create the project model
            if instance_type != "no_projects":
                for i in range(len(projects)):
                    project = Project.objects.get_or_create(instance=instance,name=projects[i]["Project"],upper_cap=int(projects[i]["Project Upper Capacity"]),lower_cap=int(projects[i]["Project Lower Capacity"]),description="Test add")[0]
                    # If advisor preferences have been uploaded, save them
                    if instance_type == "all_rankings" or instance_type == "no_student_rankings": 
                        if projects[i]["Choice 1"] != '':
                            user = User.objects.get(username=projects[i]["Choice 1"])
                            user_profile = UserProfile.objects.get(user=user)
                            academic = Academic.objects.get(user_profile=user_profile,instance=instance)
                            alevel = AdvisorLevel.objects.get_or_create(project=project, academic=academic, level=1)[0]
                            alevel.save()
                        if projects[i]["Choice 2"] != '':
                            user = User.objects.get(username=projects[i]["Choice 2"])
                            user_profile = UserProfile.objects.get(user=user)
                            academic = Academic.objects.get(user_profile=user_profile,instance=instance)
                            alevel = AdvisorLevel.objects.get_or_create(project=project, academic=academic, level=2)[0]
                            alevel.save()
                        if projects[i]["Choice 3"] != '':
                            user = User.objects.get(username=projects[i]["Choice 3"])
                            user_profile = UserProfile.objects.get(user=user)
                            academic = Academic.objects.get(user_profile=user_profile,instance=instance)
                            alevel = AdvisorLevel.objects.get_or_create(project=project, academic=academic, level=3)[0]
                            alevel.save()
            
            # For each student create a user and student object
            for i in range(len(students)):
                first_name = students[i]["Student Firstname"]
                last_name = students[i]["Student Surname"]
                matric = students[i]["Matric Number"]
                user = User.objects.get_or_create(username=matric,first_name=first_name,last_name=last_name,email=matric+"@student.gla.ac.uk")[0]
                user.set_password("TestPass1")
                user.save()
                user_profile = UserProfile.objects.get_or_create(user=user,user_type="ST",unique_id=matric)[0]
                user_profile.save()
                student = Student.objects.get_or_create(user_profile=user_profile,instance=instance,upper_cap=students[i]["Student Upper Capacity"],lower_cap=students[i]["Student Lower Capacity"])[0]
                student.save()
                # If student ranks have been uploaded then save them
                if instance_type == "all_rankings" or instance_type == "no_academic_rankings":
                    for j in range(7):
                        project = Project.objects.get(name=students[i]["Choice "+str(j+1)],instance=instance)
                        choice = Choice.objects.get_or_create(student=student,project=project,rank=j+1)[0]
                        choice.save()
            # Redirect to individual page for new instance
            return redirect(reverse('instance', kwargs={"instance_id": instance.id}))
    else:
        form = UploadForm()
    context_dict['form'] = form
    return render(request, 'alloa_matching/upload.html',context=context_dict)

@login_required
def compute_matching(request, instance_id):

    instance = Instance.objects.get(id=instance_id)
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

    # Build alloa graph
    graph_builder = GraphBuilder(data_objects, spa_cost)
    graph = graph_builder.build_graph()

    # Run alloa algorithm
    graph.populate_all_edges()
    graph.compute_flow()
    graph.simplify_flow()
    graph.allocate()

    first_level_agent_names = [x.raw_name for x in data_objects[0].file_content]
    # Get allocation
    allocation = parse_graph(graph,first_level_agent_names)

    # For each allocation
    for assignment in allocation[1:]:
        # Get assigned student
        student_user_profile = UserProfile.objects.get(unique_id=assignment[0])
        student = Student.objects.get(user_profile=student_user_profile,instance=instance)

        # If student is matched
        if assignment[1] != None:

            # Get project and academic
            project = Project.objects.get(name=assignment[1],instance=instance)
            academic_user_profile = UserProfile.objects.get(unique_id=assignment[2])
            academic = Academic.objects.get(user_profile=academic_user_profile,instance=instance)

            # Create and save result 
            result = Result(student=student,project=project,academic=academic)
            result.save()
    
    # Change stage of instance to results available
    instance.stage="R"
    instance.save()
    
    # Redirect to instance view
    return redirect(reverse('instance', kwargs={"instance_id": instance.id}))

@login_required
def instance(request, instance_id):

    context_dict = {}
    instance = Instance.objects.get(id=instance_id)
    context_dict["instance"] = instance

    # If instance is awaiting student preferences
    if instance.stage == "N":
        if request.session["user_type"] == "AD" or request.session["user_type"] == "SA":
            return render(request, 'alloa_matching/new_instance.html',context=context_dict)
        else:
            messages.error(request,"This instance is not currently available to you.")
            return redirect(reverse('home'))
    if instance.stage == "S":
        # TBC
        if request.session["user_type"] == "ST":
            print("Student")
            return render(request, 'alloa_matching/student_preference.html',context=context_dict)
        # If user is academic
        if request.session["user_type"] == "AC":
            # Get their profile
            academic_user_profile = UserProfile.objects.get(user=request.user)
            academic = Academic.objects.get(user_profile=academic_user_profile,instance=instance_id)

            # If they have ranked any projects
            if AdvisorLevel.objects.filter(academic=academic).exists():
                # Get all their choices
                choices = AdvisorLevel.objects.filter(academic=academic)
                unranked = False
            else:
                # Otherwise mark them as unranked
                choices = []
                unranked = True
            
            # Load academic waiting for results page
            context_dict["choices"] = choices
            context_dict["unranked"] = unranked

            return render(request, 'alloa_matching/academic_student_preference.html',context=context_dict)
        # TBC
        if request.session["user_type"] == "AD" or request.session["user_type"] == "SA":
            print("Admin")
            return render(request, 'alloa_matching/admin_student_preference.html',context=context_dict)

    # If instance is closed
    if instance.stage == "C":
        # If user is a student
        if request.session["user_type"] == "ST":

            # Get their profile
            student_user_profile = UserProfile.objects.get(user=request.user)
            student = Student.objects.get(user_profile=student_user_profile,instance=instance_id)

            # If they have given ranks
            if Choice.objects.filter(student=student).exists():
                # Get all their rankings
                choices = Choice.objects.filter(student=student)
                unranked = False
            else:
                # Otherwise mark as unranked
                choices = []
                unranked = True
            
            # Load student waiting for results page
            context_dict["choices"] = choices
            context_dict["unranked"] = unranked

            return render(request, 'alloa_matching/student_closed.html',context=context_dict)

        # If user is academic
        if request.session["user_type"] == "AC":
            # Get their profile
            academic_user_profile = UserProfile.objects.get(user=request.user)
            academic = Academic.objects.get(user_profile=academic_user_profile,instance=instance_id)

            # If they have ranked any projects
            if AdvisorLevel.objects.filter(academic=academic).exists():
                # Get all their choices
                choices = AdvisorLevel.objects.filter(academic=academic)
                unranked = False
            else:
                # Otherwise mark them as unranked
                choices = []
                unranked = True
            
            # Load academic waiting for results page
            context_dict["choices"] = choices
            context_dict["unranked"] = unranked

            return render(request, 'alloa_matching/academic_closed.html',context=context_dict)

        # If user is an admin
        if request.session["user_type"] == "AD" or request.session["user_type"] == "SA":
            # Get all students assigned to the instance
            students = Student.objects.filter(instance=instance_id)
            results = []
            unranked = []
            
            # For each student
            for student in students:
                # If student has given ranks, get all their ranked projects
                if Choice.objects.filter(student=student).exists():
                    result = Choice.objects.filter(student=student)
                    results.append(result)
                # Otherwise add student to unranked list
                else:
                    results.append([])
                    unranked.append(student)

            # 
            projects = Project.objects.filter(instance=instance_id)
            levels = []

            for project in projects:
                if AdvisorLevel.objects.filter(project=project).exists():
                    result = AdvisorLevel.objects.filter(project=project)
                    levels.append(result)
                else:
                    levels.append([])
            # Load admin closed page
            context_dict["projects"] = levels
            context_dict["range"] = [*range(1,8,1)]
            context_dict["results"] = zip(students,results)
            context_dict["unranked"] = unranked
            return render(request, 'alloa_matching/admin_closed.html',context=context_dict)

    # If results are available
    if instance.stage == "R":
        # If user is student
        if request.session["user_type"] == "ST":
            
            # Get profile
            student_user_profile = UserProfile.objects.get(user=request.user)
            student = Student.objects.get(user_profile=student_user_profile,instance=instance_id)

            # If matched return all students matching
            if Result.objects.filter(student=student).exists():
                results = Result.objects.filter(student=student)
                unmatched = False
            # If unmatched return unmatched as true for view 
            else:
                results = []
                unmatched = True

            # Render student results page
            context_dict["results"] = results
            context_dict["unmatched"] = unmatched

            return render(request, 'alloa_matching/student_results.html',context=context_dict)
        
        # If user is academic
        if request.session["user_type"] == "AC":
            # Get user profile
            academic_user_profile = UserProfile.objects.get(user=request.user)
            academic = Academic.objects.get(user_profile=academic_user_profile,instance=instance_id)

            # If matched return all academic matching
            if Result.objects.filter(academic=academic).exists():
                results = Result.objects.filter(academic=academic)
                unmatched = False
            # If unmatched return unmatched as true for view 
            else:
                results = []
                unmatched = True

            # Render academic results page
            context_dict["results"] = results
            context_dict["unmatched"] = unmatched

            return render(request, 'alloa_matching/academic_results.html',context=context_dict)

        # If user is an admin
        if request.session["user_type"] == "AD" or request.session["user_type"] == "SA":
            # Get all students assigned to the instance
            students = Student.objects.filter(instance=instance_id)
            results = []
            unmatched = []
            
            # For each student
            for student in students:
                # If student is matched, get all their assigned projects
                if Result.objects.filter(student=student).exists():
                    result = Result.objects.filter(student=student)
                    results.append(result)
                # Otherwise add student to unmatched list
                else:
                    unmatched.append(student)

            # Load admin results page
            context_dict["results"] = results
            context_dict["unmatched"] = unmatched

            return render(request, 'alloa_matching/admin_results.html',context=context_dict)

###########################################
#                                         #
#           HELPER FUNCTIONS              #
#                                         #
###########################################

def get_instance_type(student_headings,project_headings):
    
    if len(student_headings) > 5:
        if len(project_headings) > 3:
            return "all_rankings"
        else:
            return "no_academic_rankings"
    elif len(project_headings) > 3:
        return "no_student_rankings"
    else:
        return "no_rankings"

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
    return group, headings

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