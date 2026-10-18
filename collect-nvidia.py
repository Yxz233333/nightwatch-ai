# -*- coding: utf-8 -*-
import urllib.request,concurrent.futures,hashlib,xml.etree.ElementTree as E,json
from pathlib import Path
from email.utils import parsedate_to_datetime
D=Path('data/archive-pages')
def run(i):
 u='https://blogs.nvidia.com/feed/?paged='+str(i);p=D/(hashlib.sha256(u.encode()).hexdigest()+'.html')
 for attempt in range(3):
  try:
   if p.exists():b=p.read_bytes()
   else:b=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=30).read();p.write_bytes(b)
   items=E.fromstring(b).findall('.//item'); dates=[parsedate_to_datetime(x.findtext('pubDate')).date().isoformat() for x in items];return [i,min(dates) if dates else 'empty']
  except Exception as e:
   if attempt==2:return [i,'failed']
for start in range(46,161,10):
 with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:rs=list(ex.map(run,range(start,min(start+10,161))))
 print(json.dumps(rs),flush=True)
 dates=[x[1] for x in rs if x[1] not in ['failed','empty']]
 if dates and min(dates)<'2025-09-01':break
