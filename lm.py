

# ------------------------------------------------------------------------------
#
class LM(object):

    @staticmethod
    def create(launcher, rm):

        from lm_fork      import LM_FORK
        from lm_jsrun_rs  import LM_JSRUN_RS
        from lm_jsrun_erf import LM_JSRUN_ERF
        from lm_orte      import LM_ORTE
        from lm_prrte     import LM_PRRTE

        lm = {'fork'     : LM_FORK,
              'jsrun_rs' : LM_JSRUN_RS,
              'jsrun_erf': LM_JSRUN_ERF,
              'prrte'    : LM_PRRTE,
              'orte'     : LM_ORTE}[launcher]

        return lm(rm)


# ------------------------------------------------------------------------------

