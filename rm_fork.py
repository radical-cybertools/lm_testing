
import os
import socket

import multiprocessing as mp

from rm        import RM
from constants import FREE


# ------------------------------------------------------------------------------
#
class RM_FORK(RM):

    # --------------------------------------------------------------------------
    #
    def __init__(self, tgt, cfg):

        self._nnodes   = 1  # TODO: make configurable for debug purposes
        self._hostname = socket.gethostname()

        self._tgt = tgt
        self._cfg = cfg

        self._cpn = self._cfg.get('cpn')
        self._gpn = self._cfg.get('gpn')

        if not self._cpn:
            self._cpn = mp.cpu_count()

        if not self._gpn:
            self._gpn = int(os.popen('lspci | grep " VGA " | wc -l').read())

        self._nodes = list()
        for ni in range(self._nnodes):
            self._nodes.append(['node_%04d' % ni, self._cpn, self._gpn])


    # --------------------------------------------------------------------------
    #
    def get_nodes(self, tc):
        '''
        return a copy of the first n nodes from the available nodes
        '''

        nnodes   = tc['nodes']
        nodes    = list()
        hostname = os.popen('hostname').read().strip()

        if nnodes > self._nnodes:
            raise ValueError('insufficient nodes: %d > %d'
                            % (nnodes, self._nnodes))

        for i in range(nnodes):
            uid, cpn, gpn = self._nodes[i]
            nodes.append([uid, hostname, [FREE] * cpn, [FREE] * gpn])

        return nodes


# ------------------------------------------------------------------------------

