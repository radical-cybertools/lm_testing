
### Usage:  

        my_program.py [-tc TC ...] [-lm LM ...] [-viz VIZ] [-h]

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

```sh
        ./scratch/<launch_method>/<basename(test_case)>
```

   A summary line is written to `summary.txt` for each use case.  It
   contains the following space delimited fields describing the test state
   at the end of the respective test case:

        - test case ID
        - launch method
        - number of nodes
        - number of cores
        - number of cores still in use
        - number of cores unused
        - number of gpus
        - number of gpus still in use
        - number of gpus unused
        - number of tasks
        - number of tasks in NEW       state
        - number of tasks in WAITING   state
        - number of tasks in SCHEDULED state
        - number of tasks in RUNNING   state
        - number of tasks in DONE      state
        - number of tasks in FAILED    state

   The following command can be used to obtain a quick overview of the
   test results:

        > cat summary.txt  | cut -f 1,2,10,15,16 -d ' ' | column -t

   which formats the test case ID, launch method, total number of tasks,
   number of DONE and FAILED tasks.  Ideally, all tasks end up in DONE
   state, which would indicate a successful test.


### Options:

```
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
```

### Test Cases:

   - Test cases are specified as json files, with the following format:

```json
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
``` 

   - The following keys are supported:

```
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
```

### Example:

```sh
        > rm -r scratch/fork/tc_1/   # remove test scratch dir
        > ./lm_test.py -lm fork -tc test_cases/tc_1.json

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

        > cat summary.txt  | cut -f 1,2,10,15,16 -d ' ' | column -t
        tc_1  fork  42  42  0
```

### Notes:

   - The PRRTE test require `PRRTE_PREFIX` to be set correctly,
     like this:

```sh
        > export PRRTE_PREFIX=/home/merzky/radical/prte/install 
```

   - To enable curses based visualization, install the python
     module `asciimatics`:

```sh
        > virtualenv ve
        > source ve/bin/activate
        > pip install pip install asciimatics
```

   - The tests run a modified version of `hello_jsrun` which accepts
     a second parameter which defines a number of seconds to sleep.
     An unpatched `hello_jsrun` will ignore that parameter, potentially
     yielding different test results due to increased system pressure.


### Missing Features:

   - radical.pilot should  be added as test backend
   - non-interactive mode: the tasks are not be executed, but but
     a qsub script is to be created for each of the above, and the
     workload execution prepared up to the point where only the node
     list is used to determine the actual node names to be used.
   - better evaluation of test results

