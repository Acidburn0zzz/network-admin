#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 Adriano Monteiro Marques
#
# Authors: Amit pal<amix.pal@gmail.com>
#          Piotrek Wasilewski <wasilewski.piotrek@gmail.com>
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

try:
    import simplejson as json
except ImportError:
    import json

from django.db import models

from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
import pytz
import time

from netadmin.networks.models import Host
from netadmin.users.models import UserProfile


ALERT_LEVELS = (
    (0, _('No alert')),
    (1, _('Low')),
    (2, _('Medium')),
    (3, _('High'))
)


class EventFieldNotFound(Exception):
    pass

class EventFieldsNotValid(Exception):
    pass


class EventTypeCategory(models.Model):
    """Represents category to which an event type may be assigned
		
	"""
    name = models.CharField(max_length=50, verbose_name=_("Name"))
    slug = models.SlugField(blank=True, verbose_name=_("Message"))
    user = models.ForeignKey(User, verbose_name=_("User"))
    parent = models.OneToOneField('self', verbose_name=_("Parent category"),
                                  null=True, blank=True, unique=True)

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.pk:
            self.slug = slugify(self.name)
        super(EventTypeCategory, self).save(*args, **kwargs)


class EventType(models.Model):
    """
    Describes type of an event, e.g. INFO, CRITICAL etc. Note that every event
    type is linked with user - its owner. That is because events types are
    created automatically, when events are reported so every user may have
    different set of types.
    
    Alert level has no effect on reporting events or managing them. This field
    only indicates importance of events and is used to distinguish those of
    them which should be treated differently.
    """
    name = models.CharField(max_length=50)
    name_slug = models.SlugField(blank=True)
    user = models.ForeignKey(User)
    alert_level= models.SmallIntegerField(choices=ALERT_LEVELS, default=0)
    notify = models.BooleanField(default=False)
    category = models.OneToOneField(EventTypeCategory, unique=True, null=True)
    
    def __unicode__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.pk:
            self.name_slug = slugify(self.name)
        super(EventType, self).save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # delete relations between event type and reports
        related = self.reportmetaeventtype_set.all()
        related.delete()
        
        super(EventType, self).delete(*args, **kwargs)
        
    def events(self):
        return self.event_set.all()
    
    def pending_events(self):
        return self.events().filter(checked=False)

class Event(models.Model):
    """
    Event model class represents single notification reported to the Network
    Administrator. The following fields are defined:
        * message - description of an event
        * short_message - shorter description (could be used as a title)
        * message_slug - slug made of short_message
        * timestamp - moment, when event occured on host
        * protocol - network protocol
        * event_type - foreign key to the EventType object which simply stores
          short and readable event name like **INFO** or **WARNING**
        * source_host - foreign key to the Host object; this is the host from
          where the event came
        * fields_class - identifier of the class of additional fields
        * fields_data - serialized fields that contain more specific data
          about the event
        * checked - True means that event has been marked by user as known
          (actually this field is important only for alerts, where information
          about event status is really important)
    
    Note: Although event hasn't *user* field specified, we can say that
          event belongs to the user who ownes the source host.
    """
    message = models.TextField()
    short_message = models.CharField(max_length=200)
    message_slug = models.SlugField()
    timestamp = models.DateTimeField()
    protocol = models.CharField(max_length=30)
    event_type = models.ForeignKey(EventType)
    source_host = models.ForeignKey(Host, blank=True)
    fields_class = models.CharField(max_length=50, null=True, blank=True)
    fields_data = models.TextField(null=True, blank=True)
    checked = models.BooleanField(default=False)
    
    def __unicode__(self):
        return "'%s' at %s" % (self.message, self.timestamp)
    
    def save(self, *args, **kwargs):
        if not self.pk:
            self.message_slug = slugify(self.short_message)
        super(Event, self).save(*args, **kwargs)

    def get_details(self):
        """Returns event details extracted from monitoring module fields"""
        try:
            fields = json.loads(self.fields_data)
        except ValueError:
            raise EventFieldsNotValid(_("Cannot decode fields data."))
        return fields
    fields = property(get_details)
    
    def get_localized_timestamp(self):
		host_timezone = pytz.timezone(self.source_host.timezone)
		user = User.objects.get(username = self.source_host.user)
		user_obj = UserProfile.objects.get(id = user.id)
		if user_obj.timezone == u'': 
			user_obj.timezone = self.source_host.timezone
		user_timezone = pytz.timezone(user_obj.timezone) 
		localized_datetime_host = host_timezone.localize(self.timestamp)
		localized_datetime_user = user_timezone.localize(self.timestamp)
		differ_datetime_event = localized_datetime_host - localized_datetime_user
		event_time = self.timestamp - differ_datetime_event
		return event_time
    
    def get_field(self, field_name, default=None):
        try:
            fields = self.get_details()
        except EventFieldsNotValid:
            return default
        if field_name not in fields:   
            return default
            #raise EventFieldNotFound(_("The field '%s' is not defined for this event.") % field_name)
        return fields[field_name]
    
    def _html_message(self):
        return self.message.replace('\n', '<br />')
    html_message = property(_html_message)
    
    def user(self):
        return self.source_host.user
    
    def get_html(self):
        """Notifier support: returns event data in HTML"""
        title = '%s %s' % (str(self.timestamp), self.event_type.name)
        return '<h2>%s</h2><p>%s</p>' % (title, self.html_message)
    
    def api_detail(self):
        return {
            'event_id': self.pk,
            'description': self.message,
            'short_description': self.short_message,
            'event_type': self.event_type.name,
            'timestamp':  str(self.timestamp),
            'protocol': self.protocol,
            'source_host_id': self.source_host.pk,
            'fields_class': self.fields_class,
            'fields_data': self.fields_data
        }
        
    def api_list(self):
        return {
            'id': self.pk,
            'short_description': self.short_message
        }

class EventComment(models.Model):
    comment = models.TextField()
    user = models.CharField(max_length=30, null = False, blank=True)
    timestamp = models.DateTimeField(null=False, blank=True)
    event = models.ForeignKey(Event, blank=False, null=False)
    
    def __unicode__(self):
        return "'%s' at %s" % (self.comment)
