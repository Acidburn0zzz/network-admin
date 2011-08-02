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

from django import forms
from django.forms.models import modelformset_factory

from netadmin.plugins.core import load_plugins
from netadmin.plugins.models import PluginSettings, WidgetSettings

widgets = sum([plugin().widgets() for plugin in load_plugins(active=True)], [])
WIDGETS_CHOICES = [(widget.__name__, widget.name) for widget in widgets]


class WidgetCreateForm(forms.ModelForm):
    column = forms.ChoiceField(choices=[(1,1), (2,2)])
    widget_class = forms.ChoiceField(choices=WIDGETS_CHOICES)
    
    class Meta:
        model = WidgetSettings
        fields = ('column', 'dashboard', 'widget_class')
        widgets = {
            'dashboard': forms.HiddenInput()
        }

class PluginSettingsForm(forms.ModelForm):
    def get_meta(self):
        for plugin in load_plugins():
            meta = plugin().plugin_meta()
            if meta['name'] == self.instance.plugin_name:
                return meta
        return {}
    
    class Meta:
        model = PluginSettings
        
PluginSettingsFormset = modelformset_factory(PluginSettings,
                                             form=PluginSettingsForm)