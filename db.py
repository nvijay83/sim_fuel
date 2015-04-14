import json
from pprint import pprint
import time
import os
import shutil
import io

def create_race():
  t = get_race_folder()
  try:
    os.stat(t)
  except:
    os.mkdir(t)
  shutil.copyfile('config.json',t+'/config.json')
  shutil.copyfile('init.txt',t+'/init.txt')

def get_race_folder():
  return ".db/"+time.strftime("%m-%d-%Y")

def get_init_race():
  return 'init.txt'

def get_db():
  return get_race_folder()+'/db.json'

def get_config():
  f = get_race_folder()+"/config.json"
  with open(f) as data_file:
    data = json.load(data_file)
  init_fuel = data['init_fuel']
  max_fuel = data['max_fuel']
  return init_fuel,max_fuel

def init_race():
  kart = {}
  kart_log = {}
  fol = get_race_folder()
  f = open(get_init_race(),'r')
  (init_fuel, max_fuel) = get_config()
  for i in f:
    if '#' in i:
      continue
    else:
      token = i.split(',')
      lap_empty = int(init_fuel) - int(token[1].strip())
      l = []
      l.append((0, lap_empty))
      kart[int(token[2].strip())] = (lap_empty, l)
  f.close()
  with open(get_db(),'w') as fp:
    json.dump(kart, fp, ensure_ascii=False)

def update_db(kart,fuel,cur_lap):
  kart = str(kart)
  with open(get_db()) as fp:
    db = json.load(fp)
  (init_fuel, max_fuel) = get_config()
  lap_empty = db[kart][0]
  lap_empty = min(cur_lap+max_fuel, lap_empty+fuel)
  db[kart][0] = lap_empty
  db[kart][1].append((cur_lap, fuel))
  with open(get_db(),'w') as fp:
    json.dump(db, fp, ensure_ascii=False)
  return lap_empty

def get_race():
  with open(get_db()) as fp:
    db = json.load(fp)
  return db

create_race()
init_race()
