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

import base64
import datetime
import json
import random
from django.http import HttpRequest
from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from networks.models import Host
from events.models import Event
from piston.oauth import *
from piston.models import *

class BasicTest(TestCase):
    def setUp(self):
        #set up Django testing client
        self.client = Client()
        
        self.username = 'user'
        self.password = 'pass'
        
        #set up Django user
        self.user = User(username=self.username)
        self.user.set_password(self.password)
        self.user.save()
        
        #set up some hosts
        for i in xrange(10):
            h = Host(name='host_%i' % i,
                     description='description number %i' % i,
                     ipv4='127.0.0.%i' % (i+1),
                     ipv6='0:0:0:0:0:0:7f00:%i' % (i+1))
            h.save()
            
    def get_auth_string(self):
        """Helper function - returns basic authentication string"""
        auth = '%s:%s' % (self.username, self.password)
        auth_string = 'Basic %s' % base64.encodestring(auth)
        auth_string = auth_string.strip()
        return auth_string
    
    def test_hosts(self):
        """Select all hosts from database and get details of each """
        hosts = Host.objects.all()
        auth_string = self.get_auth_string()
        for host in hosts:
            response = self.client.get(reverse('host_detail', args=[host.pk]),
                                   HTTP_AUTHORIZATION=auth_string)
            host_json = json.loads(response.content)
            self.assertIn('host_id', host_json.keys())
    
    def test_hosts_list(self):
        """Select list of existing hosts"""
        auth_string = self.get_auth_string()
        
        response = self.client.get('/api/host/list/',
                                   HTTP_AUTHORIZATION=auth_string)
        
        j = json.loads(response.content)
        
        self.assertIn('hosts', j.keys())

        hosts_list = j['hosts']
        for host in hosts_list:
            self.assertIn('id', host.keys())
            self.assertIn('name', host.keys())
            
            response = self.client.get('/api/host/%s/' % host['id'],
                                       HTTP_AUTHORIZATION=auth_string)
            
            j = json.loads(response.content)
            
            self.assertIn('host_id', j.keys())
        
    def test_basic_auth(self):
        """Test basic authentication""" 
        host = Host.objects.all()[0]
        url = '/api/host/%i/' % host.pk
        
        auth_string = self.get_auth_string()
        
        response = self.client.get(url, HTTP_AUTHORIZATION=auth_string)
        
        self.assertEqual(response.status_code, 200)
        
    def test_report_event(self):
        """Report events"""
        
        def gen_event(index):
            #types below come from Dragos' documentation for Network Inventory
            types = ['CRITICAL', 'WARNING', 'INFO', 'RECOVERY']
            event = {
                'message': 'event_%i' % index,
                'type': types[random.randint(0, len(types) - 1)],
                'timestamp': '%s' % datetime.datetime.now(),
                'source_host_ipv4': '127.0.0.%i' % (index + 1),
                'source_host_ipv6': '0:0:0:0:0:0:7f00:%i' % (index + 1),
                'monitoring_module': '%i' % index,
                'monitoring_module_fields': '',
            }
            return event
        
        events = [gen_event(i) for i in xrange(10)]
        auth_string = self.get_auth_string()
        for event in events:
            response = self.client.post(reverse('report_event'),
                                        data=event,
                                        HTTP_AUTHORIZATION=auth_string)
            r_json = json.loads(response.content)
            self.assertEqual(r_json['status'], 'ok')
            
    def test_event_details(self):
        """Select all reported events"""
        for event in Event.objects.all():
            url = '/api/event/%i/' % event.pk
            uth_string = self.get_auth_string()
            response = self.client.get(url, HTTP_AUTHORIZATION=auth_string)
            j = json.loads(response.content)
            self.assertIn('event_id', j.keys())