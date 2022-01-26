import os
import sys
import random
import math
from copy import deepcopy


        
class SPA_IG:
    def __init__(self, students, lower_bound, upper_bound):

        self.students = students
        self.projects = int(math.ceil(0.5*self.students)) # number of projects is 0.5 * number of students
        self.lecturers = int(math.ceil(0.2*self.students))  # number of lecturers is 0.2 * number of projects
        self.tpc = int(math.ceil(1.2*self.students))  # total project upper capacity is 1.2 * number of students
        self.li = lower_bound # minimum length of each student's preference list
        self.lj = upper_bound # maximum length of each student's preference list

        self.sp = {}  # dictionary mapping each student to their preference list
        self.plc = {} # dictionary mapping each project to:
                      # - upper capacity of project (assume lower capacity is 0)
                      # - lecturer offering the project
        self.lp = {}  # dictionary mapping each lecturer to:
                      # - upper capacity (assume lower capacity is 0)
                      # - maximum capacity of all projects offered
                      # - total capacity of all projects offered

    def generate_instance(self):

        # -----------------------------------------------------------------------------------------------------------------------------------------
        # ---------------------------------------        ====== PROJECTS =======                    -----------------------------------------------
        # -----------------------------------------------------------------------------------------------------------------------------------------
        initcap = self.tpc//self.projects # initial capacity of each project is total project capacity / number of students (discarding remainder)
        self.plc = {'p'+str(i): [initcap, ''] for i in range(1, self.projects+1)} # create dictionary mapping each project to project info
        project_list = list(self.plc.keys()) # create list of all project IDs
        # randomly assign the remaining project capacities
        random.shuffle(project_list) # randomly shuffle project IDs
        for i in range(self.tpc - initcap*self.projects): # for as many times as the remainder
            self.plc[project_list[i]][0] += 1 # increment upper capacity of randomly-selected project by 1

        # -----------------------------------------------------------------------------------------------------------------------------------------
        # ---------------------------------------        ====== STUDENTS =======                    -----------------------------------------------
        # -----------------------------------------------------------------------------------------------------------------------------------------
        self.sp = {'s' + str(i): [] for i in range(1, self.students + 1)}  # create dictionary mapping each student to their preference list
        for student in self.sp: # for each student in the dictionary
            length = random.randint(self.li, self.lj)  # randomly decide the length of each student's preference list where li<=length<=lj
            #  based on the length of their preference list, we provide projects at random
            projects_copy = project_list[:] # create copy of list of projects
            random.shuffle(projects_copy) # randomly shuffle list of projects
            for i in range(length): # take the first k projects from the shuffled project list where k=length
                p = projects_copy[i]
                self.sp[student].append(p) # append each selected project to student's preference list

        # -----------------------------------------------------------------------------------------------------------------------------------------
        # ---------------------------------------        ====== LECTURERS =======                    ----------------------------------------------
        # -----------------------------------------------------------------------------------------------------------------------------------------
        self.lp = {'l' + str(i): [0, 0, 0] for i in range(1, self.lecturers + 1)}  # create dictionary mapping each lecturer to lecturer info
        lecturer_list = list(self.lp.keys()) # create list of all lecturer IDs
        upper_bound = math.floor(self.projects / self.lecturers) # set number of projects that each lecturer will initially offer
        projects_copy = project_list[:]  # deep copy all the projects
        for lecturer in self.lp:
            # assign some random projects to this lecturer
            number_of_projects = random.randint(1, upper_bound) # generate random number of projects that this lecturer will offer (between 1 and upper_bound)
            for i in range(number_of_projects):
                p = random.choice(projects_copy) # choose a random project
                projects_copy.remove(p)  # avoids picking the same project twice over
                self.plc[p][1] = lecturer  # take note of the lecturer who is offering the project
                self.lp[lecturer][2] += self.plc[p][0]  # increase the total project capacity
                if self.plc[p][0] > self.lp[lecturer][1]:  # keep track of the project with the highest capacity
                    self.lp[lecturer][1] = self.plc[p][0]
        # -----------------------------------------------------------------------------------------------------------------------------------------
        # if at this point some projects are still yet to be assigned to a lecturer
        while projects_copy:
            p = projects_copy.pop()  # remove a project from end of the list
            lecturer = random.choice(lecturer_list)  # pick a lecturer at random
            self.plc[p][1] = lecturer  # take note of the lecturer who is offering the project
            self.lp[lecturer][2] += self.plc[p][0]  # increase the total project capacity
            if self.plc[p][0] > self.lp[lecturer][1]: # keep track of the project with the highest capacity
                self.lp[lecturer][1] = self.plc[p][0]
        # -----------------------------------------------------------------------------------------------------------------------------------------
        #  Now each lecturer's capacity is a random integer between the maximum and total capacity of the projects they offer
        for lecturer in self.lp:
            self.lp[lecturer][0] = random.randint(self.lp[lecturer][1], self.lp[lecturer][2])  # set upper capacity for each lecturer

        # -----------------------------------------------------------------------------------------------------------------------------------------

    def write_instance(self, k, instance_type):  # writes the SPA instance to a txt file
        # Student details and rankings
        if instance_type == 1 or instance_type == 3:
            if __name__ == '__main__':
                filename = 'students'+str(k)+'.csv'  # create students.csv for kth instance
                with open(filename, 'w') as I:
                    I.write('Matric Number,Student Firstname,Student Surname,Student Lower Capacity,Student Upper Capacity,Choice 1,Choice 2,Choice 3,Choice 4,Choice 5,Choice 6,Choice 7\n')
                    for stud_num in range(1, self.students + 1): # for all students
                        I.write('2386'+str(stud_num)+',Firstname'+str(stud_num)+',Lastname'+str(stud_num) + ',0,1,') # assume student lower and upper capacities are 0 and 1 respectively
                        preference = self.sp['s'+str(stud_num)] # get preference list of student n
                        sliced = ['Project'+p[1:] for p in preference] # prepend 'Project' to project ID in each preference list position
                        I.writelines(','.join(sliced)) # write out preference list of student n in required format
                        I.write('\n')
                    I.close()
        # Only student details
        if instance_type == 2 or instance_type == 4 or instance_type == 5:
            if __name__ == '__main__':
                filename = 'students'+str(k)+'.csv'  # create students.csv for kth instance
                with open(filename, 'w') as I:
                    I.write('Matric Number,Student Firstname,Student Surname,Student Lower Capacity,Student Upper Capacity\n')
                    for stud_num in range(1, self.students + 1): # for all students
                        I.write('2386'+str(stud_num)+',Firstname'+str(stud_num)+',Lastname'+str(stud_num) + ',0,1') # assume student lower and upper capacities are 0 and 1 respectively
                        I.write('\n')
                    I.close()
        # Projects 
        if instance_type == 1 or instance_type == 2:
            filename = 'projects'+str(k)+'.csv' # create projects.csv for kth instance
            with open(filename, 'w') as I:
                I.write('Project,Project Lower Capacity,Project Upper Capacity,Choice 1,Choice 2,Choice 3\n')
                for proj_num in range(1, self.projects + 1): # for all projects
                    project = 'p'+str(proj_num) # get project ID
                    capacity = self.plc[project][0] # get upper capacity of project
                    lecturer = self.plc[project][1][1:] # get lecturer who offers that project
                    I.write('Project'+str(proj_num) + ',0,' + str(capacity) + ',ID' + str(lecturer)+',,') # write out info for project in required format
                    I.write('\n')
                I.close()
        # Only projects no advisor levels
        if instance_type == 3 or instance_type == 4:
            filename = 'projects'+str(k)+'.csv' # create projects.csv for kth instance
            with open(filename, 'w') as I:
                I.write('Project,Project Lower Capacity,Project Upper Capacity\n')
                for proj_num in range(1, self.projects + 1): # for all projects
                    project = 'p'+str(proj_num) # get project ID
                    capacity = self.plc[project][0] # get upper capacity of project
                    lecturer = self.plc[project][1][1:] # get lecturer who offers that project
                    I.write('Project'+str(proj_num) + ',0,' + str(capacity)) # write out info for project in required format
                    I.write('\n')
                I.close()
        # Academics
        filename = 'academics'+str(k)+'.csv' # create academics.csv for kth instance
        with open(filename, 'w') as I:
            I.write('Staff ID,Supervisor Firstname,Supervisor Surname,Supervisor Lower Capacity,Supervisor Upper Capacity\n')
            for lec_num in range(1, self.lecturers + 1): # for all lecturers
                lecturer = 'l'+str(lec_num) # get lecturer ID
                capacity = self.lp[lecturer][0] # get upper capacity of lecturer
                I.write('ID'+str(lec_num)+',AcademicFN'+str(lec_num) + ',AcademicSN'+str(lec_num) +',0,' + str(capacity) + ' ') # write out info for lecturer in required format
                I.write('\n')
            I.close()

#Entry point
students = int(sys.argv[1]) # number of students
pref_lb = int(sys.argv[2]) # minimum length of each student's preference list
pref_ub = int(sys.argv[3]) # maximum length of each student's preference list
num_reps = int(sys.argv[4]) # number of instances to generate
instance_type = int(sys.argv[5]) # Type of instance to generate

if instance_type > 0 and instance_type < 6:
    for k in range(0, num_reps): # for each instance number
        S = SPA_IG(students, pref_lb, pref_ub) # call constructor
        S.generate_instance() # generate instance
        S.write_instance(k+1,instance_type) # write instance files for instance k+1
else:
    print("Invalid instance type")
