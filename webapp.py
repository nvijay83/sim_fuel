from operator import itemgetter
import re
from flask import Flask, request, render_template, redirect, url_for, abort, flash, jsonify
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
  karts = get_race()
  start = "<td><p>"
  end = "</p></td>"
  glb=""
  s = ""
  l = sorted(karts)
  l = [int(i) for i in l]
  l = sorted(l)
  for i in l:
    s=s+"<tr>"+start+str(i)+end
    s=s+start+str(karts[str(i)][0])+end+"</tr>\n"
  f = open('live.html','r')
  for i in f:
    if "insert_here" in i:
      glb = glb+s
    else:
      glb = glb+i
  f.close()
  return glb

@app.route('/up', methods=['GET','POST'])
def up():
  return render_template("update.html",update_string="") 
@app.route('/update', methods=['GET','POST'])
def update():
  kart = int(request.form['kart'])
  cur_lap = int(request.form['cur_lap'])
  fuel = int(request.form['fuel'])
  lap_empty=update_db(kart, fuel, cur_lap)
  s="Update successful: kart %d, current lap %d, fuel %d lap empty %d"%(kart,cur_lap,fuel,lap_empty)
  print s
  return render_template("update.html", update_string=s)


if __name__ == "__main__":
    # TODO: move to config
    app.run(host="0.0.0.0", port=5000, threaded=False,debug=True)

