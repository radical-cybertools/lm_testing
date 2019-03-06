
import os 


# ------------------------------------------------------------------------------
class LM_JSRUN_rs(object):

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

        pwd = os.path.abspath(pwd)

        tid    = task['uid']
        exe    = task['exe']
        slots  = task['slots']

        fout   = '%s/%s.out' % (pwd, tid)
        ferr   = '%s/%s.err' % (pwd, tid)
        fcmd   = '%s/%s.cmd' % (pwd, tid)
        frs    = '%s/%s.rs'  % (pwd, tid)

        rs_str = ''
        rs_id  = 0
        for node_uid, cores, gpus in slots:

            rs_str += 'RS %d: {'  % rs_id
            rs_str += ' host: %d' % (int(node_uid) + 1)
            if cores: rs_str += ' cpu: %s'  % ' '.join([str(c) for c in cores])
            if gpus : rs_str += ' gpu: %s'  % ' '.join([str(g) for g in gpus])
            rs_str += ' }\n'
            rs_id  += 1

        with open(frs, 'w') as f:
            f.write('\n%s\n' % rs_str)

        cmd = 'jsrun -a 1 -U %s %s 1>%s 2>%s' % (frs, exe, fout, ferr)

        with open(fcmd, 'w') as f:
            f.write('\n%s\n' % cmd)

        return cmd


# ------------------------------------------------------------------------------

