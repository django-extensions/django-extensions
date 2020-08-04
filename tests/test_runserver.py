# -*- coding: utf-8 -*-
import pytest

from os.path import join

from django_extensions.management.commands.runserver_plus import Command as RunServerCommand

from unittest import mock


location = join('some', 'strange', 'path')
different_path = join('some', 'other', 'path')


@pytest.mark.parametrize("cert_option, key_file_option, expected_cert_path, expected_key_path", [
    ['hello', None, join(location, 'hello.crt'), join(location, 'hello.key')],
    ['hello.crt', None, join(location, 'hello.crt'), join(location, 'hello.key')],
    [None, 'hello', join(location, 'hello.crt'), join(location, 'hello.key')],
    [None, 'hello.key', join(location, 'hello.crt'), join(location, 'hello.key')],
    ['first', 'second', join(location, 'first.crt'), join(location, 'second.key')],
    ['first.pem', 'second.pem', join(location, 'first.pem'), join(location, 'second.pem')],
    ['cert.pem', 'key.pem', join(location, 'cert.pem'), join(location, 'key.pem')],
    [join(location, 'hello'), None, join(location, 'hello.crt'), join(location, 'hello.key')],
    [None, join(location, 'hello'), join(location, 'hello.crt'), join(location, 'hello.key')],
    [join(location, 'hello'), join(location, 'hello'), join(location, 'hello.crt'), join(location, 'hello.key')],
    [join(location, 'hello.crt'), join(location, 'hello.key'), join(location, 'hello.crt'), join(location, 'hello.key')],
    [join(location, 'hello.key'), join(location, 'hello.crt'), join(location, 'hello.key'), join(location, 'hello.crt')],
    [join(location, 'cert.pem'), join(location, 'key.pem'), join(location, 'cert.pem'), join(location, 'key.pem')],
    [join(location, 'hello.crt'), join(location, 'hello.key'), join(location, 'hello.crt'),
     join(location, 'hello.key')],
    [join(location, 'other'), join(location, 'hello.key'), join(location, 'other.crt'),
     join(location, 'hello.key')],
    [join(location, 'hello.key'), join(location, 'hello.crt'), join(location, 'hello.key'),
     join(location, 'hello.crt')],
    [join(different_path, 'hello'), None, join(different_path, 'hello.crt'), join(different_path, 'hello.key')],
    [None, join(different_path, 'hello'), join(different_path, 'hello.crt'), join(different_path, 'hello.key')],
    [join(location, 'hello.crt'), join(different_path, 'hello.key'), join(location, 'hello.crt'), join(different_path, 'hello.key')],
    [join(different_path, 'hello.crt'), join(location, 'hello.key'), join(different_path, 'hello.crt'), join(location, 'hello.key')],
])
def test_determining_paths(cert_option, key_file_option, expected_cert_path, expected_key_path):
    with mock.patch('django_extensions.management.commands.runserver_plus.os.getcwd', return_value=location):
        options = {'cert_path': cert_option, 'key_file_path': key_file_option}
        result_cert_path, result_key_path = RunServerCommand.determine_ssl_files_paths(options)
        assert expected_cert_path == result_cert_path
        assert expected_key_path == result_key_path
