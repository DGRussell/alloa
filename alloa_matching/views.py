from django.shortcuts import render, redirect, reverse
from django import template
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.template import Context
from django.template.loader import render_to_string, get_template
from django.conf import settings
from django.forms import formset_factory
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
    user = request.user
    context_dict["user"] = user
    context_dict["user_type"] = request.session["user_type"]
    if request.session["user_type"] == "ST":
        user_profile = UserProfile.objects.get(user=user)
        instances = []
        students = Student.objects.filter(user_profile=user_profile)
        for s in students:
            if s.instance.stage != "N" and s.instance.stage != "L" and s.instance.stage != "P":
                instances.append(s.instance)
    if request.session["user_type"] == "AC":
        user_profile = UserProfile.objects.get(user=user)
        instances = []
        academics = Academic.objects.filter(user_profile=user_profile)
        for a in academics:
            if a.instance.stage != "N":
                instances.append(a.instance)
    if request.session["user_type"] == "AD" or request.session["user_type"] == "SA":
        instances = Instance.objects.all()
    context_dict["instances"] = instances
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

            # List of values to set as default, and potential list of reasons why files are invalid
            defaults = []
            reasons = []
            # Prepare academic headings for validity check
            academic_headings[len(academic_headings)-1] = academic_headings[len(academic_headings)-1].replace("\r","")
            academics_valid = True

            # Staff ID, Supervisor Firstname and Supervisor Surname must be in headings, otherwise not valid file
            if "Staff ID" not in academic_headings:
                academics_valid = False
                reasons.append("No Staff ID column")
            if "Supervisor Firstname" not in academic_headings:
                academics_valid = False
                reasons.append("No academic firstname column")
            if "Supervisor Surname" not in academic_headings:
                academics_valid = False
                reasons.append("No academic surname column")

            # If no capacities given then assume 1 and 0
            if len(academic_headings) == 3:
                defaults.append("Supervisor Upper Capacity")
                defaults.append("Supervisor Lower Capacity")

            # If one capacity given, assume the other is 1 or 0 respectively
            if len(academic_headings) == 4:
                if "Supervisor Lower Capacity" in academic_headings:
                    defaults.append("Supervisor Upper Capacity")
                elif "Supervisor Upper Capacity" in academic_headings:
                    defaults.append("Supervisor Lower Capacity")
                else:
                    academics_valid = False
                    reasons.append("Invalid 4th column, should be either Supervisor Lower Capacity or Supervisor Upper Capacity")

            # If both are given check they are valid
            elif len(academic_headings) == 5:
                if "Supervisor Lower Capacity" not in academic_headings:
                    academics_valid = False
                if "Supervisor Upper Capacity" not in academic_headings:
                    academics_valid = False
            # If more than 5 headers or less than 3, then the file is invalid
            else:
                academics_valid = False
                reasons.append("Too many columns in academics file")

            # Prepare student headings for validity check
            student_headings[len(student_headings)-1] = student_headings[len(student_headings)-1].replace("\r","")
            students_valid = True

            # If matric no, firstname or surname are not provided then file is invalid
            if "Matric Number" not in student_headings:
                students_valid = False
                reasons.append("Matric Number column missing")
            if "Student Firstname" not in student_headings:
                students_valid = False
                reasons.append("Student firstname column missing")
            if "Student Surname" not in student_headings:
                students_valid = False
                reasons.append("Student surname column missing")

            # Check if capacities are provided, if they arent then assume they are 0 and 1 respectively, if they are then the minimum number of headings stays high
            students_min_length = 5
            if "Student Lower Capacity" not in student_headings:
                students_min_length -= 1
                defaults.append("Student Lower Capacity")
            if "Student Upper Capacity" not in student_headings:
                students_min_length -= 1
                defaults.append("Student Upper Capacity")


            if request.FILES.get("projects",False):
                # if a projects file has been uploaded, create its dictionary and headings file
                projects,project_headings = file_read(request.FILES["projects"])

                # Prepare project heading for validity checks
                project_headings[len(project_headings)-1] = project_headings[len(project_headings)-1].replace("\r","")
                projects_valid = True

                # If project name not in file then projects file isn't valid
                if "Project" not in project_headings:
                    projects_valid = False
                    reasons.append("Project name column missing")

                if "Description" not in project_headings:
                    projects_valid = False
                    reasons.append("Project description column missing")

                # Check if project capacities have been supplied, if not then reduce the minimum headings length and assume 0 or 1 respectively
                projects_min_length = 4
                if "Project Lower Capacity" not in project_headings:
                    projects_min_length -= 1
                    defaults.append("Project Lower Capacity")
                if "Project Upper Capacity" not in project_headings:
                    projects_min_length -= 1
                    defaults.append("Project Upper Capacity")

                # Calculate instance type
                instance_type = get_instance_type(student_headings, students_min_length, project_headings, projects_min_length)

                # If student ranks have been provided then check each one
                if instance_type == "all_rankings" or instance_type == "no_academic_rankings":
                    i = 0
                    # For each heading check it is the next expected one (always from 1 upwards)
                    for heading in student_headings[students_min_length:]:
                        i+=1
                        if heading != ("Choice " + str(i)):
                            students_valid = False
                            reasons.append("Choice " + str(i) + " column missing from student rankings")
                    # Get max number of provided ranks
                    num_student_ranks = i

                # If advisor ranks have been supplied then check they are in expected order (1 upwards)
                if instance_type == "all_rankings" or instance_type == "no_student_rankings":
                    i = 0
                    # Check each heading is as expected, if not file is invalid
                    for heading in project_headings[projects_min_length:]:
                        i+=1
                        if heading != ("Choice " + str(i)):
                            projects_valid = False
                            reasons.append("Choice " + str(i) + " column missing from project rankings")
                    # Get max number of advisor ranks per project
                    num_advisor_ranks = i
            else:
                # otherwise instance type can only be a projectless instance, therefore check no ranking information has been provided in studennts file
                if len(student_headings) > students_min_length:
                    students_valid = False
                    reasons.append("Too many columns in student file")
                instance_type="no_projects"
                projects_valid=True
                valid_advisor_levels=True

            if students_valid and projects_valid and academics_valid:
                # Create a new instance for uploaded files
                instance = Instance.objects.get_or_create(name=form.cleaned_data.get("name"),min_pref_len=form.cleaned_data.get("min_pref_len"),max_pref_len=form.cleaned_data.get("max_pref_len"),stage="N")[0]
                instance.save()

                # For each academic
                for i in range(len(academics)):
                    # If user already exists then fetch
                    if User.objects.filter(username = academics[i]["Staff ID"]).exists():
                        user = User.objects.get(username = academics[i]["Staff ID"])
                        user_profile = UserProfile.objects.get(user=user)

                    # If not then create a new user and corresponding profile
                    else:
                        user = User(username=academics[i]["Staff ID"], first_name=academics[i]["Supervisor Firstname"],last_name=academics[i]["Supervisor Surname"],email=academics[i]["Staff ID"])
                        user.save()
                        user.set_password("TestPass1")
                        user.save()
                        user_profile = UserProfile(user=user,user_type="AC",unique_id=academics[i]["Staff ID"])
                        user_profile.save()

                    # Either set capacities to default values or provided values
                    if "Supervisor Lower Capacity" in defaults:
                        sup_l_cap = 0
                    else:
                        sup_l_cap = int(academics[i]["Supervisor Lower Capacity"])
                    if "Supervisor Upper Capacity" in defaults:
                        sup_u_cap = 1
                    else:
                        sup_u_cap = int(academics[i]["Supervisor Upper Capacity"])

                    # Create new academic object for the instance and save
                    academic = Academic(user_profile=user_profile,instance=instance,upper_cap=sup_u_cap,lower_cap=sup_l_cap)
                    academic.save()

                # if projects uploaded - For each project create the project model
                if instance_type != "no_projects":
                    for i in range(len(projects)):
                        # Either set capacities to default values or provided values
                        if "Project Lower Capacity" in defaults:
                            pro_l_cap = 0
                        else:
                            pro_l_cap = int(projects[i]["Project Lower Capacity"])
                        if "Project Upper Capacity" in defaults:
                            pro_u_cap = 1
                        else:
                            pro_u_cap = int(projects[i]["Project Upper Capacity"])
                        project = Project(instance=instance,name=projects[i]["Project"],upper_cap=pro_u_cap,lower_cap=pro_l_cap,description=projects[i]["Description"])
                        project.save()
                        # If advisor preferences have been uploaded, save them
                        valid_advisor_levels = True
                        if instance_type == "all_rankings" or instance_type == "no_student_rankings":
                            for j in range(num_advisor_ranks):
                                choice = "Choice " + str(j+1)
                                if projects[i][choice] != '':
                                    if UserProfile.objects.filter(unique_id=projects[i][choice]).exists():
                                        user_profile = UserProfile.objects.get(unique_id=projects[i][choice])
                                        if Academic.objects.filter(user_profile=user_profile,instance=instance).exists():
                                            academic = Academic.objects.get(user_profile=user_profile,instance=instance)
                                            alevel = AdvisorLevel(project=project, academic=academic, level=j+1)
                                            alevel.save()
                                        else:
                                            valid_advisor_levels = False
                                            reasons.append("Project " + project.name + " advisor choice " + str(j) + " is not an academic assigned to this instance.")
                                    else:
                                        valid_advisor_levels = False
                                        reasons.append("Project " + project.name + "'s advisor choice " + str(i) + " is not a registered academic.")
                # For each student create a user and student object
                for i in range(len(students)):
                    first_name = students[i]["Student Firstname"]
                    last_name = students[i]["Student Surname"]
                    matric = students[i]["Matric Number"]
                    if User.objects.filter(username = matric).exists():
                        user = User.objects.get(username = matric)
                        user_profile = UserProfile.objects.get(user=user)

                    # If not then create a new user and corresponding profile
                    else:
                        user = User(username=matric,first_name=first_name,last_name=last_name,email=matric+"@student.gla.ac.uk")
                        user.save()
                        user.set_password("TestPass1")
                        user.save()
                        user_profile = UserProfile(user=user,user_type="ST",unique_id=matric)
                        user_profile.save()

                    # Either set capacities to default values or provided values
                    if "Student Lower Capacity" in defaults:
                        stu_l_cap = 0
                    else:
                        stu_l_cap = students[i]["Student Lower Capacity"]
                    if "Student Upper Capacity" in defaults:
                        stu_u_cap = 1
                    else:
                        stu_u_cap = students[i]["Student Upper Capacity"]

                    student = Student(user_profile=user_profile,instance=instance,upper_cap=stu_u_cap,lower_cap=stu_l_cap)
                    student.save()
                    # If student ranks have been uploaded then save them
                    valid_student_choices = True
                    if instance_type == "all_rankings" or instance_type == "no_academic_rankings":
                        for j in range(num_student_ranks):
                            choice = "Choice " + str(j+1)
                            if students[i][choice] != '':
                                if Project.objects.filter(name=students[i]["Choice "+str(j+1)],instance=instance).exists():
                                    project = Project.objects.get(name=students[i]["Choice "+str(j+1)],instance=instance)
                                    choice = Choice.objects.get_or_create(student=student,project=project,rank=j+1)[0]
                                    choice.save()
                                else:
                                    valid_student_choices = False
                                    reasons.append("Student " + student.user_profile.unique_id + "'s project choice " + str(j+1) + " is not a registered project.")
                # Redirect to individual page for new instance
                if valid_student_choices and valid_advisor_levels:
                    return redirect(reverse('instance', kwargs={"instance_id": instance.id}))
                else:
                    for reason in reasons:
                        messages.error(request, reason)
                        instance.delete()
            else:
                for reason in reasons:
                    messages.error(request, reason)

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

    # Get the instance
    context_dict = {}
    instance = Instance.objects.get(id=instance_id)
    context_dict["instance"] = instance

    # If instance is new
    if instance.stage == "N":
        if request.session["user_type"] == "AD" or request.session["user_type"] == "SA":

            # Get students, projects and academics assigned to this instance
            context_dict["students"] = Student.objects.filter(instance=instance)
            context_dict["academics"] = Academic.objects.filter(instance=instance)
            context_dict["projects"] = Project.objects.filter(instance=instance)
            ranks = {}
            levels = {}

            # Get all student rankings, keeping track of the maximum number of rankings provided and whether students have enough rankings
            max_ranks = 0
            all_ranks = True
            for student in context_dict["students"]:
                rank = Choice.objects.filter(student=student)
                if len(rank) > max_ranks:
                    max_ranks = len(rank)
                if len(rank) < instance.min_pref_len:
                    all_ranks = False
                ranks[student.user_profile.unique_id] = []
                for r in rank:
                    ranks[student.user_profile.unique_id].append(r.project.name)

            # If any rankings are found get the max and pad any list under the maximum to this length
            if max_ranks != 0:
                context_dict["student_ranks"] = True
                context_dict["max_ranks"] = max_ranks
                for rank in ranks.values():
                    for i in range(max_ranks-len(rank)):
                        rank.append("No Ranking")
            # Otherwise set boolean so template knows which table to load
            else:
                context_dict["student_ranks"] = False

            # Get all advisor levels keeping track of the maximum number of levels per project
            max_levels = 0
            all_levels = True
            for project in context_dict["projects"]:
                level = AdvisorLevel.objects.filter(project=project)
                if len(level) > max_levels:
                    max_levels = len(level)
                if len(level) == 0:
                    all_levels = False
                levels[project.name] = []
                for l in level:
                    levels[project.name].append(l)

            # If any levels are found get the maximum number and pad any list under the maximum to this length
            if max_levels != 0:
                context_dict["advisor_levels"] = True
                context_dict["max_levels"] = max_levels
                for level in levels.values():
                    for i in range(max_levels-len(level)):
                        level.append("No Ranking")
            # Otherwise set boolean so template knows which table to load
            else:
                context_dict["advisor_levels"] = False

            context_dict["range"] = list(range(1,max_ranks+1))
            context_dict["advisor_range"] = list(range(1,max_levels+1))
            context_dict["ranks"] = ranks
            context_dict["levels"] = levels
            context_dict["all_levels"] = all_levels
            context_dict["all_ranks"] = all_ranks

            return render(request, 'alloa_matching/new_instance.html',context=context_dict)
        # If user is a student or academic redirect them to home page
        else:
            messages.error(request,"This instance is not currently available to you.")
            return redirect(reverse('home'))

    # If instance is in project proposal stage
    if instance.stage == "P":
        # If user is an admin
        if request.session["user_type"] == "AD" or request.session["user_type"] == "SA":
            # Get all projects currently added and output them so admin can judge how many have been proposed
            projects = Project.objects.filter(instance=instance)
            advisor_levels = []
            no_levels = []
            count = 0
            all_levels = True
            # For each project get their advisor levels
            for project in projects:
                levels = AdvisorLevel.objects.filter(project=project)
                # Add all levels to the level list
                advisor_levels.append(levels)
                count += len(levels)
                # If a project doesn't have any advisor levels set, store in unranked list and set boolean to false so admin cannot move stage
                if len(levels) == 0:
                    all_levels = False
                    no_levels.append(project)

            # Get all student rankings, check whether students have enough rankings to move straight to closed stage
            students = Student.objects.filter(instance=instance)
            all_ranks = True
            for student in students:
                if len(Choice.objects.filter(student=student))<instance.min_pref_len or len(Choice.objects.filter(student=student))>instance.max_pref_len:
                    all_ranks = False

            context_dict["projects"] = projects
            context_dict["advisor_levels"] = advisor_levels
            context_dict["count"] = count
            context_dict["all_levels"] = all_levels
            context_dict["all_ranks"] = all_ranks
            context_dict["no_levels"] = no_levels
            return render(request, 'alloa_matching/admin_proposal.html/', context=context_dict)

        # If user is an academic
        if request.session["user_type"] == "AC":

            # Get all projects and load project proposal form
            context_dict["results"] = Project.objects.filter(instance=instance)
            form=ProposalForm()
            context_dict["form"] = form
            # If form has been submitted
            if request.method == "POST":
                # Get form and check validity
                form = ProposalForm(request.POST)
                if form.is_valid():
                    # Send error message if project name already used in this instance or if theres a problem with project capacities
                    if Project.objects.filter(name=form.cleaned_data.get('name'),instance=instance).exists():
                        messages.error(request,"A project already exists with this name for this instance.")
                    elif form.cleaned_data.get('upper_cap') < 1:
                        messages.error(request,"Upper capacity must be at least one.")
                    elif form.cleaned_data.get('lower_cap') < 0:
                        messages.error(request,"Lower capacity must not be a negative number.")
                    elif form.cleaned_data.get('lower_cap') > form.cleaned_data.get('upper_cap'):
                        messages.error(request,"Upper capacity must be equal to or larger than lower capacity.")
                    # If valid
                    else:
                        # Save project and set proposer as expert advisor on this project
                        project = Project(name=form.cleaned_data.get('name'),description=form.cleaned_data.get('description'),upper_cap=form.cleaned_data.get('upper_cap'),lower_cap=form.cleaned_data.get('lower_cap'),instance=instance)
                        project.save()
                        user_profile = UserProfile.objects.get(user=request.user)
                        academic = Academic.objects.get(user_profile=user_profile,instance=instance)
                        advisor_level = AdvisorLevel(project=project,academic=academic,level=1)
                        advisor_level.save()
                        # Redirect to instance page to load a fresh form
                        messages.success(request, "Project added successfully.")
                        return redirect(reverse('instance',kwargs={"instance_id":instance_id}))

            return render(request, 'alloa_matching/academic_proposal.html/',context=context_dict)

        # If user is a student redirect to the home page
        if request.session["user_type"] == "ST":
            messages.error(request,"This instance is not currently available to you.")
            return redirect(reverse('home'))

    # If instance is in Advisor level ranking stage
    if instance.stage == "L":
        # If user is an admin
        if request.session["user_type"] == "AD" or request.session["user_type"] == "SA":
            # Get all projects currently added and output them so admin can judge how many have been proposed
            projects = Project.objects.filter(instance=instance)
            advisor_levels = []
            no_levels = []
            count = 0
            all_levels = True
            # For each project get their advisor levels
            for project in projects:
                levels = AdvisorLevel.objects.filter(project=project)
                # Add all levels to the level list
                advisor_levels.append(levels)
                count += len(levels)
                # If a project doesn't have any advisor levels set, store in unranked list and set boolean to false so admin cannot move stage
                if len(levels) == 0:
                    all_levels = False
                    no_levels.append(project)

            # Get all student rankings, check whether students have enough rankings to move straight to closed stage
            students = Student.objects.filter(instance=instance)
            all_ranks = True
            for student in students:
                if len(Choice.objects.filter(student=student))<instance.min_pref_len or len(Choice.objects.filter(student=student))>instance.max_pref_len:
                    all_ranks = False

            context_dict["projects"] = projects
            context_dict["advisor_levels"] = advisor_levels
            context_dict["count"] = count
            context_dict["all_levels"] = all_levels
            context_dict["all_ranks"] = all_ranks
            context_dict["no_levels"] = no_levels
            return render(request, 'alloa_matching/admin_levels.html/', context=context_dict)

        # If user is an academic
        if request.session["user_type"] == "AC":
            # Get all projects and get instance profile of current user
            context_dict["results"] = Project.objects.filter(instance=instance)
            user_profile = UserProfile.objects.get(user=request.user)
            academic = Academic.objects.get(user_profile=user_profile,instance=instance)
            context_dict["levels"] = AdvisorLevel.objects.filter(academic=academic)
            # Load advisor level form
            form=AdvisorLevelForm()
            context_dict["form"] = form
            # If form has been submitted
            if request.method == "POST":
                # Load form results and check validity
                form = AdvisorLevelForm(request.POST)
                if form.is_valid():
                    # If ranked project exists
                    if Project.objects.filter(name=form.cleaned_data.get('name'),instance=instance).exists():
                        # Get project and either set new advisor level or overwrite existing level
                        project = Project.objects.get(name=form.cleaned_data.get('name'),instance=instance)
                        if AdvisorLevel.objects.filter(project=project,academic=academic).exists():
                            alevel = AdvisorLevel.objects.get(project=project,academic=academic)
                            alevel.level = form.cleaned_data.get('level')
                            alevel.save()
                            messages.success(request, "Advisor level updated successfully.")
                        else:
                            alevel = AdvisorLevel(project=project,academic=academic,level=form.cleaned_data.get('level'))
                            alevel.save()
                            messages.success(request, "Advisor level added successfully.")
                            return redirect(reverse('instance',kwargs={"instance_id":instance.id}))
                    # If project doesnt exist throw error (Should be impossible with read only project field)
                    else:
                        messages.error(request,"Invalid project name provided")

            return render(request, 'alloa_matching/academic_levels.html/',context=context_dict)

        # If user is a student redirect to home page
        if request.session["user_type"] == "ST":
            messages.error(request,"This instance is not currently available to you.")
            return redirect(reverse('home'))

    # If instance is in student ranking stage
    if instance.stage == "S":
        # If user is a student
        if request.session["user_type"] == "ST":
            # Load their profile and current ranks to be added to the form
            user_profile = UserProfile.objects.get(user=request.user)
            student = Student.objects.get(user_profile=user_profile, instance=instance)
            ranks = Choice.objects.filter(student=student)
            initial = []
            context_dict["initial_length"] = len(ranks)
            # Either add the project name or a null value to the form
            for r in ranks:
                initial.append({"project":r.project.name})
            for i in range(instance.max_pref_len-len(ranks)):
                initial.append({"project":''})
            # Load the formset with extra values to add up to the max preferennce list length
            RankFormSet = formset_factory(RankForm,extra=(instance.max_pref_len-len(initial)),max_num=instance.max_pref_len)
            formset = RankFormSet(initial=initial)

            # If formset has been submitted
            if request.method == "POST":
                preferences = []
                # Get each submitted preference
                for i in range(instance.max_pref_len):
                    name = "project_name_" + str(i)
                    data = request.POST.get(name)
                    if data != '':
                        preferences.append(data)
                # Check all preferences are unique
                if len(set(preferences)) == len(preferences):
                    # Wipe all existing preferences and create the new ones
                    Choice.objects.filter(student=student).delete()
                    for i in range(len(preferences)):
                        project = Project.objects.get(name=preferences[i],instance=instance)
                        choice = Choice(project=project,student=student,rank=i+1)
                        choice.save()
                    # If list is too short, update but add warning for student
                    if len(preferences) < instance.min_pref_len:
                        messages.success(request,"Ranking List updated successfully, however your ranking list is now below the minimum length, please rank another " + str(instance.min_pref_len-len(preferences)) + " project(s).")
                    else:
                        messages.success(request,"Ranking List updated successfully.")
                    # Redirect to rankings page
                    return redirect(reverse('instance',kwargs={"instance_id":instance.id}))
                # Throw error if projects are not unique
                else:
                    messages.error(request,"All projects ranked must be unique.")
            # Get all projects and get instance profile of current user
            context_dict["results"] = Project.objects.filter(instance=instance)
            context_dict["formset"] = formset
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
        # If user is an admin
        if request.session["user_type"] == "AD" or request.session["user_type"] == "SA":
            # Get all students assigned to the instance
            students = Student.objects.filter(instance=instance_id)
            results = []
            matched = []
            unranked = []
            all_ranks = True
            # For each student
            for student in students:
                # If student has given ranks, get all their ranked projects
                if Choice.objects.filter(student=student).exists():
                    matched.append(student)
                    result = Choice.objects.filter(student=student)
                    edited_result = []
                    if len(result) < instance.max_pref_len:
                        if len(result) < instance.min_pref_len:
                            all_ranks = False
                        for i in range(len(result)):
                            edited_result.append(result[i].project.name)
                        for i in range(instance.max_pref_len - len(result)):
                            edited_result.append("Unranked")
                    results.append(edited_result)

                # Otherwise add student to unranked list
                else:
                    all_ranks = False
                    unranked.append(student)
            context_dict["all_ranks"] = all_ranks
            context_dict["range"] = [*range(1,instance.max_pref_len+1,1)]
            context_dict["results"] = zip(matched,results)
            context_dict["unranked"] = unranked
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
            matched = []
            unranked = []
            # For each student
            for student in students:
                # If student has given ranks, get all their ranked projects
                if Choice.objects.filter(student=student).exists():
                    matched.append(student)
                    result = Choice.objects.filter(student=student)
                    edited_result = []
                    if len(result) < instance.max_pref_len:
                        for i in range(len(result)):
                            edited_result.append(result[i].project.name)
                        for i in range(instance.max_pref_len - len(result)):
                            edited_result.append("Unranked")
                    results.append(edited_result)

                # Otherwise add student to unranked list
                else:
                    unranked.append(student)

            # Get all projects currently added and output them so admin can judge how many have been proposed
            projects = Project.objects.filter(instance=instance)
            advisor_levels = []
            no_levels = []
            # For each project get their advisor levels
            for project in projects:
                levels = AdvisorLevel.objects.filter(project=project)
                # Add all levels to the level list
                advisor_levels.append(levels)
                # If a project doesn't have any advisor levels set, store in unranked list and set boolean to false so admin cannot move stage
                if len(levels) == 0:
                    no_levels.append(project)

            # Load admin closed page
            context_dict["projects"] = projects
            context_dict["advisor_levels"] = advisor_levels
            context_dict["no_levels"] = no_levels
            context_dict["projects"] = levels
            context_dict["range"] = [*range(1,instance.max_pref_len+1,1)]
            context_dict["results"] = zip(matched,results)
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

@login_required
def set_stage(request,instance_id,new_stage):
    instance = Instance.objects.get(id=instance_id)
    instance.stage = new_stage
    instance.save()
    messages.success(request,"Stage updated successfully.")
    return redirect(reverse('instance', kwargs={"instance_id": instance.id}))

@login_required
def remove_level(request,instance_id,level_id):
    AdvisorLevel.objects.get(id=level_id).delete()
    messages.success(request, "Advisor level removed successfully.")
    return redirect(reverse('instance',kwargs={"instance_id":instance_id}))

###########################################
#                                         #
#           HELPER FUNCTIONS              #
#                                         #
###########################################

def get_instance_type(student_headings,students_min_length,project_headings,projects_min_length):

    if len(student_headings) > students_min_length:
        if len(project_headings) > projects_min_length:
            return "all_rankings"
        else:
            return "no_academic_rankings"
    elif len(project_headings) > projects_min_length:
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