# -*- coding: utf-8 -*-
import os


def run(*args):
    print('Script called from: %s' % os.getcwd())
    os.chdir(os.path.dirname(os.getcwd()))  # to test is NONE option freezing start directory
