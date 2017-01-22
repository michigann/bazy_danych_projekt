#!/usr/bin/python
import os
import sys
lib_path = os.path.abspath(os.path.join('..','..','Bazy','projekt'))
sys.path.append(lib_path)

from wsgiref.handlers import CGIHandler
from main import app

CGIHandler().run(app)
