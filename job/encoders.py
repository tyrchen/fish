# -*- coding: utf-8 -*-
from __future__ import division, unicode_literals, print_function
import json
import gearman

class JSONDataEncoder(gearman.DataEncoder):
  @classmethod
  def encode(cls, encodable_object):
    if not encodable_object:
      return None

    return json.dumps(encodable_object)

  @classmethod
  def decode(cls, decodable_string):
    if not decodable_string:
      return None
    return json.loads(decodable_string)
