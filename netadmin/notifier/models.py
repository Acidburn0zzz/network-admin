#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2012 Adriano Monteiro Marques
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

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import models


class Notification(models.Model):
    """Represents notification that has to be sent as soon as possible
    """
    title = models.CharField(max_length=255)
    content = models.TextField()
    user = models.ForeignKey(User)
    related_type = models.ForeignKey(ContentType, null=True, blank=True)
    related_id = models.PositiveIntegerField(null=True, blank=True)
    
    related_object = generic.GenericForeignKey('related_type', 'related_id')

    def __unicode__(self):
        return self.title
