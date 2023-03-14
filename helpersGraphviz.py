import sublime, sublime_plugin
import subprocess
import os
import platform
import re
import tempfile
import base64

ENVIRON = os.environ
if platform.system() != 'Windows':
    ENVIRON['PATH'] += ':/usr/local/bin'

def surroundingGraphviz(data, cursor):
    '''
    Find graphviz code in source surrounding the cursor.
    '''
    data_before = data[0:cursor]
    data_after = data[cursor:]

    # find code before selector
    index = data_before.rfind("@dot")
    if index == -1:
        return ""
    full_code_before = data_before[index:]

    # there might be options after @dot, need to ignore all of those
    index = full_code_before.find("\n")
    if index == -1:
        return ""
    code_before = full_code_before[index:]

    # find code after selector
    index = data_after.find("@enddot")
    if index == -1:
        return ""
    code_after = data_after[0:index]

    # done!
    return code_before + code_after

def graphvizImage(code):
    '''
    Convert graphviz code to a PNG.
    '''
    viz_filename = tempfile.gettempdir() + os.sep + 'sublime_text_graphviz_preview.viz'
    if os.path.isfile(viz_filename):
        os.unlink(viz_filename)
    grapviz = open(viz_filename, mode='wb')
    grapviz.write(code.encode('utf-8'))
    grapviz.close()

    settings = sublime.load_settings('DiagramPreview.sublime-settings')
    dot_path = settings.get('dot_path', 'C:\\Program Files\\Graphviz\\bin\\dot.exe')
    dot_font = settings.get('dot_font', 'Consolas')

    #print(dot_font)
    cmd = [dot_path, '-Tpng',
           '-Nfontname="' + dot_font + '"',
           '-Ncharset="UTF-8"',
           '-Efontname="' + dot_font + '"',
           '-Echarset="UTF-8"',
           '-Gfontname="' + dot_font + '"',
           '-Gcharset="UTF-8"', grapviz.name]
    startupinfo = None
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    # Default cwd is Sublime Text installation directory, such as `D:\Sublime Text`
    # We change it to the directory the same as dot file. See issue #16.
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    startupinfo=startupinfo)
    try:
        stdout, stderr = process.communicate(timeout=2)
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()
    return base64.b64encode(stdout)
