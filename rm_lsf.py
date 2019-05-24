
import os
import socket

import multiprocessing as mp

from rm        import RM
from constants import FREE


# ------------------------------------------------------------------------------
#
class RM_LSF(RM):

    # --------------------------------------------------------------------------
    #
    def __init__(self, tgt, cfg):

        self._nnodes   = 1  # TODO: make configurable for debug purposes
        self._hostname = socket.gethostname()

        self._tgt = tgt
        self._cfg = cfg

        self._cpn = self._cfg['cpn']
        self._gpn = self._cfg['gpn']

        self._nodes = list()
        
        # filter batch node (localhost) from the node list
        localhost = socket.gethostname().split('.')[0]

        hosts = set()
        with open(os.environ['LSB_DJOB_HOSTFILE'], 'r') as fin:
            for line in fin.readlines():
                host = line.strip()
                if host != localhost:
                    hosts.add(host)

        for host in hosts:
            self._nodes.append([host, host, self._cpn, self._gpn])


    # --------------------------------------------------------------------------
    #
    def get_nodes(self, tc):
        '''
        return a copy of the first n nodes from the available nodes
        '''

        nnodes = tc['nodes']
        nodes  = list()

        if nnodes > len(self._nodes):
            raise ValueError('insufficient nodes: %d > %d'
                            % (nnodes, len(self._nodes)))

        for i in range(nnodes):
            uid, node, cpn, gpn = self._nodes[i]
            nodes.append([uid, node, [FREE] * cpn, [FREE] * gpn])

        return nodes


# ------------------------------------------------------------------------------

