
import os 


# ------------------------------------------------------------------------------
class LM_JSRUN_ERF(object):

    # --------------------------------------------------------------------------
    #
    def __init__(self, nodes):

        pass


    # --------------------------------------------------------------------------
    #
    def close(self, nodes):

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
        slots   = task['slots']

        fout    = '%s/%s.out' % (pwd, tid)
        ferr    = '%s/%s.err' % (pwd, tid)
        fcmd    = '%s/%s.cmd' % (pwd, tid)
        ferf    = '%s/%s.erf'  % (pwd, tid)


        erf_str = '\ncpu_index_using: physical\n'
        rank = 0

        for node_uid, cores, gpus in slots:

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

        cmd = 'jsrun --erf_input %s %s 1>%s 2>%s' % (ferf, exe, fout, ferr)

        with open(fcmd, 'w') as f:
            f.write('\n%s\n' % cmd)

        return cmd


# ------------------------------------------------------------------------------

