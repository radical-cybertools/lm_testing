#!/usr/bin/env python

'''

        my_program.py [-tc TC ...] [-lm LM ...] [-viz VIZ] [-h]

Purpose:

        This script consumes a set of test cases (test_cases/tc_*.json).
        For each test case, it will create a workload as described, and
        will prepare to run that workload via

          - fork
          - jsrun 
          - prrte (prun)
          - orte  (orte-submit)

        For the `prrte` and `orte` launchers, a  DVM is created and terminated
        on the fly, for each test case.  The state of all nodes used is reset
        between individual test cases

        Test runs will create subdirectories under `./scratch/`.  Runs will be
        skipped if the respective directory exist.  The name is formed as:

            ./scratch/<launch_method>/<basename(test_case)>

Options:
        -h               : this screen.
        --launch-methods
        -lm LM_1 ...     : select launch methods to test
                           available: fork, jsrun, prrte, orte
                           default  : all
        --test-cases
        -tc TC_1 ...     : select test cases to test against
                           available: see subdir `test_cases`
                           default  : all 
        --visualizer
        -v  VIZ          : select visualization methods
                           available: curses, simple, text, mute (off)
                           default  : text


Test Cases:

        Test cases are specified as json files, with the following format:

            {
                "comment"   : "20 tasks of random size on 1 node",
                "nodes"     : 1,
                "cpn"       : 42, 
                "gpn"       : 6, 

                "tasks"     : 20,
                "procs"     : [1, 20],
                "threads"   : 1,
                "gpus"      : 0,
                "exe"       : "hello_jsrun verbose 3"
            }

        The following keys are supported:

            - 'comment' : description of test case (optional)
            - 'nodes'   : number of nodes to allocate for the test
            - 'cpn'     : cores per node
            - 'gpn'     : gpus  per node

            - 'tasks'   : number of tasks to run in this test case
            - 'procs'   : number of processes per task
            - 'threads' : number of threads per process
                          threads are spawned by the workload.
                          OMP_NUM_THREADS is set for the process.
            - 'gpus'    : number of GPU devices per process.
            - 'exe'     : workload to execute
                          This will usually be something like 'hello_jsrun' or
                          some other LM specific workload which can be used to
                          verify LM correctness.

Example:
        $ rm -r scratch/fork/tc_1/   # remove test scratch dir
        $ ./lm_test.py -lm fork -tc test_cases/tc_1.json

         ----------------------------------------------------------------
         text case: tc_1 [ fork ]

         ||  cores |   busy |   free ||   gpus |   busy |   free ||  tasks |    new |   wait |  sched |    run |   done |   fail ||
         ||     42 |      0 |     42 ||      6 |      0 |      6 ||     42 |     42 |      0 |      0 |      0 |      0 |      0 ||
         ||     42 |     42 |      0 ||      6 |      0 |      6 ||     42 |      0 |      0 |     42 |      0 |      0 |      0 ||
         ||     42 |     42 |      0 ||      6 |      0 |      6 ||     42 |      0 |      0 |      0 |     42 |      0 |      0 ||
         ||     42 |     39 |      3 ||      6 |      0 |      6 ||     42 |      0 |      0 |      0 |     39 |      3 |      0 ||
         ||     42 |     31 |     11 ||      6 |      0 |      6 ||     42 |      0 |      0 |      0 |     31 |     11 |      0 ||
         ||     42 |     14 |     28 ||      6 |      0 |      6 ||     42 |      0 |      0 |      0 |     14 |     28 |      0 ||
         ||     42 |      0 |     42 ||      6 |      0 |      6 ||     42 |      0 |      0 |      0 |      0 |     42 |      0 ||

        $ cat summary.txt
        tc_1 fork 1 42 0 42 6 0 6 42 0 0 0 0 42 0

Missing Features:

        - radical.pilot should  be added as test backend
        - non-interactive mode: the tasks are not be executed, but but
          a qsub script is to be created for each of the above, and the
          workload execution prepared up to the point where only the node
          list is used to determine the actual node names to be used.
        - better evaluation of test results

.
'''

import os
import sys
import glob
import json
import time
import pprint
import random
import argparse

import subprocess as sp

from viz import VIZ  # visualizers
from lm  import LM   # launch methods

