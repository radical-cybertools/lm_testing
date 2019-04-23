
import os 

from lm import LM


# ------------------------------------------------------------------------------
class LM_JSRUN_ERF(LM):

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
        For the given task, prepare a jsrun resource file and execute return
        a jsrun command line to execute the task via jsrun.
        '''

        pwd     = os.path.abspath(pwd)

        tid     = task['uid']
        exe     = task['exe']
        args    = task['args']
        slots   = task['slots']

        fout    = '%s/%s.out' % (pwd, tid)
        ferr    = '%s/%s.err' % (pwd, tid)
        fcmd    = '%s/%s.cmd' % (pwd, tid)
        ferf    = '%s/%s.erf'  % (pwd, tid)

        rank    = 0
        erf_str = '\ncpu_index_using: physical\n'

        for node_uid, node_name, cores, gpus in slots:

            cores = [str(c) for c in cores]
            gpus  = [str(g) for g in gpus ]

            node_uid = int(node_uid) + 1
            erf_str += 'rank: %d: {host: %d' % (rank, node_uid)
            if cores: erf_str += '; cpu: {%s}' % ','.join(cores)
            if gpus : erf_str += '; gpu: {%s}' % ','.join(gpus)
            erf_str += ' }\n'
            rank    += 1

        erf_str += '\n'

        with open(ferf, 'w') as f:
            f.write('\n%s\n' % erf_str)

        task['cmd'] = 'jsrun --erf_input %s %s %s 1>%s 2>%s' \
                    % (ferf, exe, args, fout, ferr)

        with open(fcmd, 'w') as f:
            f.write('\n%s\n' % task['cmd'])

        self.dump_task(task)

        return task['cmd']


# ------------------------------------------------------------------------------

