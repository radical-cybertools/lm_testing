
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

        from rm_fork      import RM_FORK
        from rm_lfs       import RM_LFS

        rm = {'fork'     : RM_FORK,
              'jsrun_rs' : RM_LFS
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