from constants import FREE, BUSY
from constants import NEW, WAITING, SCHEDULED, RUNNING, DONE, FAILED


'''
'''


# ------------------------------------------------------------------------------
#
def create_nodes(pwd, tc):
    ''''
    create a list of nodes (with core and gpu slots) which we can use to place
    tasks.  The returned list has the following structure:

        [ 
            [node_id, [cores]. [gpus]],  
            [node_id, [cores]. [gpus]], 
            ...
        ]

    where:

      node_id: integer, 0-based
      cores  : list of bools, one per core, where `BUSY` indicates a used core
      gpus   : list of bools, one per core, where `BUSY` indicates a used gpu

    All cores and gpus are initially not used.

    NOTE: this uses logical node IDs, the physical node names are not known at
    this point.
    '''

    nodes = list()
    for n in range(tc['nodes']):
        nodes.append([str(n), [FREE] * tc['cpn'], [FREE] * tc['gpn']])

    return nodes


# ------------------------------------------------------------------------------
#
def create_tasks(pwd, tc):
    '''
    from a test case description like this:

        {
            "pnodes"    : 1, 
            "procs"     : [1, 20],
            "threads"   : 1,
            "gpus"      : 0,
            "time"      : 60,
            "tasks"     : 20,
            "executable": "jsrun_layout"
        }

    create a set of task descriptions representing the requested tasks.  A task
    description here is dict which contains:

      - 'uid'  : a unique ID
      - 'exe'  : the workload to execute
      - 'procs': a list of process descriptions, where each process has some
                 resource requirements (nunmber of cores and gpus).
    '''

    tasks = list()
    for tid in range(tc['tasks']):

        n_cores = tc['threads']
        n_gpus  = tc['gpus']
        tmp     = tc['procs']
        if isinstance(tmp, list):
            if len(tmp) == 2:  # min/max
                n_procs = random.randint(tmp[0], tmp[1])
            else:                  # list of choices
                randidx = random.randint(0, len(tmp) - 1)
                n_procs = tmp[randidx]
        else:
            n_procs = tmp

        task = {'uid'     : 'task.%06d' % tid, 
                'exe'     : tc['exe'],
                'n_procs' : n_procs,
                'n_gpus'  : n_gpus,
                'n_cores' : n_cores,
                'procs'   : [[n_cores, n_gpus] for _ in range(n_procs)],
                'state'   : NEW
               }

        fsh = '%s/%s.json'  % (pwd, task['uid'])
        with open(fsh, 'w') as f:
            f.write('\n%s\n\n' % pprint.pformat(task))

        tasks.append(task)

    return tasks


# ------------------------------------------------------------------------------
#
def find_slot(nodes, n_cores, n_gpus):
    '''
    Find a node in the node list which can host the requested process, and
    return 

      node_uid, [core_ids], [gpu_ids]


    A process is here defined by the number of cores and GPUs it needs to have
    available on the matc hing node.  Once a suitable node is found, the
    respective cores and GPUs are marked as BUSY.
    '''

    # iterate through node list
    for node_uid, cores, gpus in nodes:

        core_ids = list()
        gpu_ids  = list()

        # check for available cores
        for i,c in enumerate(cores):

            if len(core_ids) == n_cores:
                break               # enough cores found (or none needed)

            if c == FREE:
                core_ids.append(i)  # another one found and recorded

        # check for available GPUs
        for i,g in enumerate(gpus):

            if len(gpu_ids) == n_gpus:
                break               # enough found or none needed

            if g == FREE:
                gpu_ids.append(i)   # another gpu found and recorded

        # is the process slot is complete?
        if len(core_ids) == n_cores and \
           len(gpu_ids)  == n_gpus  :

            # mark the resources as used and return the found slot
            for cid in core_ids: cores[cid] = BUSY
            for gid in gpu_ids : gpus [gid] = BUSY

            return node_uid, core_ids, gpu_ids

    # nothing found
    return None


