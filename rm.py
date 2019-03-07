

# ------------------------------------------------------------------------------
#
# Resource Manager base class
#
class RM(object):

    @staticmethod
    def create(rmgr):

        from rm_fork      import RM_FORK
        from rm_lfs       import RM_LFS

        rm = {'fork'     : RM_FORK,
              'jsrun_rs' : RM_LFS
             }[rmgr]

        return rm()


# ------------------------------------------------------------------------------

