from os.path import join as _j
from os.path import dirname, abspath, isfile
import inspect
import os

def get_project_root():
    """ get the project root directory """
    f = inspect.currentframe()
    o = inspect.getouterframes(f)
    fn = o[-1][0].f_code.co_filename
    root = dirname(abspath(fn))
    assert isfile(_j(root, "settings.py")), "Could not find project root directory"
    return root
