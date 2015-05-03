import json
from pprint import pprint
import time
import os
import shutil
import io
import tinydb
import threading
from tinydb import TinyDB, where
import requests

def get_race_folder():
  return ".db/"+time.strftime("%m-%d-%Y")
t = get_race_folder()
try:
  os.stat(t)
except:
  os.mkdir(t)

def create_race(init_fuel, max_fuel, races, track_id):
  t = get_race_folder()
  try:
    os.stat(t)
  except:
    os.mkdir(t)
  db = TinyDB(t+'/config.json')
  db.purge()
  db.insert({'init_fuel':init_fuel, 'max_fuel':max_fuel, 'races':races,'track_id':track_id})
  db = TinyDB(t+'/laps.json')
  db.purge()
  db = TinyDB(t+'/logs.json')
  db.purge()
  db = TinyDB(t+'/laps_empty.json')
  db.purge()
  db = TinyDB(t+'/race.json')
  db.purge()
  db = TinyDB(t+'/race_log.json')
  db.purge()

def get_config():
  db = TinyDB(get_race_folder()+'/config.json')
  data = db.all()
  init_fuel = data[0]['init_fuel']
  max_fuel = data[0]['max_fuel']
  races = data[0]['races']
  track_id = data[0]['track_id']
  return init_fuel,max_fuel,races,track_id

def init_race():
  (init_fuel, max_fuel, races, track_id) = get_config()
  thread = threading.Thread(target=monitor, args=(init_fuel, max_fuel, races, track_id))
  thread.start()


def add_fuel(cust_id,fuel):
  cust_id = int(cust_id)
  t = get_race_folder()
  db1 = TinyDB(t+'/logs.json')
  db = TinyDB(t+'/laps_empty.json')
  db2 = TinyDB(t+'/race.json')
  #get race
  race = db2.search(where('status') == 1)[0]
  race_id = race['race_id']
  #get racer
  racer,created = Racer.get_racer(cust_id, None, None,None, None,None, race_id)
  if created:
    print "This cannot happen"
    return
  (init_fuel, max_fuel, races, track_id) = get_config()
  laps = racer.laps
  #get laps empty
  laps_empty = db.search(where('cust_id') == cust_id)[0]
  lap_empty = laps_empty['laps_empty']
  empty = min(laps+max_fuel, lap_empty+fuel)
  db.update({'laps_empty':empty}, where('cust_id') == cust_id)
  db1.insert({'cust_id':cust_id,'laps':laps,'fuel':fuel,'time':time.time()})

def add_fuel_correction(cust_id,fuel):
  cust_id = int(cust_id)
  t = get_race_folder()
  db1 = TinyDB(t+'/logs.json')
  db = TinyDB(t+'/laps_empty.json')
  db2 = TinyDB(t+'/race.json')
  #get race
  race = db2.search(where('status') == 1)[0]
  race_id = race['race_id']
  #get racer
  racer,created = Racer.get_racer(cust_id, None, None,None, None, None, race_id)
  if created:
    print "This cannot happen"
    return
  (init_fuel, max_fuel, races, track_id) = get_config()
  laps = racer.laps
  #get laps empty
  laps_empty = db.search(where('cust_id') == cust_id)[0]
  lap_empty = laps_empty['laps_empty']
  empty = lap_empty+fuel
  db.update({'laps_empty':empty}, where('cust_id') == cust_id)
  db1.insert({'cust_id':cust_id,'laps':laps,'fuel':fuel,'time':time.time()})

def adjust_fuel(cust_id, laps):
  t = get_race_folder()
  cust_id = int(cust_id)
  db = TinyDB(t+'/laps_empty.json')
  laps_empty = db.search(where('cust_id') == cust_id)[0]
  lap_empty = laps_empty['laps_empty']
  empty = lap_empty-int(laps)
  db.update({'laps_empty':empty}, where('cust_id') == cust_id)

