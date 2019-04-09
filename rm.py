

# ------------------------------------------------------------------------------
#
# Resource Manager base class
#
class RM(object):

    @staticmethod
    def create(rmgr):

        from rm_fork import RM_FORK
        from rm_lsf  import RM_LSF

        rm = {'fork' : RM_FORK,
              'lsf'  : RM_LSF
             }[rmgr]

        return rm()


# ------------------------------------------------------------------------------

