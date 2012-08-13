# -*- coding: utf-8 -*-
# __author__ = chenchiyuan

from __future__ import division, unicode_literals, print_function
from manager.tasks import BaseTask
from django.conf import settings

import py_compile
import json
import uuid
import os
import logging

logger = logging.getLogger(__name__)

class MafengwoSpiderTask(BaseTask):
  def __init__(self, start, end,  burst):
    self.start = start
    self.end = end
    self.burst = burst

  def map(self):
    start = self.start
    end = self.end
    burst = self.burst

    return [{'start': i, 'end': (i+burst) if (i+burst) <=end else end} for i in range(start, end+1, burst)]

  def callback(self, worker, job):
    json_data = json.loads(job.data)
    json_data['unique'] = str(job.unique)

    try:
      result = self.on_callback(json_data)
    except Exception as err:
      logger.error(err)
      result = {'success': 'success'}

    return json.dumps(result)

  def on_callback(self, json_data):
    if json_data.has_key('exception'):
      return json.dumps(json_data)

    start = int(json_data['start'])
    end = int(json_data['end'])
    unique = str(json_data['unique']) if json_data.has_key('unique') else str(uuid.uuid1())

    self.compile(start, end, unique)
    self.run(unique)
    return json.dumps({'success' : 'Success'})

  def compile(self, start, end, unique):
    file = open('%s/mafengwo.txt' %settings.TEMPLATE_DIR, 'r')
    data = file.read()
    file.close()

    path = '%s/mafengwo_%s.py' %(settings.SPIDER_EXE_HOME, unique)
    file = open(path, 'w')
    file.write(data %(start, end, unique))
    file.close()

    py_compile.compile(path)

  def run(self, unique):
    command_1 = 'cd %s' %settings.SPIDER_HOME
    command_2 = 'scrapy crawl mafengwo_%s' %unique
    os.system('%s && %s' %(command_1, command_2))