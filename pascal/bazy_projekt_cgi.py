#!/usr/bin/python
import os
import sys
import cgitb
from wsgiref.handlers import CGIHandler

lib_path = os.path.abspath(os.path.join('..', '..', 'Bazy', 'projekt'))
sys.path.append(lib_path)
cgitb.enable()

from main import my_app as app


class ScriptNameStripper(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        environ['SCRIPT_NAME'] = '/~4kuklewski/flyhigh'
        environ['SERVER_NAME'] = 'pascal.fis.agh.edu.pl'
        environ['SERVER_PORT'] = '80'
        environ['REQUEST_METHOD'] = os.environ['REQUEST_METHOD']
        return self.app(environ, start_response)


app = ScriptNameStripper(app)
CGIHandler().run(app)
