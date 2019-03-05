

# ------------------------------------------------------------------------------
#
class LM(object):

    @staticmethod
    def create(launcher, nodes):

        from lm_fork  import LM_FORK
        from lm_jsrun import LM_JSRUN
        from lm_orte  import LM_ORTE
        from lm_prrte import LM_PRRTE

        lm = {'fork' : LM_FORK,
              'jsrun': LM_JSRUN,
              'prrte': LM_PRRTE,
              'orte' : LM_ORTE}[launcher]

        return lm(nodes)


# ------------------------------------------------------------------------------