# ------------------------------------------------------------------------------
#
# create list of jsrun resource file according to test case
#
def schedule_tasks(tc, nodes, tasks):
    '''
    the given tasks will be expanded by a `slots` key, which will contain a list
    of tuples of the form

       [node_uid, [cores], [gpus]]

    Those tuples define where each of the task's processes is to be placed.
    If no suitable resources can be found, the key will be set to an empty list.

    The method will change the tasks which ate passed by reference, but will
    also return two sublists: one of tasks which were successfully scheduled,
    and one of those tasks which remain waiting.
    '''

    scheduled = list()
    waiting   = list()

    cpn = tc['cpn']
    gpn = tc['gpn']

    for task in tasks:

        task['slots'] = list()

        assert(task['state'] in [NEW, WAITING])

        # fail task if it does not fit on a node
        max_slot = [0, 0]
        for cores, gpus in task['procs']:
            if cores > max_slot[0]: max_slot[0] = cores
            if gpus  > max_slot[1]: max_slot[1] = gpus 

        if max_slot[0] > cpn or max_slot[1] > gpn:
            task['state'] = FAILED
            scheduled.append(task)
            continue

        # find resources - one per process
        for cores, gpus in task['procs']:

            slot = find_slot(nodes, cores, gpus)

            if not slot:
                # give up
                break

            task['slots'].append(slot)


        if len(task['slots']) == len(task['procs']):
            task['state'] = SCHEDULED
            scheduled.append(task)
        else:
            # free any slots we found
            set_slots(nodes, task['slots'], FREE)
            task['state'] = WAITING
            waiting.append(task)

    return scheduled, waiting


# ------------------------------------------------------------------------------
#
# create list of jsrun resource file according to test case
#
def set_slots(nodes, slots, state):
    '''
    The given lots will be marked as BUSY or FREE
    '''

    assert(state in [BUSY, FREE])

    for slot in slots:

        # FIXME: optimization: instead of searching for
        #        the node_uid, store the node_idx for lookups.
        ok = False
        for node_uid, cores, gpus in nodes:

            if slot[0] != node_uid:
                continue

            for cidx in slot[1]: cores[cidx] = state
            for gidx in slot[2]: gpus [gidx] = state

            ok = True
            break  # this slot is set

        if not ok:
            print 'ERROR could not set slot state: %s' % slot


# ------------------------------------------------------------------------------
#
# free task resources
#
def unschedule_tasks(nodes, tasks):
    '''
    The slots (node_uid, cores, gpus) of the given tasks will be set to FREE.
    '''

    for task in tasks:

        assert(task['state'] in [DONE, FAILED])

        set_slots(nodes, task['slots'], FREE)


# ------------------------------------------------------------------------------
#
def execute_tasks(lm, pwd, scheduled):
    '''
    Prepare the given task for excution, and run it.
    '''

    running = list()
    for task in scheduled:

        if task['state'] == FAILED:
            continue

        assert(task['state'] == SCHEDULED)

        task['cmd']   = lm.prepare_task(pwd, task)
        task['proc']  = sp.Popen(task['cmd'], shell=True)
        task['state'] = RUNNING

        running.append(task)

    return running


# ------------------------------------------------------------------------------
#
def wait_tasks(nodes, running):
    '''
    For the given set of tasks, poll the task processes and check if they are
    done.  If so, collect the return value.  For each completed task, free the
    resources it used.

    The method changes the tasks passed by reference, but also returns two
    lists, one with tasks which are completed, and one with tasks which are
    still running.
    '''

    still_running = list()  # tasks continue to run
    collected     = list()  # tasks are done

    for task in running:

        assert(task['state'] == RUNNING)

        task['ret'] = task['proc'].poll()

        if task['ret'] is None:
            still_running.append(task)
        else:
            if task['ret']: task['state'] = FAILED
            else          : task['state'] = DONE
            collected.append(task)

    # free resources
    unschedule_tasks(nodes, collected)

    return still_running, collected


