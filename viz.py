
import sys
import time


try:
    from asciimatics.effects    import Print
    from asciimatics.renderers  import DynamicRenderer
    from asciimatics.scene      import Scene
    from asciimatics.screen     import Screen
    use_curses = True
except ImportError:
    use_curses = False


from constants import FREE, BUSY
from constants import NEW, WAITING, SCHEDULED, RUNNING, DONE, FAILED, MISPLACED


if use_curses:

    # ------------------------------------------------------------------------------
    #
    class TextBox(DynamicRenderer):

        # --------------------------------------------------------------------------
        #
        def __init__(self, msg):

            self.height =   3
            self.width  = 100
            self._msg   = msg

            super(TextBox, self).__init__(self.height, self.width)


        # --------------------------------------------------------------------------
        #
        def set(self, msg):

            self._msg = msg


        # --------------------------------------------------------------------------
        #
        def _render_now(self):

            self._clear()

            col = (Screen.COLOUR_RED, 0)

            for i, char in enumerate(self._msg):
                self._write(char, i, 0, col[0], col[1], 0)

            return self._plain_image, self._colour_map


    # ------------------------------------------------------------------------------
    #
    class NodeChart(DynamicRenderer):

        _cpu_glyphs = {FREE : [FREE, (Screen.COLOUR_RED,    0)],
                       BUSY : [BUSY, (Screen.COLOUR_GREEN,  0)]}

        _gpu_glyphs = {FREE : [FREE, (Screen.COLOUR_RED,    0)],
                       BUSY : [BUSY, (Screen.COLOUR_GREEN,  0)]}


        # --------------------------------------------------------------------------
        #
        def __init__(self, nodes, cpn, gpn):

            self.nodes  = nodes
            self.cpn    = cpn
            self.gpn    = gpn

            self.height =  len(self.nodes) + 2
            self.width  =  self.cpn + self.gpn + 3

            super(NodeChart, self).__init__(self.height, self.width)


        # --------------------------------------------------------------------------
        #
        def _render_now(self):

            self._clear()
            for n,node in enumerate(self.nodes):

                for i,c in enumerate(node[1]):
                    glyph  = self._cpu_glyphs[c]
                    char   = glyph[0]
                    col    = glyph[1]
                    self._write(char, i, n, col[0], col[1], 0)

                for i,g in enumerate(node[2]):
                    glyph  = self._gpu_glyphs[g]
                    char   = glyph[0]
                    col    = glyph[1]
                    self._write(char, self.cpn + i + 1, n, col[0], col[1], 0)

            return self._plain_image, self._colour_map


    # ------------------------------------------------------------------------------
    #
    class TaskChart(DynamicRenderer):

        _task_glyphs = {NEW       : [NEW      , (Screen.COLOUR_RED,    0)],
                        WAITING   : [WAITING  , (Screen.COLOUR_GREEN,  0)],
                        SCHEDULED : [SCHEDULED, (Screen.COLOUR_GREEN,  0)],
                        RUNNING   : [RUNNING  , (Screen.COLOUR_GREEN,  0)],
                        DONE      : [DONE     , (Screen.COLOUR_GREEN,  0)],
                        FAILED    : [FAILED   , (Screen.COLOUR_GREEN,  0)],
                        MISPLACED : [MISPLACED, (Screen.COLOUR_GREEN,  0)]}


        # --------------------------------------------------------------------------
        #
        def __init__(self, tasks, chunk=1024):

            self.tasks  = tasks
            self.chunk  = chunk

            self.width  = self.chunk + 1
            self.height = len(self.tasks) // self.chunk + 1

            print self.width
            print self.height

            super(TaskChart, self).__init__(self.height, self.width)


        # --------------------------------------------------------------------------
        #
        def _render_now(self):

            self._clear()
            for n,task in enumerate(self.tasks):

                x = n %  self.chunk
                y = n // self.chunk

                glyph  = self._task_glyphs[task['state']]
                char   = glyph[0]
                col    = glyph[1]
                self._write(char, x, y, col[0], col[1], 0)

            return self._plain_image, self._colour_map


# ------------------------------------------------------------------------------
#
class VIZ(object):

    # --------------------------------------------------------------------------
    #
    @staticmethod
    def create(viztype, nodes, cpn, gpn, tasks, chunk=128):

        if viztype == 'curses' and not use_curses:
            sys.stdout.write('non asciimatics, fall back to simple viz\n')
            sys.stdout.flush()
            time.sleep(1)
            viztype = 'text'

        viz = {'curses': VizCurses,
               'simple': VizSimple,
               'text'  : VizText,
               'mute'  : VizMute}[viztype]

        return viz(nodes, cpn, gpn, tasks, chunk)


# ------------------------------------------------------------------------------
#
class VizCurses(object):

    if not use_curses:
        pass

    else:
        # ----------------------------------------------------------------------
        #
        def __init__(self, nodes, cpn, gpn, tasks, chunk=128):
    
            self._screen = Screen.open()
            self._msg    = 'FOO'
    
            try:
                self._header  = TextBox(msg=self._msg)
                self._nodes   = NodeChart(nodes=nodes, cpn=cpn, gpn=gpn)
                self._tasks   = TaskChart(tasks=tasks, chunk=chunk)
                effects = [Print(self._screen, self._header, x=1, y=1),
                           Print(self._screen, self._nodes,  x=1, y=4),
                           Print(self._screen, self._tasks,  x=1, y=3
                                                        + self._nodes.height)]
    
                self._scenes = [Scene(effects, -1)]
                self._screen.set_scenes(self._scenes)
    
            except Exception:
                self._screen.close()
                self._screen = None
                raise
    
    
        # ----------------------------------------------------------------------
        #
        def header(self, msg):
    
            self._header.set(msg)
    
    
        # ----------------------------------------------------------------------
        #
        def text(self, msg):
    
            pass
    
    
        # ----------------------------------------------------------------------
        #
        def update(self):
    
            if not self._screen:
                return False
    
          # try:
            if True:
                self._screen.draw_next_frame(repeat=False) 
    
                event = self._screen.get_event()
                while event:
                    for scene in self._scenes:
                        if not event:
                            break
                        event = scene.handle_event(event)
                    event = self._screen.get_event()
                # screen.wait_for_input(1.0)
    
                return True
    
          # except Exception:
          #     self._screen.close()
          #     self._screen = None
          #     return False
    
    
        # ----------------------------------------------------------------------
        #
        def close(self):
    
            if self._screen:
                time.sleep(1)
                self._screen.close()
                self._screen = None


