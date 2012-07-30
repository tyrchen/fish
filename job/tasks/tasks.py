# -*- coding: utf-8 -*-
from __future__ import division, unicode_literals, print_function
import json, py_compile, os
from django.conf import settings
import uuid

from settings import logger

class BaseTask(object):
  def map(self):
    pass

  def callback(self, worker, job):
    json_data = json.loads(job.data)
    return json.dumps(self.on_callback(json_data))

  def on_callback(self, json_data):
    pass

  def sync_run(self, need_unique=False):
    json_datas = self.map()

    for json_data in json_datas:
      if need_unique:
        json_data['unique'] = str(uuid.uuid1())
      self.on_callback(json_data)

  def on_success(self):
    pass

  def reduce(self):
    pass

class TestTask(BaseTask):
  def __init__(self, num, burst):
    self.num = num
    self.burst = burst

  def map(self):
    data_list = range(0, self.num)
    return [{'data': data_list[data: data+self.burst]} for data in range(0, self.num, self.burst)]

  def on_callback(self, json_data):
    list =json_data['data']
    for i in list:
      print(i)

    return {'success': 'success'}

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
    file = open('%s/job/jobs/spiders/spiders/spiders/templates' %settings.PROJECT_HOME, 'r')
    data = file.read()
    file.close()

    file = open('%s/job/jobs/spiders/spiders/spiders/mafengwo_%s.py' %(settings.PROJECT_HOME, unique), 'w')
    file.write(data %(start, end, unique))
    file.close()

    py_compile.compile('%s/job/jobs/spiders/spiders/spiders/mafengwo_%s.py' %(settings.PROJECT_HOME, unique))

  def run(self, unique):
    command_1 = 'cd %s/job/jobs/spiders/' %settings.PROJECT_HOME
    command_2 = 'ls'
    command_3 = 'scrapy crawl mafengwo_%s' %unique
    os.system('%s && %s && %s' %(command_1, command_2, command_3))

class RailEuropeTask(BaseTask):
  def __init__(self, from_city=None, to_city=None):
    self.from_city = from_city
    self.to_city = to_city

  def map(self):
    file = open('job/tasks/hot_cities', 'r')
    lines = file.readlines()
    file.close()

    cities = []
    for line in lines[:20]:
      city = line.split('\t')[0]
      cities.append(city)

    results = []
    for from_city in cities:
      result = []
      for to_city in cities:
        if from_city != to_city:
          result.append({'from_city': from_city, 'to_city': to_city})

      results.append({'data' : result})

    return results

  def on_callback(self, json_data):
    import requests, xmltodict, datetime, base64
    request_url = 'http://tukeq.com/api/railway/add/'

    TIME_SPAN = 7

    for data in json_data['data']:
      from_city = data['from_city']
      to_city = data['to_city']

      for delta in range(1, TIME_SPAN+1):
        time_delta = datetime.timedelta(days=delta)
        format_date = (datetime.datetime.now() + time_delta).strftime('%Y-%m-%d')
        print("Now test from_city %s, to_city %s, date %s" %(from_city, to_city, format_date))
        file = open('job/tasks/headers', 'r')
        resource = file.read()
        file.close()
        resource = resource %(from_city, to_city, format_date)
        requestUrl = 'https://m.raileurope.com/us/ws-auth/ws-auth.xml?version=2&server=s2'
        requestHeaders = {'user-agent': 'wsdl2objct', 'soapaction':'urn:doBuildItinerary' , 'content-type': 'text/xml; charset=utf-8', 'accept-encoding': 'gzip, deflate'}

        response = requests.post(requestUrl, data=resource, headers=requestHeaders)

        if response.status_code == 200:
          doc = xmltodict.parse(response.text)
          try:
            solutions = doc['soapenv:Envelope']['soapenv:Body']['doBuildItineraryResponse']['return']['buildItineraryContent']['forwardItinerary']['solutions']
          except Exception as err:
            logger.error(err)
            solutions = ''

          if not solutions:
            continue

          params = {'from_city': from_city, 'to_city': to_city, 'date': format_date,
                    'solutions': base64.b64encode(json.dumps({'solutions': solutions}))}
          api_response = requests.post(url=request_url, data=params)
          print("Success parse from_city %s, to_city %s, %s" %(from_city, to_city, format_date))

    return {'success': 'success'}

