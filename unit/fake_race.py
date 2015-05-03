__author__ = 'vijay'

import sys
sys.path.append("../")
import mock
from db import *
import json

@staticmethod
def fake_race_api(track_id):
  return '158928'

@staticmethod
def fake_in_progress_race():
  return '158928'

@staticmethod
def fake_scoreboard_api(heat_id):
  s = ClubSpeedApi.url+ClubSpeedApi.api_race+heat_id+ClubSpeedApi.key
  res = requests.get(s)
  html = json.loads(res.text)
  html['race']['heat_status_id'] = 1
  return html

@staticmethod
def fake_scoreboard_api1(heat_id):
  s = ClubSpeedApi.url+ClubSpeedApi.api_race+heat_id+ClubSpeedApi.key
  res = requests.get(s)
  html = json.loads(res.text)
  return html

def test1():
  ClubSpeedApi.get_race_api = fake_race_api
  ClubSpeedApi.get_scoreboard_api = fake_scoreboard_api
  Race.get_in_progress_race = fake_in_progress_race
  print ClubSpeedApi.get_scoreboard_api(ClubSpeedApi.get_race_api(1))
  create_race(22,22,1,1)
  init_race()