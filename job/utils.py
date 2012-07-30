# -*- coding: utf-8 -*-
from __future__ import division, unicode_literals, print_function
import re
from subprocess import Popen, PIPE

def get_ip_addr():
  return re.search('\d+\.\d+\.\d+\.\d+',Popen('ifconfig', stdout=PIPE).stdout.read()).group(0)

def get_gearman_host(port=4730):
  return ['10.18.114.20:4730']
  #return ['%s:%s' %(get_ip_addr(), str(port))]

