import requests
from lxml import html
import json
import os.path

def create_cust_directory():
  try:
    os.stat(".db/cust")
  except:
    os.mkdir(".db/cust")

def create_heat_directory():
  try:
    os.stat(".db/heats")
  except:
    os.mkdir(".db/heats")

def get_cust_directory():
  return ".db/cust/"

def get_cust_file(cust):
  return get_cust_directory()+str(cust)+".json"

def is_cust_available(cust):
  if os.path.exists(get_cust_file(cust)):
    return True
  else:
    return False

def get_cust_db(cust):
  if not is_cust_available(cust):
    return None
  else:
    with open(get_cust_file(cust)) as fp:
      data = json.load(fp)
  return data

'''pass array of heats,kart tuple'''
def compare_cust_with_cache(cust, heats):
  data = get_cust_db(cust)
  if data is None:
    return False
  else:
    return data[cust] == heats

'''
   return cust -> heats, cached
'''
def get_cust_heats(cust, cached):
  customer = {}
  if cached == True:
    data = get_cust_db(cust)
    if data is not None:
      return data, True
  url = get_url_cust(cust)
  tree = get_tree(url)
  l = tree.xpath("//tr[@class='Normal']/td/a")
  l = [int(i.attrib['href'].split('=')[1]) for i in l]
  kart = tree.xpath("//tr[@class='Normal']/td/a/text()")
  kart = [int(i.split("Kart")[1].strip()) for i in kart]
  customer[cust] = []
  for i,j in zip(l,kart):
    customer[cust].append((i,j))
  return customer, False

def write_cust_db(cust, data):
  with open(get_cust_file(cust),'w') as fp:
    json.dump(data,fp)

def get_heat_directory():
  return ".db/heats/"

def is_heat_cached(heatno):
  if os.path.exists(get_heat_directory()+str(heatno)+".json"):
    return True
  else:
    return False

def get_name_id_map(tree):
  data = {}
  inv_data = {}
  name = get_racername(tree)
  ids = get_id(tree)
  for i,j in zip(name,ids):
    data[i] = j
    inv_data[j] = i
  return data, inv_data

def get_racername(tree):
  l = tree.xpath("//td[@class='Racername']/span/a/text()")
  return [i.encode('ascii','ignore') for i in l]

def get_avglap(tree):
  return tree.xpath("//td[@class='AvgLap']/span/text()")

def get_bestlap(tree):
  return tree.xpath("//td[@class='BestLap']/span/text()")

def get_id(tree):
  return [int(i.attrib['href'].split('=')[1]) for i in tree.xpath("//td[@class='Racername']/span/a")]

def get_alllaps(tree):
  data = {}
  l = tree.xpath("//tr[contains(@class,'LapTimesRow')]/td/text()")
  if len(l) == 0:
    return data
  cust = tree.xpath("//table[@class='LapTimes']/thead/tr/th/text()")
  laps = []
  first = True
  count = 0
  cust = [i.strip().encode('ascii','ignore') for i in cust]
  for i,j in zip(l[0::2], l[1::2]):
    '''First time when we go thru the list
       start appending'''
    i = int(i)
    s = j.split('[')
    j = s[0].strip().encode('ascii','ignore')
    if len(s) > 1:
      k = s[1].strip().encode('ascii','ignore')[:-1]
    else:
      k = 0
    if i is 1 and first is True:
      laps.append((i,j,k))
      first = False
      ''' When we process laps times of second driver
      save the first drivers to the map and clear out for second driver'''
    elif i is 1 and first is False:
      data[cust[count]] = laps
      count = count + 1
      laps = []
      laps.append((i,j,k))
    else:
      laps.append((i,j,k))
  #for final driver
  data[cust[count]] = laps
  return data

def get_totallaps(tree):
  return tree.xpath("//td[@class='Laps']/span/text()")

def get_url_heat(heatno):
  return "http://clubspeedtiming.com/lmkfremont/HeatDetails.aspx?HeatNo="+str(heatno)

def get_url_cust(custid):
  return "http://clubspeedtiming.com/lmkfremont/RacerHistory.aspx?CustID="+str(custid)

def get_tree(url):
  print "Processing url: %s"%(url)
  page = requests.get(url)
  return html.fromstring(page.text)

def populate_cust_db(directory, seed):
  cust = {}
  try:
    with open(directory+"/cust_map.json",'r') as fp:
      cust =json.load(fp)
  except IOError:
    print "No cust_map.json file to load"
    cust = {}
  url = get_url_cust(seed)
  tree = get_tree(url)
  l = tree.xpath("//tr[@class='Normal']/td/a")
  l = [i.attrib['href'].split('=')[1] for i in l]
  for i in l:
    url = get_url_heat(i)
    tree = get_tree(url)
    m,im = get_name_id_map(tree)
    for i in im:
      if i not in cust:
        cust[i] = im[i]
  with open(directory+"/cust_map.json",'w') as f:
    json.dump(cust, f)

