
import os
import time
import tempfile

import subprocess as sp

from lm import LM


# ------------------------------------------------------------------------------
class LM_PRRTE(LM):

    # --------------------------------------------------------------------------
    #
    def __init__(self, nodes):

        self._proc    = None
        self._dvm_uri = None

        flog   = 'prrte.log'
        furi   = '/tmp/prrte.uri'
        fhosts = '/tmp/prrte.hosts'

        with open(fhosts, 'w') as fout:
            for node_uid, node_name, cores, gpus in nodes:
                fout.write('%s slots=%d\n' % (node_name, len(cores)))

        pre   = os.environ['PRRTE_DIR']
        prte  = '%s/bin/prte'      % pre
        prte += ' --prefix %s'     % pre
        prte += ' --report-uri %s' % furi
        prte += ' --hostfile %s'   % fhosts
      # prte += ' --mca plm_rsh_no_tree_spawn 1'

        with open('popen.log', 'a') as fout:
            fout.write('%s\n' % prte)

        fout = open(flog, 'w')

        self._proc = sp.Popen(prte.split(), stdout=fout, stderr=sp.STDOUT)

        for _ in range(100):

            try:
                with open(furi, 'r') as fin:
                    for line in fin.readlines():
                        if '://' in line:
                            self._dvm_uri = line.strip()
                            break
                        else:
                            print '>> %s' % line
            except:
                pass

            time.sleep(0.1)

        if not self._dvm_uri:
            raise RuntimeError('PRTE DVM did not come up')


    # --------------------------------------------------------------------------
    #
    def __del__(self):

        self.close()


    # --------------------------------------------------------------------------
    #
    def close(self):

        if self._proc:

            term = 'prun --hnp %s --terminate' % self._dvm_uri

            with open('popen.log', 'a') as fout:
                fout.write('%s\n' % term)

            proc = sp.Popen(term, stdout=sp.PIPE, stderr=sp.STDOUT, shell=True)
            proc.wait()

            try:
                self._proc.terminate()
            except:
                pass

            self._proc = None

        try:
            os.unlink('prrte_dvm.uri')

        except OSError:
            pass


    # --------------------------------------------------------------------------
    #
    def prepare_task(self, pwd, task):
        '''
        For the given task, prepare a prun command line to execute that task
        '''

        tid   = task['uid']
        exe   = task['exe']
        args  = task['args']
        slots = task['slots']

        fout  = '%s/%s.out' % (pwd, tid)
        ferr  = '%s/%s.err' % (pwd, tid)

        hosts = list()

        for node_uid, node_name, cores, gpus in slots:

            hosts.append(node_name)
          # for _ in cores: hosts.append(node_name)
          # for _ in gpus : hosts.append(node_name)

        host_str  = ','.join(hosts)
        np_flag   = '-np %s' % len(hosts)
        map_flag  = '--report-bindings'
        map_flag += ' --bind-to hwthread:overload-allowed'
     #  map_flag += ' --map-by hwthread:PE=%d' % len(slots[0][2])

        task['cmd'] = 'prun --hnp "%s" %s %s -host %s %s %s 1>%s 2>%s' \
            % (self._dvm_uri, np_flag, map_flag, host_str, exe, args, fout, ferr)

        self.dump_task(task)

        return task['cmd']


    # --------------------------------------------------------------------------
    #
    def finalize_task(self, pwd, task):
        '''
        cleanup after the given task completed
        '''

        # avoid overloading of the DVM
        time.sleep(0.100)


# ------------------------------------------------------------------------------