class Race:
  db = TinyDB(get_race_folder()+'/race_log.json')
  db1 = TinyDB(get_race_folder()+'/race.json')

  @staticmethod
  def create_race(race_id, duration, race_time):
    Race.db1.insert({'race_id':race_id,'duration':duration,'race_time':race_time, 'last_update':time.time(), 'status':1})

  @staticmethod
  def add_log(race_id, duration, race_time):
    Race.db.insert({'race_id':race_id,'duration':duration,'race_time':race_time,'log_time':time.time()})
    Race.db1.update({'race_time':race_time, 'last_update':time.time()}, where('race_id') == race_id)

  @staticmethod
  def end_race(race_id):
    Race.db1.update({'status':2}, where('race_id') == race_id)

  @staticmethod
  def get_in_progress_race():
    race = Race.db1.search(where('status') == 1)
    if len(race) > 0:
      return race[0]['race_id']
    else:
      return None

class Racer:
  db = TinyDB(get_race_folder()+'/laps.json')
  db1 = TinyDB(get_race_folder()+'/laps_empty.json')

  @staticmethod
  def get_laps_empty(cust_id):
    laps_empty = Racer.db1.search(where('cust_id') == cust_id)[0]
    return laps_empty

  @staticmethod
  def get_live_scoreboard():
    ret = {}
    cur_race = Race.get_in_progress_race()
    laps_empty = Racer.db1.all()
    dic = {}
    cust_map = {}
    for i in laps_empty:
      dic[i['cust_id']] = i['laps_empty']
    if cur_race is None:
      all = Racer.get_all_racers()
      for i in all:
        cust_map[i['cust_id']] = i['nickname']
      for i in laps_empty:
        ret[i['cust_id']] = {'laps_empty':i['laps_empty'], 'nickname':cust_map[i['cust_id']]}
      return ret, True
    else:
      cur_race = Racer.get_racers(cur_race)
      for i in cur_race:
        ret[i['cust_id']] = {'last_lap':i['last_lap'],'laps':i['laps'],'kart':i['kart'],'laps_empty':dic[i['cust_id']]-i['laps']}
    return ret, False


  @staticmethod
  def get_all_racers():
    return Racer.db.all()

  @staticmethod
  def get_racers(race_id):
    racers = Racer.db.search(where('race_id') == race_id)
    return racers

  @staticmethod
  def get_racer(cust_id, nickname, laps, kart, avg_time, last_lap, race_id):
    #check if racer_id is present in laps_empty table if not create one
    cust_id = int(cust_id)
    laps_empty = Racer.db1.search(where('cust_id') == cust_id)
    if len(laps_empty) == 0:
      init_fuel, max_fuel, races, track_id = get_config()
      Racer.db1.insert({'cust_id': cust_id, 'laps_empty': init_fuel})
    else:
      #we are good
      pass

    racer = Racer.db.search((where('cust_id') == cust_id) & (where('race_id') == race_id))
    if len(racer) >= 1:
      racer = racer[0]
      return Racer(racer['cust_id'], racer['nickname'], racer['laps'], racer['kart'], racer['avg_time'], racer['last_lap'], racer['race_id']), False
    else:
      racer = Racer(cust_id, nickname, laps, kart, avg_time, last_lap, race_id)
      Racer.db.insert(racer.get_json())
      return racer, True


  def __init__(self, iden, nickname, laps, kart, avg_time, last_lap, race_id):
    self.iden = int(iden)
    self.nickname = nickname
    self.laps = int(laps)
    if kart is not None:
      self.kart = int(kart)
    else:
      self.kart = 0
    self.race_id = race_id
    self.avg_time = avg_time
    self.last_lap = last_lap

  def __eq__(self,other):
    return self.iden == other.iden

  def __ne__(self, other):
    return not self.__eq__(other)
  
  def update(self, laps, kart, avg_time, last_lap):
    if kart is not None:
      self.kart = int(kart)
    else:
      self.kart = 0
    self.laps = int(laps)
    self.avg_time = avg_time
    self.last_lap = last_lap
    Racer.db.update({'laps':self.laps,'kart':self.kart,'avg_time':avg_time,'last_lap':last_lap}, where('cust_id') == self.iden)

  def __str__(self):
    return "id is %s, nickname is %s, laps is %d, kart is %d, avg_time is %s, last_lap is %s"%(self.iden, self.nickname, self.laps, self.kart, self.avg_time, self.last_lap)

  def get_json(self):
    return {'cust_id':self.iden,'nickname':self.nickname,'kart':self.kart,'laps':self.laps,'avg_time':self.avg_time, 'last_lap':self.last_lap,'race_id':self.race_id}

