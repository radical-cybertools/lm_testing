
# Launch Method Tester

usaage:

    > ./lm_test.py

This will run all test cases defined in `test_cases/tc_*.json` against
4 different launch methods: fork, orte, orrte and jsrun.  The default progress
visualization is text based - other types can be selected in the main routine.

A summary line is written to `summary.txt` for each use case.  It contains the
following space delimited fields describing the test state at the end of the
respective test case:

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

The following command can be used to obtain a quick overview of the test
results:

    > cat summary.txt  | cut -f 1,2,10,15,16 -d ' ' | column -t

which formats the test case ID, launch method, total number of tasks, number of
DONE and FAILED tasks.  Ideally, all tasks end up in DONE state, which would
indicate a successful test.

The PRRTE test require `PRRTE_PREFIX` to be set correctly, like this:

    > export PRRTE_PREFIX=/home/merzky/radical/prte/install 


To enable curses based visualization, install the python module `asciimatics`:

    > virtualenv ve
    > source ve/bin/activate
    > pip install pip install asciimatics


The tests run a modified version of `hello_jsrun` which accepts a second
parameter which defines a number of seconds to sleep.  An unpatched
`hello_jsrun` will ignore that parameter.


