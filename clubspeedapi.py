import requests
from lxml import html
import json

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

''' No Such URL exist'''
def is_valid_heat(tree):
  title = tree.xpath("//title/text()")[0]
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
def get_file_db(directory, filename):
  data = {}
  try:
    with open(director+"/"+filename,'r') as fp:
      data = json.load(fp)
  except IOError:
    return None
  return data

def write_file_db(data, directory, filename):
  with open(director+"/"+filename,'w') as fp:
    json.dump(data, fp)

'''
  Return True if written to file
  returns False if the race is incomplete
'''
def get_and_write_completed_heat(directory, heatno):
  data,complete = get_heat(directory, heatno)
  if complete is True:
    write_file_db(data, directory, heatno)
    return True
  else:
    return False

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
    title = tree.xpath("//title/text()")[0]
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
    date = tree.xpath("//span[@id='lblDate']/text()")
    race_type = tree.xpath("//span[@id='lblRaceType']/text()")
    l.append((i,race_type,date,complete))
  
  return l

def get_heat(directory, heatno):
  url = get_url_heat(heatno)
  race = []
  racer = {}
  tree = get_tree(url)
  title = tree.xpath("//title/text()")[0]
  if title == "Server Error":
    print "Server Error"
    return None, None
  complete = is_heat_complete(tree)
  ''' Race still in progress. Giver partial info
      If data is [] then race not scheduled'''
  if complete is False:
    data = get_alllaps(tree)
    return data, False
  '''Complete race give the entire json'''
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
    race.append(racer)
    racer = {}
    count = count + 1
  return race, True

#populate_cust_db('.',1038352)
#print look_for_races('163952',10)
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
