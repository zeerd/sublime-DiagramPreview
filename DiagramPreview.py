import sublime, sublime_plugin
import os
import platform
import base64
import threading
import time
from subprocess import call
from .helpersGraphviz import surroundingGraphviz, graphvizImage, ENVIRON
from .helpersPlantuml import surroundingPlantuml, plantumlImage, ENVIRON

class DiagramPreviewCommand(sublime_plugin.TextCommand):

    def image_progress(self):
        index = 0
        while self.view.get_status('drawingImage') != "":
            bar = "-"*index + "=" + "-"*(4-index)
            index = index + 1
            if index == 5:
                index = 0
            self.view.set_status('drawingImage', 'drawing Diagram<' + bar + '>')
            time.sleep(0.5)

    def image_thread(self, graphviz, pure_code):

        self.view.set_status('drawingImage', 'drawing Diagram')
        image_progress = threading.Thread(target=self.image_progress, daemon=True)
        image_progress.start()

        if graphviz:
            b64_string = graphvizImage(pure_code)
        else:
            b64_string = plantumlImage(pure_code)

        #print('b64:' + b64_string)
        if len(b64_string) != 0:
            # https://stackoverflow.com/a/39568773
            self.view.show_popup('<img src="data:image/gif;base64,'
                                 +bytes.decode(b64_string)+'">',
                                  max_width=800, max_height=600)
        else:
            sublime.message_dialog("Image has not been rendered!")

        self.view.erase_status('drawingImage')

    def run(self, view):
        sel = self.view.sel()[0]

        data = self.view.substr(sublime.Region(0, self.view.size()))
        cursor = sel.begin()

        data_before = data[0:cursor]
        data_after = data[cursor:]

        kind = 'uml'
        indexUml = data_before.rfind("@startuml")
        if indexUml == -1:
            indexUml = data_before.rfind("\\startuml")
        # indexUml = data_before.rfind("@startwbs")
        # if indexUml == -1:
        #     indexUml = data_before.rfind("\\startwbs")
        #     kind = 'wbs'

        indexDot = data_before.rfind("@dot")
        if indexDot == -1:
            indexDot = data_before.rfind("\\dot")

        if indexUml > indexDot:
            code = surroundingPlantuml(data, cursor, kind)
            graphviz = False
        else:
            graphviz = True
            code = surroundingGraphviz(data, cursor)

        if not code:
            sublime.message_dialog('Please place cursor in graphviz or plantuml code before running')
            return

        # I think there must be some cooler way to do this.
        # But I am really not know python too much.
        codes = code.split('\n')
        pure_code = ""
        for line in codes:
            pline = line.strip();
            prefix = pline.split(' ', 1) # remove '*' or '//' in doxygen block
            if prefix[0][0:1] == "*" or prefix[0][0:2] == '//':
                if len(prefix) == 2:
                    pline = prefix[1]
                else:
                    pline = ''
            pure_code = pure_code + pline + '\n'

        print(pure_code)
        image_thread = threading.Thread(target=self.image_thread,
                                        daemon=True, args=(graphviz, pure_code))
        image_thread.start()
