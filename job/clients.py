# -*- coding: utf-8 -*-
from __future__ import division, unicode_literals, print_function

import json
from gearman.client import GearmanClient
from gearman.admin_client import GearmanAdminClient
from job.workers import Worker
from job.utils import get_gearman_host
import os

class Client(GearmanClient):
  def __init__(self, host_list=get_gearman_host(), *args, **kwargs):
    super(Client, self).__init__(host_list, *args, **kwargs)

  def send_job(self, name, data, unique=False, *args, **kwargs):
    print("Send job task %s, %r" %(name, data))
    self.submit_job(task=name, data=data, unique=unique, *args, **kwargs)

  def send_jobs(self, jobs, wait_until_complete=False, background=False):
    print("Send jobs count %d" %len(jobs))
    return self.submit_multiple_jobs(jobs, wait_until_complete=wait_until_complete, background=background)

class Admin(GearmanAdminClient):
  def __init__(self, host_list=get_gearman_host(), *args, **kwargs):
    super(Admin, self).__init__(host_list=host_list, *args, **kwargs)
    self.host_list = host_list

  def get_status(self):
    return super(Admin, self).get_status()

  def get_workers(self):
    return super(Admin, self).get_workers()

  def get_version(self):
    return super(Admin, self).get_version()

  def get_response_time(self):
    return super(Admin, self).ping_server()

  def empty_task(self, task):
    def callback(worker, job):
      return json.dumps({'a': 'a'})

    worker = Worker(self.host_list)
    worker.register_task(task, callback)
    worker.safely_work()

  def start_server(self, port=4730):
    os.system('gearmand -d -L 0.0.0.0 -p %s' %str(port))
    print("Job Server Start at port %s" %str(port))

  def send_shutdown(self, graceful=True):
    print("Job Server will shutdown")
    return super(Admin, self).send_shutdown(graceful)