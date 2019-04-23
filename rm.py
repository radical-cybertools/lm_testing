
import json


# ------------------------------------------------------------------------------
#
# Resource Manager base class
#
class RM(object):


    # --------------------------------------------------------------------------
    #
    @staticmethod
    def create(rmgr, tgt):

        from rm_fork import RM_FORK
        from rm_lsf  import RM_LSF

        rm = {'fork' : RM_FORK,
              'lsf'  : RM_LSF
             }[rmgr]

        with open('tgt_%s.cfg' % tgt, 'r') as fin:
            cfg = json.load(fin)

        return rm(tgt, cfg)


    # --------------------------------------------------------------------------
    #
    @property
    def cpn(self):
        return self._cpn


    # --------------------------------------------------------------------------
    #
    @property
    def gpn(self):
        return self._gpn


# ------------------------------------------------------------------------------

