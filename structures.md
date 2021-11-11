Runner objects ->   data_objects list -> List of FileData objects
                    config dict -> passed in from settings parse_config function
                                    {allocation_path (output allocation csv path),
                                     allocation_profile_path (output allocation txt path),
                                     level_paths (list of paths to students,projects and academics csv),
                                     randomised (boolean)}
                    graph -> initially none, created later
    FileData objects ->     randomiser boolean
                            delimiter string -> default comma for csv
                            quoting int (3 for all FileData objects, maybe number of files?)
                            level int -> 1 for students, 2 for projects, 3 for academics
                            file path -> csv files not stored so unsure what to do here (may not be used)
                            hieracrchy function -> takes level as input so always 3 for input (see alloa.agents)
                            file_content list -> List of line objects
        Line objects ->     Line list -> list of strings of raw_data
                            raw_name string -> first element of line, always name of project/student/academic
                            capacities list -> 2nd and 3rd elements of line converted to ints in and length 2 list
                            raw_preferences list -> all other elements of line, project academic choices/student project choices