# ------------------------------------------------------------------------------
#
def run_tc(launcher, visualizer, tc, pwd):
    '''
    For the given set of tasks, do the following:

      - find a set of resources to run them (schedule)
      - prepare a shell script and execute it via `fork` (popen).
      - wait for it to to complete.

    If a task cannot be scheduled, it is put on a wait list, and reschedule is
    attempted when some other task finished and frees resources
    '''

    # prepare node list, create ctasks for this tc
    nodes = create_nodes(pwd, tc)
    tasks = create_tasks(pwd, tc)

    v  = None  # visualizer
    lm = None  # launch method

    try:
        v = VIZ.create(visualizer, nodes, tc['cpn'], tc['gpn'], tasks)
        v.header('text case: %s [ %s ]' % (tc['uid'], launcher))
        v.update()

        lm = LM.create(launcher, nodes)

        waiting     = tasks
        scheduled   = list()
        running     = list()
        done        = list()
        first       = True    # first iteration

        i = 0
        while True:

            # is there *anything* to do?
            if not waiting and not scheduled and not running:
                break

            v.update()

            # are there any tasks to collect / resources to be freed?
            running, collected = wait_tasks(nodes, running)
            done += collected

            v.update()

            # are there any tasks waiting, and do we have resources?
            if first or collected:
                first = False
                scheduled, waiting = schedule_tasks(tc, nodes, waiting)
                v.update()

            # execute scheduled tasks
            running += execute_tasks(lm, pwd, scheduled)
            scheduled = list()

            # slow down, matey!
            time.sleep(0.1)
            i += 1

        v.update()

    finally:
        if v : v.close()
        if lm: lm.close(nodes)

    # summary:
    summary = '%s %s ' % (tc['uid'], launcher)

    if not nodes:
        summary += '0 0 0 0 0 0 '

    else:
        c_total = 0
        c_busy  = 0
        c_free  = 0

        g_total = 0
        g_busy  = 0
        g_free  = 0

        for node in nodes:

            c_total += len(node[1])
            c_busy  += node[1].count(BUSY)
            c_free  += node[1].count(FREE)

            g_total += len(node[2])
            g_busy  += node[2].count(BUSY)
            g_free  += node[2].count(FREE)

        summary += '%d %d %d %d %d %d %d ' \
                % (len(nodes), c_total, c_busy, c_free, g_total, g_busy, g_free)


    if not tasks:
        summary += '0 0 0 0 0 0 0'

    else:
        t_total     = len(tasks)
        t_new       = len([1 for t in tasks if t['state'] == NEW])
        t_waiting   = len([1 for t in tasks if t['state'] == WAITING])
        t_scheduled = len([1 for t in tasks if t['state'] == SCHEDULED])
        t_running   = len([1 for t in tasks if t['state'] == RUNNING])
        t_done      = len([1 for t in tasks if t['state'] == DONE])
        t_failed    = len([1 for t in tasks if t['state'] == FAILED])

        summary += '%d %d %d %d %d %d %d ' \
                % (t_total, t_new, t_waiting, t_scheduled, 
                   t_running, t_done, t_failed)

    return summary


# ------------------------------------------------------------------------------
#
if __name__ == '__main__':

    parser = argparse.ArgumentParser(usage=__doc__, add_help=False)
    parser.add_argument('-h', '--help',           action='store_true')
    parser.add_argument('-tc','--test-cases',     nargs='+', default='all')
    parser.add_argument('-lm','--launch-methods', nargs='+', default=['fork'],
                        choices=['fork', 'jsrun', 'prrte', 'orte'])
    parser.add_argument('-v','--visualizer',      nargs=1,   default=['text'],
                        choices=['curses', 'simple', 'text', 'mute'])
    args = parser.parse_args()

    if args.help:
        print __doc__
        sys.exit()

    visualizer = args.visualizer[0]
    launchers  = args.launch_methods
    tc_names   = args.test_cases

    if tc_names == 'all':
        tc_names = glob.glob("test_cases/tc_*.json")

    tcases = list()
    for fname in sorted(tc_names):
        with open(fname, 'r') as fin:
            tc = json.load(fin)

        tc['uid'] = os.path.basename(fname)[:-5]  # chop '.json']
        tcases.append(tc)


    # write error messages to file on curses output (would be lost otherwise)
    if visualizer in ['curses']:
        sys.stderr = open('err', 'w')


    with open('summary.txt', 'w') as fout:

        try           : os.mkdir('./scratch/')
        except OSError: pass

        for launcher in launchers:

            try           : os.mkdir('./scratch/%s/' % launcher)
            except OSError: pass

            for tc in tcases:

                pwd = './scratch/%s/%s/' % (launcher, tc['uid'])
                try:
                    os.mkdir(pwd)
                except OSError:
                    print
                    print 'skipping test case %s [%s] - scratch exists (%s)' \
                        % (tc['uid'], launcher, pwd)
                    print
                    continue

                summary = run_tc(launcher, visualizer, tc, pwd)
                fout.write('%s\n' % summary)


# ------------------------------------------------------------------------------

