# -*- coding: utf-8 -*-
from collections.abc import Container
import ipaddress
import itertools


class InternalIPS(Container):
    """
    InternalIPS allows to specify CIDRs for INTERNAL_IPS.

    It takes an iterable of ip addresses or ranges.

    Inspiration taken from netaddr.IPSet, please use it if you can since
    it support more advanced features like optimizing ranges and lookups.
    """

    __slots__ = ["_cidrs"]

    def __init__(self, iterable, sort_by_size=False):
        """
        Constructor.

        :param iterable: (optional) an iterable containing IP addresses and
            subnets.

        :param sort_by_size: sorts internal list according to size of ip
            ranges, largest first.
        """
        self._cidrs = []
        for address in iterable:
            self._cidrs.append(ipaddress.ip_network(address))

        if sort_by_size:
            self._cidrs = sorted(self._cidrs)

    def __contains__(self, address):
        """
        :param ip: An IP address or subnet.

        :return: ``True`` if IP address or subnet is a member of this InternalIPS set.
        """
        address = ipaddress.ip_address(address)
        for cidr in self._cidrs:
            if address in cidr:
                return True
        return False

    def __hash__(self):
        """
        Raises ``TypeError`` if this method is called.
        """
        raise TypeError('InternalIPS containers are unhashable!')

    def __len__(self):
        """
        :return: the cardinality of this InternalIPS set.
        """
        return sum(cidr.num_addresses for cidr in self._cidrs)

    def __iter__(self):
        """
        :return: an iterator over the IP addresses within this IP set.
        """
        return itertools.chain(*self._cidrs)

    def iter_cidrs(self):
        """
        :return: an iterator over individual IP subnets within this IP set.
        """
        return sorted(self._cidrs)