def get_title(tree):
  return tree.xpath("//title/text()")[0].strip()

''' No Such URL exist'''
def is_valid_heat(tree):
  title = get_title(tree) 
  if title == "Server Error":
    return False
  else:
    return True

''' Is heat in progress'''
def is_heat_in_progress(tree):
  if is_valid_heat(tree):
    if not is_heat_complete(tree):
      data = get_alllaps(tree)
      if len(data) > 0:
        return True
      else:
        return False
    return False
  return False

''' Heat is complete. winner available '''
def is_heat_complete(tree):
  s = tree.xpath("//span[@id='lblWinner']/text()")[0].encode('ascii','ignore')
  s = s.strip()
  if s == '-':
    return False
  else:
    return True

'''returns json'''
def get_heat_db(heatno):
  data = {}
  if not is_heat_cached(heatno):
    return None
  try:
    with open(get_heat_directory()+str(heatno)+".json",'r') as fp:
      data = json.load(fp)
  except IOError:
    return None
  return data

def write_heat_db(data, filename):
  with open(get_heat_directory()+str(filename)+".json",'w') as fp:
    json.dump(data, fp)

'''
  Return True if written to file
  returns False if the race is incomplete
'''
def get_and_write_completed_heat(heatno, cached):
  data,complete,cached= get_heat(heatno, cached)
  if complete is True:
    write_heat_db(data, heatno)
    return True
  else:
    return False

def get_date(tree):
  if is_valid_heat(tree):
    return tree.xpath("//span[@id='lblDate']/text()")[0].encode('ascii','ignore')
  return None

def get_type(tree):
  if is_valid_heat(tree):
    return tree.xpath("//span[@id='lblRaceType']/text()")[0].encode('ascii','ignore')
  return None

'''goes + and - hint/2'''
def look_for_races(seed, hint):
  l = []
  ''' 0 not scheduled
      1 complete
      2 in progress '''
  complete = 0
  heatno = int(seed)
  heatno = heatno - (hint/2)
  for i in range(heatno, heatno+hint):
    url = get_url_heat(i)
    tree = get_tree(url)
    title = get_title() 
    if title == "Server Error":
      print "Server error: %s",(url)
      continue
    if is_heat_complete(tree) is True:
      complete = 1
    else:
      data = get_alllaps(tree)
      if len(data) == 0:
        complete = 0
      else:
        complete = 2
    date = get_date(tree)
    race_type = get_type(tree) 
    l.append((i,race_type,date,complete))

  return l

def get_heat(heatno, cached):
  if cached == True:
    data = get_heat_db(heatno)
    if data is not None:
      return data, True, True
  url = get_url_heat(heatno)
  race = {}
  racer = {}
  tree = get_tree(url)
  if not is_valid_heat(tree):
    raise Exception("Not Valid Heat Race")
  complete = is_heat_complete(tree)
  ''' Race still in progress. Giver partial info
      If data is [] then race not scheduled'''
  if complete is False:
    data = get_alllaps(tree)
    return data, False, False
  '''Complete race give the entire json'''
  race['date'] = get_date(tree)
  race['type'] = get_type(tree)
  race['details'] = []
  name = get_racername(tree)
  ids = get_id(tree)
  totlap = get_totallaps(tree)
  avglap = get_avglap(tree)
  bestlap = get_bestlap(tree)
  d = get_alllaps(tree)
  count = 0
  for i in name:
    racer['name'] = i
    racer['id'] = ids[count]
    racer['totlap'] = totlap[count]
    racer['avglap'] = avglap[count]
    racer['bestlap'] = bestlap[count]
    racer['alllaps'] = d[i]
    race['details'].append(racer)
    racer = {}
    count = count + 1
  return race, True, False

create_cust_directory()
data,cached = get_cust_heats(1038352,False)
write_cust_db(1038352, data)
create_heat_directory()
if data is not None:
  for i,j in data[1038352]:
    get_and_write_completed_heat(i, True)

#print data
#write_cust_db(1038352, data)
#populate_cust_db('.',1038352)
#print look_for_races('163952',10)
#create_heat_directory()
#get_and_write_completed_heat('.',163952)
#print get_heat(163952, True)
#print ""
#print get_heat(163952, False)

'''
s = ""
f = open('Desktop/clubspeed.html','r')
for i in f:
  s = s+i
url = get_url_heat(163952)
tree = get_tree(url)
#tree = html.fromstring(page.text)
print is_valid_heat(tree)
print is_heat_in_progress(tree)
print is_heat_complete(tree)
print get_alllaps(tree)
  '''
