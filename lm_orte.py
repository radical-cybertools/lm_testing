
import os
import time

import subprocess as sp

from lm import LM


# ------------------------------------------------------------------------------
class LM_ORTE(LM):

    # --------------------------------------------------------------------------
    #
    def __init__(self, nodes):

        self._proc    = None
        self._dvm_uri = None

        flog   = 'orte.log'
        furi   = 'orte.uri'
        fhosts = 'orte.hosts'

        with open(fhosts, 'w') as fout:
            for node_uid, cores, gpus in nodes:
                fout.write('%s slots=%d\n' % (node_uid, len(cores)))

        cmd  = 'orte-dvm --report-uri %s --hostfile %s 2>&1 >> %s' \
               % (furi, fhosts, flog)

        with open('popen.log', 'a') as fout:
            fout.write('%s\n' % cmd)

        self._proc = sp.Popen(cmd.split(), stdout=sp.PIPE, stderr=sp.STDOUT)

        for _ in range(100):

            try:    self._dvm_uri = open(furi, 'r').read().strip()
            except: pass

            if self._dvm_uri:
                break

          # time.sleep(0.1)

        if not self._dvm_uri:
            raise RuntimeError('ORTE DVM did not come up')


    # --------------------------------------------------------------------------
    #
    def __del__(self):

        self.close()


    # --------------------------------------------------------------------------
    #
    def close(self):

        if self._proc:

            term = 'orterun --hnp %s --terminate' % self._dvm_uri

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
            os.unlink('orte_dvm.uri')

        except OSError:
            pass


    # --------------------------------------------------------------------------
    #
    def prepare_task(self, pwd, task):
        '''
        For the given task, prepare a orterun command line to execute that task.
        '''

        tid   = task['uid']
        exe   = task['exe']
        args  = task['args']
        slots = task['slots']

        fout  = '%s/%s.out' % (pwd, tid)
        ferr  = '%s/%s.err' % (pwd, tid)

        hosts = list()

        for node_uid, node_name, cores, gpus in slots:

            for _ in cores: hosts.append(node_uid)
            for _ in gpus : hosts.append(node_uid)

        host_str = ','.join(hosts)
        np_flag  = '-np %s' % len(hosts)
        map_flag = '--bind-to none'

        task['cmd'] = 'orterun --hnp "%s" %s %s -host %s %s %s 1>%s 2>%s' \
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
      # time.sleep(0.1)
        pass


# ------------------------------------------------------------------------------

