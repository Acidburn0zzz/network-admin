#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 Adriano Monteiro Marques
#
# Author: Piotrek Wasilewski <wasilewski.piotrek@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from netadmin.networks.models import Host, Network

try:
    import search
    from search.core import startswith

    search.register(Host, ('name', 'description', 'ipv4', 'ipv6'),
                    indexer=startswith)

    search.register(Network, ('name', 'description'),
                    indexer=startswith)
except ImportError:
    from haystack import indexes
    from haystack import site

    class HostIndex(indexes.SearchIndex):
        text = indexes.CharField(document=True, use_template=True)

        def index_queryset(self):
            return Host.objects.all()

    class NetworkIndex(indexes.SearchIndex):
        text = indexes.CharField(document=True, use_template=True)

        def index_queryset(self):
            return Network.objects.all()

    site.register(Network, NetworkIndex)
    site.register(Host, HostIndex)
    