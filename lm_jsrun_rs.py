
import os 

from lm import LM


# ------------------------------------------------------------------------------
#
class LM_JSRUN_RS(LM):

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

        pwd = os.path.abspath(pwd)

        tid    = task['uid']
        exe    = task['exe']
        args   = task['args']
        slots  = task['slots']

        fout   = '%s/%s.out' % (pwd, tid)
        ferr   = '%s/%s.err' % (pwd, tid)
        fcmd   = '%s/%s.cmd' % (pwd, tid)
        frs    = '%s/%s.rs'  % (pwd, tid)

        rs_id  = 0
        rs_str = ''

        for node_uid, node_name, cores, gpus in slots:

            rs_str += 'RS %d: {'  % rs_id
            rs_str += ' host: %d' % (int(node_uid) + 1)
            if cores: rs_str += ' cpu: %s'  % ' '.join([str(c) for c in cores])
            if gpus : rs_str += ' gpu: %s'  % ' '.join([str(g) for g in gpus])
            rs_str += ' }\n'
            rs_id  += 1

        with open(frs, 'w') as f:
            f.write('\n%s\n' % rs_str)

        task['cmd'] = 'jsrun -a 1 -U %s %s %s 1>%s 2>%s' \
                    % (frs, exe, args, fout, ferr)

        with open(fcmd, 'w') as f:
            f.write('\n%s\n' % task['cmd'])

        self.dump_task(task)

        return task['cmd']


# ------------------------------------------------------------------------------

