# -*- coding: utf-8 -*-
# __author__ = chenchiyuan

from __future__ import division, unicode_literals, print_function

from gearman.worker import GearmanWorker
import json
import threading
from manager.utils import get_gearman_host

class Worker(GearmanWorker):
  def __init__(self, host_list=get_gearman_host()):
    super(Worker, self).__init__(host_list=host_list)

  def on_job_execute(self, current_job):
    return super(Worker, self).on_job_execute(current_job)

  def on_job_exception(self, current_job, exc_info):
    return super(Worker, self).on_job_exception(current_job, exc_info)

  def on_job_complete(self, current_job, job_result):
    json_data = json.loads(job_result)
    if isinstance(json_data, dict) and json_data.has_key('quit'):
      self.send_job_complete(current_job, job_result)
      self.shutdown()
      return True
    return super(Worker, self).on_job_complete(current_job, job_result)

  def safely_work(self):
    try:
      self.work()
    except Exception as err:
      print(err)
      pass

  def after_poll(self, any_activity):
    return True

class ThreadWorker(threading.Thread):
  def __init__(self, task, callback, daemon=False, host_list=get_gearman_host()):
    threading.Thread.__init__(self)
    self.task = task
    self.callback = callback
    self.daemon = daemon
    self.worker = Worker(host_list=host_list)

  def run(self):
    self.worker.register_task(self.task, self.callback)
    self.worker.safely_work()
