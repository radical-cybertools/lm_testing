

# ------------------------------------------------------------------------------
class LM_JSRUN(object):

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

        tid    = task['uid']
        exe    = task['exe']
        slots  = task['slots']

        fout   = '%s/%s.out' % (pwd, tid)
        ferr   = '%s/%s.err' % (pwd, tid)
        frs    = '%s/%s.rs'  % (pwd, tid)

        rs_str = ''
        rs_id  = 0
        for node_uid, cores, gpus in slots:

            rs_str += 'RS %d: {'  % rs_id
            rs_str += ' host: %s' % node_uid
            if cores: rs_str += ' cpu: %s'  % ' '.join([str(c) for c in cores])
            if gpus : rs_str += ' gpu: %s'  % ' '.join([str(g) for g in gpus])
            rs_str += ' }\n'
            rs_id  += 1

        with open(frs, 'w') as f:
            f.write('\n%s\n' % rs_str)

        cmd = 'jsrun -a 1 %s %s 1>%s 2>%s' % (frs, exe, fout, ferr)

        return cmd


# ------------------------------------------------------------------------------

