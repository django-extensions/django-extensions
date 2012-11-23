#!/usr/bin/env python
#-*- coding:utf-8 -*-

from django.template import Library, Node, TemplateSyntaxError


register = Library()


class SplitListNode(Node):

    def __init__(self, list_string, chunk_size, new_list_name):
        self.list = list_string
        self.chunk_size = chunk_size
        self.new_list_name = new_list_name

    def split_seq(self, seq, size):
        """ Split up seq in pieces of size, from
        http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/425044"""
        return [seq[i:i+size] for i in range(0, len(seq), size)]

    def render(self, context):
        context[self.new_list_name] = \
            self.split_seq(context[self.list], int(self.chunk_size))
        return ''


def split_list(parser, token):
    """<% split_list list as new_list 5 %>"""
    bits = token.contents.split()
    if len(bits) != 5:
        raise TemplateSyntaxError("split_list list as new_list 5")
    return SplitListNode(bits[1], bits[4], bits[3])


split_list = register.tag(split_list)
