# -*- coding: utf-8 -*-
# __author__ = chenchiyuan

from __future__ import division, unicode_literals, print_function
from django.conf import settings

HOST = settings.GEARMAN_HOST
PORT = settings.GEARMAN_PORT

def get_gearman_host(port=None):
  p = int(port) if port else PORT
  return ['%s:%d' %(HOST, p)]