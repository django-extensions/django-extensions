# -*- coding: utf-8 -*-
"""
Based entirely on Django's own ``setup.py``.
"""
import os
import sys
from distutils.command.install import INSTALL_SCHEMES
from distutils.command.install_data import install_data

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup  # NOQA

try:
    from setuptools.command.test import test as TestCommand

    class PyTest(TestCommand):
        user_options = [('pytest-args=', 'a', "Arguments to pass into py.test")]

        def initialize_options(self):
            TestCommand.initialize_options(self)
            self.pytest_args = 'tests django_extensions --ds=tests.testapp.settings --cov=django_extensions'

        def finalize_options(self):
            TestCommand.finalize_options(self)
            self.test_args = []
            self.test_suite = True

        def run_tests(self):
            import shlex
            import pytest
            errno = pytest.main(shlex.split(self.pytest_args))
            sys.exit(errno)
except ImportError:
    PyTest = None


class osx_install_data(install_data):
    # On MacOS, the platform-specific lib dir is at:
    #   /System/Library/Framework/Python/.../
    # which is wrong. Python 2.5 supplied with MacOS 10.5 has an Apple-specific
    # fix for this in distutils.command.install_data#306. It fixes install_lib
    # but not install_data, which is why we roll our own install_data class.

    def finalize_options(self):
        # By the time finalize_options is called, install.install_lib is set to
        # the fixed directory, so we set the installdir to install_lib. The
        # install_data class uses ('install_data', 'install_dir') instead.
        self.set_undefined_options('install', ('install_lib', 'install_dir'))
        install_data.finalize_options(self)


if sys.platform == "darwin":
    cmdclasses = {'install_data': osx_install_data}
else:
    cmdclasses = {'install_data': install_data}

if PyTest:
    cmdclasses['test'] = PyTest


def fullsplit(path, result=None):
    """
    Split a pathname into components (the opposite of os.path.join) in a
    platform-neutral way.
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)


# Tell distutils to put the data_files in platform-specific installation
# locations. See here for an explanation:
# http://groups.google.com/group/comp.lang.python/browse_thread/thread/35ec7b2fed36eaec/2105ee4d9e8042cb
for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']


# Compile the list of packages available, because distutils doesn't have
# an easy way to do this.
packages, package_data = [], {}

root_dir = os.path.dirname(__file__)
if root_dir != '':
    os.chdir(root_dir)
extensions_dir = 'django_extensions'

for dirpath, dirnames, filenames in os.walk(extensions_dir):
    # Ignore PEP 3147 cache dirs and those whose names start with '.'
    dirnames[:] = [d for d in dirnames if not d.startswith('.') and d != '__pycache__']
    parts = fullsplit(dirpath)
    package_name = '.'.join(parts)
    if '__init__.py' in filenames:
        packages.append(package_name)
    elif filenames:
        relative_path = []
        while '.'.join(parts) not in packages:
            relative_path.append(parts.pop())
        relative_path.reverse()
        path = os.path.join(*relative_path)
        package_files = package_data.setdefault('.'.join(parts), [])
        package_files.extend([os.path.join(path, f) for f in filenames])


version = __import__('django_extensions').__version__

setup(
    name='django-extensions',
    version=version,
    description="Extensions for Django",
    long_description="""django-extensions bundles several useful
additions for Django projects. See the project page for more information:
  http://github.com/django-extensions/django-extensions""",
    author='Michael Trier',
    author_email='mtrier@gmail.com',
    maintainer='Bas van Oostveen',
    maintainer_email='v.oostveen@gmail.com',
    url='http://github.com/django-extensions/django-extensions',
    license='MIT License',
    platforms=['any'],
    packages=packages,
    cmdclass=cmdclasses,
    package_data=package_data,
    install_requires=['six>=1.2'],
    tests_require=[
        'Django',
        'shortuuid',
        'python-dateutil',
        'pytest',
        'pytest-django',
        'pytest-cov',
        'tox',
        'mock',
        'vobject'
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9',
        'Framework :: Django :: 1.10',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Utilities',
    ],
)
