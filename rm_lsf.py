
import os
import socket

import multiprocessing as mp

from constants import FREE


# ------------------------------------------------------------------------------
class RM_LSF(object):

    # --------------------------------------------------------------------------
    #
    def __init__(self):

        # FIXME: configurable
        self._cpn   = 20
        self._gpn   =  4
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
            self._nodes.append([host, self._cpn, self._gpn])


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
            uid, cpn, gpn = self._nodes[i]
            nodes.append([str(uid), [FREE] * cpn, [FREE] * gpn])

        return nodes


# ------------------------------------------------------------------------------

