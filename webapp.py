from operator import itemgetter
import re
from flask import Flask, request, render_template, redirect, url_for, abort,flash, jsonify,send_from_directory
# noinspection PyUnresolvedReferences
#from flask.ext.login import LoginManager, login_user
# noinspection PyUnresolvedReferences
#from flask.ext.security import login_required
from db import *
from operator import itemgetter

app = Flask(__name__, static_folder='webapp/static', template_folder='webapp/templates')
#app.config.from_envvar('WEBAPP_SETTINGS')

@app.route('/live',methods=['GET','POST'])
def live():
  racers, finished = Racer.get_live_scoreboard()
  sorted_racers = [racers[i] for i in racers]
  if not finished:
    sorted_racers.sort(key=lambda k: k['kart'])
  else:
    sorted_racers.sort(key=lambda k: k['nickname'])
  return render_template('live.html', racers=sorted_racers, finished=finished)


@app.route('/create', methods=['GET','POST'])
def create():
  init_fuel = int(request.form['init_fuel'])
  max_fuel = int(request.form['max_fuel'])
  races = int(request.form['races'])
  print request.form['track']
  track_id = int(request.form['track'])
  create_race(init_fuel, max_fuel, races, track_id)
  init_race()
  return render_template('admin.html')

@app.route('/fix', methods=['GET','POST'])
def fix():
  cur_race = Race.get_in_progress_race()
  if cur_race is  None:
    return "No race in progress"
  else:
    racers = Racer.get_racers(cur_race)
  racers.sort(key=lambda k:k['kart'])
  return render_template("fix.html", update_string="", racers=racers)

@app.route('/correction',methods=['POST'])
def correction():
  cust_id = int(request.form['cust_id'])
  fuel = int(request.form['fuel'])
  update_string="updated: cust_id is %d, fuel is %d"%(cust_id,fuel)
  print update_string
  cur_race = Race.get_in_progress_race()
  add_fuel_correction(cust_id, fuel)
  if cur_race is  None:
    return "No race in progress"
  else:
    racers = Racer.get_racers(cur_race)
  racers.sort(key=lambda k:k['kart'])
  return render_template("fix.html",update_string=update_string, racers=racers)

@app.route('/up',methods=['GET','POST'])
def up():
  cur_race = Race.get_in_progress_race()

  if cur_race is  None:
    return "No race in progress"
  else:
    racers = Racer.get_racers(cur_race)
  racers.sort(key=lambda k:k['kart'])
  return render_template("up.html", racers=racers)

@app.route('/update', methods=['GET','POST'])
def update():
  cust_id = int(request.form['cust_id'])
  print request.form['fuel']
  fuel = int(request.form['fuel'])
  add_fuel(cust_id, fuel)
  cur_race = Race.get_in_progress_race()
  if cur_race is  None:
    return "No race in progress"
  else:
    racers = Racer.get_racers(cur_race)
  racers.sort(key=lambda k:k['kart'])
  print "added cust_id %d, fuel %s"%(cust_id,fuel)
  return render_template("up.html", racers=racers)

@app.route('/cr')
def cr():
  tracks = ClubSpeedApi.get_tracks_api()
  return render_template("index.html",tracks=tracks)

@app.route('/')
def index():
  return render_template("admin.html")

@app.route('/maxfuel', methods=['GET','POST'])
def max_fuel():
  print "here"
  print ""
  cust_id = int(request.form['cust_id'])
  print cust_id
  i,m,a,b = get_config()
  laps_empty = Racer.get_laps_empty(cust_id)
  cur_race = Race.get_in_progress_race()
  if cur_race is not None:
    racer, created = Racer.get_racer(cust_id,None, None, None, None, None, cur_race)
    max_fuel = m - (laps_empty['laps_empty'] - racer.laps)
    return str(max_fuel)
  else:
    return str(0)

'''
import sys
sys.path.append("unit/")
from fake_race import *
test1()
'''

if __name__ == "__main__":
    # TODO: move to config
    app.run(host="0.0.0.0", port=5000, threaded=False,debug=True)

