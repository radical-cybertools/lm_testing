
import os
import time

import subprocess as sp


# ------------------------------------------------------------------------------
class LM_PRRTE(object):

    # --------------------------------------------------------------------------
    #
    def __init__(self, rm):

        self._rm      = rm
        self._proc    = None
        self._dvm_uri = None

        pre  = os.environ['PRRTE_PREFIX']
        exe  = '%s/bin/prte --prefix %s' % (pre, pre)
        cmd  = '%s --report-uri prrte_dvm.uri 2>&1 >> prrte.log' % exe
        proc = sp.Popen(cmd.split(), stdout=sp.PIPE, stderr=sp.STDOUT)

        self._proc = proc

        for _ in range(100):

            try:    self._dvm_uri = open('prrte_dvm.uri', 'r').read().strip()
            except: pass

            if self._dvm_uri:
              # print 'dvm uri: %s' % self._dvm_uri
                break

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

        exe   = task['exe']
        tid   = task['uid']
        slots = task['slots']

        fout  = '%s/%s.out' % (pwd, tid)
        ferr  = '%s/%s.err' % (pwd, tid)

        hosts = list()
        for node_uid, cores, gpus in slots:

            for _ in cores: hosts.append(node_uid)
            for _ in gpus : hosts.append(node_uid)

        host_str = ','.join(hosts)
        np_flag  = '-np %s' % len(hosts)
        map_flag = '--bind-to none'

        cmd  = 'prun --hnp "%s" %s %s -host %s %s 1>%s 2>%s' \
             % (self._dvm_uri, np_flag, map_flag, host_str, exe, fout, ferr)

        return cmd


# ------------------------------------------------------------------------------

