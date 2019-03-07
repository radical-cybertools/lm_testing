

# ------------------------------------------------------------------------------
class LM_FORK(object):

    # --------------------------------------------------------------------------
    #
    def __init__(self, rm):

        self._rm = rm


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
        slots = task['slots']

        fsh  = '%s/%s.sh'  % (pwd, tid)
        fout = '%s/%s.out' % (pwd, tid)
        ferr = '%s/%s.err' % (pwd, tid)

        with open(fsh, 'w') as f:

            f.write('#!/bin/sh\n\n')

            for node_uid, cores, gpus in slots:

                f.write('export OMP_NUM_THREADS=%d\n' % len(cores)) 
                f.write('%s 1>>%s 2>>%s &\n\n' % (exe, fout, ferr))

            f.write('wait\n\n')

        cmd = '/bin/sh %s' % fsh
        return cmd


# ------------------------------------------------------------------------------

