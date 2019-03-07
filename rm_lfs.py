
import os
import socket

import multiprocessing as mp

from constants import FREE


# ------------------------------------------------------------------------------
class RM_LFS(object):

    # --------------------------------------------------------------------------
    #
    def __init__(self):

        self._nnodes   = 1  # TODO: make configurable for debug purposes
        self._hostname = socket.gethostname()
        self._cpn      = mp.cpu_count()
        self._gpn      = int(os.popen('lspci | grep " VGA " | wc -l').read())

        self._nodes = list()
        for ni in range(self._nnodes):
            self._nodes.append(['node_%04d' % ni, self._cpn, self._gpn])


    # --------------------------------------------------------------------------
    #
    def get_nodes(self, tc):
        '''
        return a copy of the first n nodes from the available nodes
        '''

        nnodes = tc['nodes']
        nodes  = list()

        if nnodes > self._nnodes:
            raise ValueError('insufficient nodes: %d > %d'
                            % (nnodes, self._nnodes))

        for i in range(nnodes):
            uid, cpn, gpn = self._nodes[i]
            nodes.append([str(uid), [FREE] * cpn, [FREE] * gpn])

        return nodes


# ------------------------------------------------------------------------------

