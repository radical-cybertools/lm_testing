
from lm import LM


# ------------------------------------------------------------------------------
class LM_FORK(LM):

    # --------------------------------------------------------------------------
    #
    def __init__(self, nodes):

        pass


    # --------------------------------------------------------------------------
    #
    def close(self):

        pass


    # --------------------------------------------------------------------------
    #
    def prepare_task(self, pwd, task):
        '''
        Create a shell script for the given task.
        Return a command to run it.
        '''

        tid   = task['uid']
        exe   = task['exe']
        args  = task['args']
        slots = task['slots']

        fsh   = '%s/%s.sh'  % (pwd, tid)
        fout  = '%s/%s.out' % (pwd, tid)
        ferr  = '%s/%s.err' % (pwd, tid)

        clist = list()

        with open(fsh, 'w') as f:

            f.write('#!/bin/sh\n\n')

            for node_uid, node_name, cores, gpus in slots:

                f.write('export OMP_NUM_THREADS=%d\n' % len(cores)) 
                f.write('%s %s 1>>%s 2>>%s &\n\n' % (exe, args, fout, ferr))
                for c in cores:
                    clist.append(str(c))

            f.write('wait\n\n')

        task['cmd'] = 'taskset -c %s /bin/sh %s' % (','.join(clist), fsh)

        self.dump_task(task)

        return task['cmd']


# ------------------------------------------------------------------------------

