# coding=utf-8
import six


def null_technical_500_response(request, exc_type, exc_value, tb, status_code=500):
    six.reraise(exc_type, exc_value, tb)
