# Timelog

* PROJECT NAME
* Douglas Russell
* 2386206R
* David Manlove

## Guidance

* This file contains the time log for your project. It will be submitted along with your final dissertation.
* **YOU MUST KEEP THIS UP TO DATE AND UNDER VERSION CONTROL.**
* This timelog should be filled out honestly, regularly (daily) and accurately. It is for *your* benefit.
* Follow the structure provided, grouping time by weeks.  Quantise time to the half hour.

## Week 1

### 1 Oct 2021
* *0.5 hour* First meeting with advisor discussing algorithm requirements and desired outputs

## Week 2

### 7 Oct 2021
* *2 hours* Initial planning of my ideas for project, collecting questions to ask at advisor meeting 
* *1 hours* Sketched ER diagram to help visualise project structure and show advisor

### 8 Oct 2021
* *1 hours* Second advisor meeting, got answers for all my questions 
* *2 hours* Created priority list for project, different stages of release I hope to reach

## Week 3

### 14 Oct 2021
* *2 hours* Cloned alloa repository and ran on my PC, went through code to try and understand algorithm better
* *2 hours* Setup django project and alloa app

### 15 Oct 2021
* *1 hour* 3rd advisor meeting, channged priorities slightly and added to them, moving on to planning database

## Week 4

### 20 Oct 2021
* *3 hours* Formally created ER Diagram 
* *2 hours* Created Models.py file based off of ER Diagram

### 22 Oct 2021 
* *1 hour* 4th advisor meeting, ER diagram was too complicated and can be simplified down, able to assume students are only on one course at a time currently

## Week 5

### 26 Oct 2021
* *1 hour* Redoing ER Diagram as discussed in previous meeting and redoing models.py to match the new diagram

### 27 Oct 2021
* *3 hours* Creating view for uploading files, creating file upload form, and saved files in dictionaries

### 28 Oct 2021
* *3 hours* Saved dictionaries into database 

### 29 Oct 2021
* *1 hour* Created a clean database function and added forms to add the name and level of the instance
* *1 hour* Meeting with advisor discussing next steps - setup data structures and run alloa

## Week 6

### 4 Nov 2021
* *4 hours* Investigating original Alloa code to find data structures that I will need to pass in from the database
* Had to cancel advisor meeting as had not had a chance to do much work this week until after meeting had passed

## Week 7

### 8 Nov 2021
* *1 hour* Created structures.md to record all findings and objects I need to create to use the graph_builder function from alloa

### 9 Nov 2021
* *3 hours* Querying database to get necessary data and storing in dictionary representation

### 10 Nov 2021
* *3 hours* Creating objects and converting dictionaries to instances of these objects

### 11 Nov 2021
* *1 hour* Advisor meeting - discussing structure I found and created classes

## Week 8

### 17 Nov 2021
* *2 hours* Going through alloa graph building stages trying to understand the structures that are created and how they are outputted 

* Had very little time to work this week as several courseworks were due

## Week 9

### 21 Nov 2021

* *2 hours* Started to implement the graph builder functions to try and create an allocation graph
* *1 hour* Decided to change approach and copy the .py files from orignial alloa and import all the classes instead of recreating them

### 23 Nov 2021

* *3 hours* Implementing the classes and functions now they are being imported, recreating what happens in run.py in my view function

### 24 Nov 2021

* *2 hours* Taking output from alloa implementation and saving results to the database, need to separate instances that have been computed

### 25 Nov 2021

* *1 hour* Created list view for all instances and instance results
* *1 hour* Added booleans for instances for if they are available to students, closed for making choices and if their matching has been computed or stored. Used these to check if matching needs to be computed or can be loaded from database.
* *30 mins* Created list of final project allocations for an instance

### 26 Nov 2021

* *1 hour* Advisor meeting, working out next steps after must haves completed

## Week 10

### 30 Nov 2021

* *2 hours* Created planning diagram for should have steps
* *1 hour* Planning status splits for instances

### 2 Dec 2021

* *2 hours* Planning out versions of pages depending on instance status and user type

### 3 Dec 2021

* *1 hour* Advisor meeting, making slight changes to plan and stages

## Week 11

### 8 Dec 2021

* *3 hours* Starting wireframing

### 9 Dec 2021

* *1 hour* Advisor meeting, showing wireframes, discussing potential changes

## Week 12 

### 13 Dec 2021

* *2 hours* Allocation viewing pages wireframing
* *1 hour* Added stage enum variable for instances

### 14 Dec 2021

* *1 hour* Starting to implement home page, needed to generate more instances for testing
* *3 hours* Editing instance generator to generate relevant data for database

### 16 Dec 2021

* *1 hour* Advisor meeting - discussed planned progress over christmas break
* *3 hours* Writing end of semester status report

## Week 15

### 4 Jan 2022

* *2 hours* Login view made and session variables for user type setup
* *3 hours* Base template created
* *2 hours* logout made and session variables deleted after use

## Week 16

### 10 Jan 2022

* *3 hours* Compute matching view moved and converted to a redirect
* *2 hours* View instance view separated into different stages and user types
* *30 mins* Looking for javascript table search and sort plugin, settled on datatables