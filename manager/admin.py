# -*- coding: utf-8 -*-
# __author__ = chenchiyuan

from __future__ import division, unicode_literals, print_function
from django.contrib import admin
from models import Job, Manager

class ManagerAdmin(admin.ModelAdmin):
  pass

class JobAdmin(admin.ModelAdmin):
  pass

admin.site.register(Job, JobAdmin)
admin.site.register(Manager, ManagerAdmin)