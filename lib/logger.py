#! /usr/bin/env python

"""Provides methods to log information to the console and process logs."""

import time, traceback

def log(event, message=''):
    """
    Logs to console in specific format: [time] event : message.
    
    Returns time.clock() at which log() was called.
    """
    t = time.clock()
    print '[ %10.8f ] %20.20s : %s' % (t, event, message)
    return t


def log_runtime_of(function):
    """
    Runs $function and logs its start, end, and runtime.

    Tip: use lambda to run functions which take parameters, like so:
        log_runtime_of(lambda: f(arg1, arg2))

    Returns runtime of $function.
    """
    f_name = function.__name__
    f_event_str = '%-10.s %s' % (function.__name__, '%9.9s')

    start = log(f_event_str % '<start>')
    function_output = function()
    end = log(f_event_str % '<end>')
    
    runtime = end-start
    log(f_event_str % '<runtime>', 
        '%10.10s() runtime was %10.8f' % (f_name, runtime))

    return (runtime, function_output)


def log_error(e, event=''):
    """
    Logs an error as 
        
        [time] error.type : error.value

    If $event specified, instead logs as

        [time] $event     : error.type -> error.value
    """
    if event == '': log(type(e).__name__, e.message)
    else:           log(event, '%s -> %s' % (type(e).__name__, e.message))
    traceback.print_exc()


def parse_runtimes(fnames):
    """
    Takes a list of filenames corresponding to files containing logs with
    runtimes, and writes to STDOUT summaries of the runtime information in said
    files (what runtimes were logged, average, and number of trials in file).
    """
    
    runtime_sum = {}
    runtime_count = {}
    
    for fname in fnames:
        f = open(fname, 'rU')
    
        for line in f:
            if 'runtime' not in line: continue
    
            line = line.split(' : ')[1].split()
    
            (fxn, runtime) = (line[0], float(line[-1]))
    
            if fxn not in runtime_sum:
                runtime_sum[fxn] = 0.0
                runtime_count[fxn] = 0
    
            runtime_sum[fxn] += runtime
            runtime_count[fxn] += 1
    
        for fxn in runtime_sum: 
            print '%10.10s : %15.15s had average runtime %12.8f ms (%4d trials)' % (
                fname, fxn, runtime_sum[fxn]/runtime_count[fxn], runtime_count[fxn])
