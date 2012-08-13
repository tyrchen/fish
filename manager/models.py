# -*- coding: utf-8 -*-
from __future__ import division, unicode_literals, print_function
from django.db import models
from gearman.constants import *
from distribute.clients import Client
from distribute.admin import Admin
from distribute.workers import Worker, ThreadWorker
from utils import get_gearman_host

import tasks
import json
import logging

logger = logging.getLogger(__name__)

class JsonField(models.TextField):
  __metaclass__ = models.SubfieldBase
  '''
  Need to determine the data struct
  '''
  def __init__(self, *args, **kwargs):
    kwargs['default'] = kwargs.get('default', '')
    super(JsonField, self).__init__(*args, **kwargs)

  def to_python(self, value):
    if not value:
      return
    if isinstance(value, basestring):
      return json.loads(value, encoding='utf-8')
    else:
      return value

  def get_prep_value(self, value):
    if not value:
      return
    assert isinstance(value, list) or isinstance(value, dict)
    return json.dumps(value, encoding='utf-8')

  def value_to_string(self, obj):
    value = self._get_val_from_obj(obj)
    return self.get_prep_value(value)

class Manager(models.Model):
  """ 任务管理 -》 每个具体的task对应一个任务管理
  具体实现取决于task_handle的引用，采用反射来获取handle。
  distribute任务前，必须test通过，不要手动设置tested变量。
  """
  class Meta:
    verbose_name = verbose_name_plural = u'任务管理器'

  HANDLE_CHOICES = tuple([(obj.__name__, obj.__name__) for obj in tasks.__all__])

  name = models.CharField(verbose_name=u'名字', max_length=36, unique=True)
  description = models.CharField(verbose_name=u'描述', max_length=512, default='', blank=True)
  server_address = models.CharField(verbose_name=u'服务器地址', max_length=64, default=get_gearman_host()[0])
  tested = models.BooleanField(verbose_name=u'是否处理', default=False, help_text=u'如果没测试，将不能分发')

  task_handle = models.CharField(verbose_name=u'任务处理器', max_length=24, choices=HANDLE_CHOICES)

  def __unicode__(self):
    return u'%s %s' %(self.name, self.description)

  def dispatch(self, create=False, *args, **kwargs):
    """任务分发
    必须满足分发任务所需要的参数。任务管理者自己应该清楚。
    """
    if not self.tested:
      print('You must run script to test the task manager, then you can dispatch tasks')
      logger.error("Must test manager %s" %self.name)
      return
    
    handle = getattr(tasks, self.task_handle)(*args, **kwargs)
    data_list = handle.map()

    logger.info("Will handle task %s, num %d" %(self.name, len(data_list)))
    jobs = []
    for json_data in data_list:
      job = Job.create(name=self.name, data=json_data, manager=self) if create else None
      jobs.append(dict(task=str(self.name), data=json.dumps(json_data)))
    client = self.get_client()

    logger.info("Will send task %s, num %d" %(self.name, len(data_list)))
    #异步分发？
    client.send_jobs(jobs)

  def address(self):
    return [self.server_address]

  def send_task(self, json_data):
    job = Job.create(name=self.name, data=json_data, manager=self)
    if not job:
      return

    client = self.get_client()
    client.send_job(name=str(job.name), data=json.dumps(json_data), wait_until_complete=False)
    logger.info("Dispatch a task name %s, %r" %(job.name, json_data))

  def get_worker(self, host_list=get_gearman_host(), *args, **kwargs):
    handle = getattr(tasks, self.task_handle)(*args, **kwargs)()
    worker = Worker(host_list)
    worker.register_task(str(self.name), handle.callback)
    return worker

  def build_workers(self, workers=3, **kwargs):
    assert self.tested == True
    handle = getattr(tasks, self.task_handle)(**kwargs)
    for i in range(workers):
      t = ThreadWorker(task=str(self.name), callback=handle.callback)
      t.start()

  def clear_worker(self):
    self.send_task({'quit': True})

  def clear_workers(self):
    admin = Admin()
    current_status = admin.get_status()
    num = 0

    for status in current_status:
      if status['task'] == self.name:
        num = int(status['workers'])

    print(num)
    for i in range(num):
      self.clear_worker()

  def get_admin(self):
    """
    获得admin实例，可以管理gearmand

    """
    return Admin([self.server_address])

  def get_client(self):
    '''
    获得gearman client, 可以分发任务。
    '''
    return Client([self.server_address])

  def test(self, *args, **kwargs):
    """
    简单的测试任务是否可以分发。测试过后可能出现的问题。
    1. 编码在gearman中的传递。gearman只支持简单str编码。
    2. worker关闭可能出现的问题。

    """
    handle = getattr(tasks, self.task_handle)(*args, **kwargs)
    mapped_data = handle.map()
    
    assert 0 < len(mapped_data) < 1000
    assert isinstance(mapped_data, list)
    assert isinstance(mapped_data[0], dict)

    for json_data in mapped_data:
      assert isinstance(json.dumps(json_data), basestring)
      #模拟 send task, 所以job data为str
      result = handle.on_callback(json_data)
      assert isinstance(json.dumps(result), basestring)

    self.tested = True
    self.save()

    logger.info("Test task %s success" %self.name)

class Job(models.Model):
  class Meta:
    verbose_name = verbose_name_plural = u'任务'

  PRIORITY_CHOICES = (
    ('NONE', PRIORITY_NONE),
    ('LOW', PRIORITY_LOW),
    ('HIGH', PRIORITY_HIGH),
  )

  name = models.CharField(verbose_name=u'名字', max_length=36)
  unique = models.BooleanField(verbose_name=u'是否唯一', default=False)
  priority = models.CharField(verbose_name=u'优先级',max_length=24, choices=PRIORITY_CHOICES, default='NONE')
  data = JsonField()
  completed = models.BooleanField(verbose_name=u'是否完成', default=True)

  manager = models.ForeignKey(Manager, verbose_name=u'管理者')

  def __unicode__(self):
    return u'%s %d' %(self.name, self.id)

  @classmethod
  def create(cls, name, data, manager, *args, **kwargs):
    job = cls(name=name, data=data, manager=manager, *args, **kwargs)
    try:
      job.save()
    except Exception as err:
      print(err)
      return None
    return job
