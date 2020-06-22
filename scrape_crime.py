from urllib.request import urlopen
import urllib
from bs4 import BeautifulSoup
import numpy as np
from datetime import datetime
import time
import pandas as pd
import pdb

def get_year(pd, d):
	if pd.month == 1 and d.month == 12:
		return pd.year - 1
	return pd.year

def fix_date(date_s):
	date_s = date_s.strip().replace(", 2018", "").split(", ")[-1].replace(".", "").replace("Sept", "Sep").replace("August", "Aug")
	date_s = date_s.replace("July", "Jul").replace("June", "Jun").replace("April", "Apr")
	return date_s.replace("March", "Mar").replace("September", "Sep").replace("Sepember", "Sep").strip()

def fix_time(time_s):
	time_s = time_s.strip().replace(".", "")
	if not time_s.endswith("m"):
		time_s = time_s + " am"
	return time_s

def is_date(d):
	try:
		datetime.strptime(fix_date(d), "%b %d")
		return True
	except:
		pass
	try:
		datetime.strptime(fix_date(d), "%B %d")
		return True
	except:
		return False

def get_date(d):
	try:
		d = datetime.strptime(fix_date(d), "%b %d")
		return d
	except:
		pass
	try:
		d = datetime.strptime(fix_date(d), "%B %d")
		return d
	except:
		return False

def get_time(par):
	try:
		t = datetime.strptime(par.strip().replace(".", ""), "%I:%M %p")
		return t
	except:
		pass
	try:
		t = datetime.strptime(par.strip().replace(".", ""), "%I %p")
		return t
	except:
		return False



data = []
for i in range(47):
	print("Total data at index {}: {}".format(i, len(data)))
	req = urllib.request.Request("https://huntnewsnu.com/category/crime-logs/page/{}/".format(i+1), headers={'User-Agent' : "Magic Browser"}) 
	top = BeautifulSoup(urlopen(req), 'html.parser')
	links  = top.find_all("a", {"class": "headline"})
	for link in links:
#         time.sleep(0.1)
		req_l = urllib.request.Request(link.attrs['href'], headers={'User-Agent' : "Magic Browser"}) 
		cl = BeautifulSoup(urlopen(req_l), 'html.parser')
		content = cl.find("span", {"class": "storycontent"}).find_all("p")
		if content[-1].text.startswith("Bikes stolen this semester"):
			print(content[-1].text)
			content = content[:-1]
		if content[0].text.startswith("Compiled by"):
			print(content[0].text)
			content = content[1:]
		if content[0].text.startswith("Entry of the week"):
			content = content[2:]
		
		content = [c for c in content if c.text.strip() != ""]
		pub_date = datetime.strptime(cl.find("span", {"class": "time-wrapper"}).text, "%B %d, %Y")
		if i < 17:
			groups = [index for index, x in enumerate(content) if x.find('b') != None and is_date(x.text)]
			for j in range(len(groups)):
				cur = content[groups[j]:groups[j+1]] if j < len(groups) - 1 else content[groups[j]:]
				date = datetime.strptime(fix_date(cur[0].text), "%b %d")
				date = date.replace(year=get_year(pub_date, date))
				cur = cur[1:]
				if len(cur) % 2 != 0:
					print("skipping")
					continue
				it = iter(cur)
				grouped = list(zip(it, it))
				for crime in grouped:
					try:
						c_time = datetime.strptime(fix_time(crime[0].text), "%I:%M %p").time()
					except:
						continue
					c_date = date.replace(minute=c_time.minute, hour=c_time.hour)
					log = crime[1].text

					data.append([log, c_date])
		elif i < 29:
			date = ""
			c_time = ""
			for par in content:
				if "\n" in par.text and i >= 21:
					try:
						psplit = par.text.split("\n")
						psplit = [x for x in psplit if x.strip() != ""]
						if len(psplit) == 3:
							date = datetime.strptime(fix_date(psplit[0]), "%b %d")
							date = date.replace(year=get_year(pub_date, date))
							psplit = psplit[1:]
						if get_time(psplit[0]) != False:
							c_time = get_time(psplit[0])
							c_date = date.replace(minute=c_time.minute, hour=c_time.hour)
							log = psplit[1]
							data.append([log, c_date])
					except Exception as e:
						# pdb.set_trace()
						pass
				elif get_date(par.text) != False:
					date = get_date(par.text)
					date = date.replace(year=get_year(pub_date, date))
				elif get_time(par.text) != False:
					c_time = get_time(par.text)
				else:
					if date != "" and c_time != "":
						try:
							c_date = date.replace(minute=c_time.minute, hour=c_time.hour)
							log = par.text
							data.append([log, c_date])
						except Exception as e:
							# pdb.set_trace()
							pass

		elif i < 32:
			date = ""
			c_time = ""
			for par in content:
				if get_date(par.text) != False:
					date = get_date(par.text)
					date = date.replace(year=get_year(pub_date, date))
				elif get_time(par.text) != False:
					c_time = get_time(par.text)
				else:
					if date != "" and c_time != "":
						try:
							c_date = date.replace(minute=c_time.minute, hour=c_time.hour)
							log = par.text
							data.append([log, c_date])
						except Exception as e:
							# pdb.set_trace()
							pass
		else:
			date = ""
			c_time = ""
			for par in content:
				tsplit = par.text.split(" ")
				if get_date(" ".join(tsplit[0:3])) != False:
					date = get_date(" ".join(tsplit[0:3]))
					date = date.replace(year=get_year(pub_date, date))
					tsplit = tsplit[3:]
				if get_time(" ".join(tsplit[0:2])) != False:
					c_time = get_time(" ".join(tsplit[0:2]))
					tsplit = tsplit[2:]
				if date != "" and c_time != "":
					try:
						c_date = date.replace(minute=c_time.minute, hour=c_time.hour)
						log = par.text
						data.append([log, c_date])
					except Exception as e:
						# pdb.set_trace()
						pass

dataf = pd.DataFrame(data, columns=["log", "date"])
dataf['year'] = dataf.date.apply(lambda d: d.year)
dataf.to_csv("crime_logs.csv")