def print_racers(racers):
  for i in racers:
    print i, racers[i]

class ClubSpeedApi:
  url = "http://lmkfremont.clubspeedtiming.com/api/index.php/"
  api_current_race = "races/current_race_id.json?track="
  api_race = "races/scoreboard.json?heat_id="
  track_list="tracks/index.json?"
  key_no = "key=8danakf8ahdkf"
  key = "&key=8danakf8ahdkf"

  @staticmethod
  def get_tracks_api():
    s = ClubSpeedApi.url+ClubSpeedApi.track_list+ClubSpeedApi.key_no
    res = requests.get(s)
    print res.url
    tracks = json.loads(res.text)
    return tracks['tracks']

  @staticmethod
  def get_race_api(track_id):
    s = ClubSpeedApi.url+ClubSpeedApi.api_current_race+str(track_id)+ClubSpeedApi.key
    res = requests.get(s)
    print res.url
    if 'error' in res.text:
      print "No race in progress"
      return None
    else:
      heat_id = json.loads(res.text)
      print heat_id
      print "curent race", heat_id
      return heat_id

  @staticmethod
  def get_scoreboard_api(heat_id):
    s = ClubSpeedApi.url+ClubSpeedApi.api_race+heat_id+ClubSpeedApi.key
    res = requests.get(s)
    print res.url
    if res.text !=  "" and len(res.text) > 6 and 'error' not in res.text:
      try:
        html = json.loads(res.text)
        print html
      except:
        return None
      return html


def monitor(init_fuel, max_fuel, races, track_id):
  completed = []
  print "races to monitor %d"%(races)
  print init_fuel, max_fuel
  count = 0
  session_end = False
  while True:
    if session_end == True:
      break
    heat_id = ClubSpeedApi.get_race_api(track_id)
    if heat_id is None or heat_id in completed:
      time.sleep(5)
      continue
    first = True
    racers = {}
    while True:
      race = ClubSpeedApi.get_scoreboard_api(heat_id)
      if race is None:
        break
      if first == True:
        Race.create_race(race['race']['id'],race['race']['duration']*60,race['race']['race_time_in_seconds'])
        first = False
        time.sleep(2)
        continue
      if race['race']['heat_status_id'] == "2" or race['race']['heat_status_id'] == "3":
        count = count + 1
        Race.end_race(race['race']['id'])
        completed.append(heat_id)
        r = race['scoreboard']
        for i in r:
          adjust_fuel(i['racer_id'],i['lap_num'])
        if count == races:
          session_end = True
        break

      Race.add_log(race['race']['id'],race['race']['duration']*60,race['race']['race_time_in_seconds'])
      r = race['scoreboard']
      for i in r:
        if i['racer_id'] not in racers:
          cust, created = Racer.get_racer(i['racer_id'],i['nickname'],i['lap_num'], i['kart_num'], i['average_lap_time'], i['last_lap_time'], heat_id)
          racers[i['racer_id']] = cust
        else:
          cust = racers[i['racer_id']]
          cust.update(i['lap_num'],i['kart_num'],i['average_lap_time'],i['last_lap_time'])
      print_racers(racers)
      time.sleep(3)

#create_race(60,60,2,1)
#init_race()
#print get_config()
#r = Racer(1,'vijay', 0, 20, 61)
#r.update_laps_and_kart(4, 20)
#r = Racer(2,'bill', 61, 6, 61)
#add_fuel(1, 25)
#add_fuel_correction(1,10)
#racers = get_racers_db()