# ------------------------------------------------------------------------------
#
class VizSimple(object):

    # --------------------------------------------------------------------------
    #
    def __init__(self, nodes, cpn, gpn, tasks, chunk=128):

        self._nodes = nodes
        self._tasks = tasks

        self._cpn   = cpn
        self._gpn   = gpn
        self._chunk = chunk

        self._header_out = ''
        self._text_out   = ''
        self._nodes_out  = ''
        self._tasks_out  = ''


    # --------------------------------------------------------------------------
    #
    def header(self, msg):

        self._header_out  = '\n----------------------------------------------\n'
        self._header_out += msg
        self._header_out += '\n\n'


    # --------------------------------------------------------------------------
    #
    def text(self, msg):

        if not msg:
            self._text_out = ''
        else:
            self._text_out += msg
            self._text_out += '\n'


    # --------------------------------------------------------------------------
    #
    def update(self):

        nodes_flag = self._dump_nodes()
        tasks_flag = self._dump_tasks()

        if nodes_flag or tasks_flag:
          # os.system('clear')
            print self._header_out
            print self._text_out
            print self._nodes_out
            print self._tasks_out
            print


    # ------------------------------------------------------------------------------
    #
    def _dump_nodes(self):
        '''
        Dump a human-parseable representation of the node state
        '''

        data = ''
        for node in self._nodes:
            c_str = ''.join([c for c in node[1]])
            g_str = ''.join([g for g in node[2]])
            data += '%-3s : %s : %s\n' % (node[0], c_str, g_str)

        if data != self._nodes_out:
            self._nodes_out = data
            return True

        return False


    # ------------------------------------------------------------------------------
    #
    def _dump_tasks(self):
        '''
        Dump a human-parseable representation of the task states
        '''

        i    = 0
        data = ''
        for task in self._tasks:
            if not i % self._chunk:
                data += '\n'
            data += task['state']
            i    += 1

        if data != self._tasks_out:
            self._tasks_out = data
            return True

        return False


    # --------------------------------------------------------------------------
    #
    def close(self):

        print


# ------------------------------------------------------------------------------
#
class VizText(object):

    # --------------------------------------------------------------------------
    #
    def __init__(self, nodes, cpn, gpn, tasks, chunk=128):

        self._nodes = nodes
        self._tasks = tasks

        self._cpn   = cpn
        self._gpn   = gpn
        self._chunk = chunk

        self._old_data = ''
        self._iter     = 0

        self._header = ' ||  cores |   busy |   free ||   gpus |   busy |   free |' \
                     + '|  tasks |    new |   wait |  sched |    run |   done |   fail | xplace ||' 


    # --------------------------------------------------------------------------
    #
    def header(self, msg):

        print
        print ' ----------------------------------------------------------------'
        print ' %s' % msg


    # --------------------------------------------------------------------------
    #
    def text(self, msg):

        if msg:
            print '     %s' % msg


    # --------------------------------------------------------------------------
    #
    def update(self):

        if not self._iter % 51:
            print
            print self._header
            self._iter += 1

        c_total = 0
        c_busy  = 0
        c_free  = 0

        g_total = 0
        g_busy  = 0
        g_free  = 0

        for node in self._nodes:

            c_total += len(node[1])
            c_busy  += node[1].count(BUSY)
            c_free  += node[1].count(FREE)

            g_total += len(node[2])
            g_busy  += node[2].count(BUSY)
            g_free  += node[2].count(FREE)

        t_total     = len(self._tasks)
        t_new       = len([1 for t in self._tasks if t['state'] == NEW])
        t_waiting   = len([1 for t in self._tasks if t['state'] == WAITING])
        t_scheduled = len([1 for t in self._tasks if t['state'] == SCHEDULED])
        t_running   = len([1 for t in self._tasks if t['state'] == RUNNING])
        t_done      = len([1 for t in self._tasks if t['state'] == DONE])
        t_failed    = len([1 for t in self._tasks if t['state'] == FAILED])
        t_misplaced = len([1 for t in self._tasks if t['state'] == MISPLACED])

        data  = ' || %6d | %6d | %6d || %6d | %6d | %6d |' \
            % (c_total, c_busy, c_free, g_total, g_busy, g_free)

        data += '| %6d | %6d | %6d | %6d | %6d | %6d | %6d | %6d ||' \
              % (t_total, t_new, t_waiting, t_scheduled,
                 t_running ,t_done, t_failed, t_misplaced)

        if data != self._old_data:
            print data
            self._old_data = data
            self._iter += 1


    # --------------------------------------------------------------------------
    #
    def close(self):

        print


# ------------------------------------------------------------------------------
#
class VizMute(object):

    # --------------------------------------------------------------------------
    #
    def __init__(self, nodes, cpn, gpn, tasks, chunk=128): pass
    def header(self, msg): pass
    def update(self)     : pass
    def close(self)      : pass


# ------------------------------------------------------------------------------

