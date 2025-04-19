# Description
**parser.py** is the main file in which constants, methods for initialization and a class are defined.
It uses multiprocessing to parse multiple files at once, but the output file is shared among all processes.
A lock was used to keep things simple and avoid errors due to file being already in use by another process created. 
An in depth analysis should be done to verify if the processing time was actually decreased or a bottleneck was introduced. This
could've been avoided by having an output file for each input, but then we should've had a method for aggregation for results.

# Installation
All packages used are shipped with python3, so theoretically there is nothing to be installed

# Defaults
```
    output_file = 'current_directory/output'
    input_logs_folder = 'current_directory/logs'
    regex_used_for_log_file = '^logs-[0-9]+.log$'
```

# Usage
```
    python -m parser [-l, --logs <path_to_logs_folder>]
    # or
    python parser.py [-l, --logs <path_to_logs_folder>]
```

# Result
An WARNING message will be present in 'output_file' if the process took longer than 5 minutes and 
an ERROR message if it took longer than 10 minutes.
Also, as INFO are logged duplicate processes (which started twice) - in this case, they are simply
discarded / deleted from map and no analysis is done for them & processes which ended but never started.
They were considered anomalies which are unlikely to happen.

# To do
Time analysis, change to a @classmethod for **parse** function to avoid
creating an object for each process, clean-up of output file