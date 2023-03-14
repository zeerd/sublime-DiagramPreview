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

def surroundingPlantuml(data, cursor, kind):
    '''
    Find graphviz code in source surrounding the cursor.
    '''
    data_before = data[0:cursor]
    data_after = data[cursor:]

    start = "@start" + kind
    end = "@end" + kind

    # find code before selector
    index = data_before.rfind(start)
    if index == -1:
        return ""
    full_code_before = data_before[index:]

    # there might be options after @startuml, need to ignore all of those
    index = full_code_before.find("\n")
    if index == -1:
        return ""
    code_before = start + '\n' + full_code_before[index:]

    # find code after selector
    index = data_after.find(end) + 7
    if index == -1:
        return ""
    code_after = data_after[0:index]

    # done!
    return code_before + code_after

def plantumlImage(code):
    '''
    Convert graphviz code to a PNG.
    '''
    viz_filename = tempfile.gettempdir() + os.sep + 'sublime_text_plantuml_preview'
    if os.path.isfile(viz_filename+".puml"):
        os.unlink(viz_filename+".puml")
    if os.path.isfile(viz_filename+".png"):
        os.unlink(viz_filename+".png")
    plantum = open(viz_filename+".puml", mode='wb')
    plantum.write(code.encode('utf-8'))
    plantum.close()

    settings = sublime.load_settings('DiagramPreview.sublime-settings')
    java_path = settings.get('java_path', 'C:\\Program Files\\Java\\jre1.8.0_301\\bin\\java.exe')
    plantuml_path = settings.get('plantuml_path', 'D:/tools/Utils/plantuml-1.2022.5.jar')

    #print(java_path)
    cmd = [java_path,
           '-Djava.awt.headless=true',
           '-Dfile.encoding=UTF-8',
           '-jar', plantuml_path,
           '-charset', 'UTF-8',
           #'-I' + 'D:\\tools\\Utils\\plantuml.cfg',
           '-tpng',
           '-overwrite',
           plantum.name]
    startupinfo = None
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    startupinfo=startupinfo)
    try:
        stdout, stderr = process.communicate(timeout=15)
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()

    #if stderr:
    #    print(code)
    #    print(bytes.decode(stderr))

    b64_string = ""
    if not stderr and os.path.isfile(viz_filename+".png"):
        with open(viz_filename+".png", "rb") as img_file:
           b64_string = base64.b64encode(img_file.read())

    if os.path.isfile(viz_filename+".puml"):
        os.unlink(viz_filename+".puml")
    if os.path.isfile(viz_filename+".png"):
        os.unlink(viz_filename+".png")

    return b64_string
