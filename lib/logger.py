#! /usr/bin/env python

"""Provides methods to log events and messages to the console."""

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
