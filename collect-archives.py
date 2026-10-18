# -*- coding: utf-8 -*-
import urllib.request,concurrent.futures,json,xml.etree.ElementTree as E,gzip,re,hashlib
from pathlib import Path
from bs4 import BeautifulSoup
D=Path('data/archive-pages');D.mkdir(exist_ok=True)
def get(u):
 p=D/(hashlib.sha256(u.encode()).hexdigest()+'.html')
 if p.exists():return u,p.read_text(encoding='utf8')
 for attempt in range(3):
  try:
   b=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=35).read()
   if b[:2]==b'\x1f\x8b':b=gzip.decompress(b)
   t=b.decode('utf8');p.write_text(t,encoding='utf8');return u,t
  except Exception as e:
   if attempt==2:return u,None
urls=[]
s=E.parse('data/anthropic-map.txt').getroot()
urls += [x.text for x in s.iter() if x.tag.endswith('loc') and ('/news/' in x.text or '/research/' in x.text)]
b=Path('data/deepmind-map.txt').read_bytes();b=gzip.decompress(b) if b[:2]==b'\x1f\x8b' else b
s=E.fromstring(b);dm=[x.text for x in s.iter() if x.tag.endswith('loc')];print('deepmind map',len(dm),dm[:3],flush=True)
urls += [u for u in dm if '/blog/' in u]
urls += ['https://blogs.nvidia.com/feed/?paged='+str(i) for i in range(2,46)]
urls += ['https://qwenlm.github.io/blog/','https://qwen.ai/blog','https://blog.google/technology/ai/rss/?page='+str(2)]
urls += ['https://deepmind.google/sitemap.xml?type=blog'] if not any('/blog/' in x for x in dm) else []
print('fetch',len(urls),flush=True)
rows=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
 for i,(u,t) in enumerate(ex.map(get,urls)):
  rows.append({'url':u,'ok':t is not None})
  if i%40==0:print('fetched',i,flush=True)
Path('data/archive-fetch-report.json').write_text(json.dumps(rows),encoding='utf8')
print('done',len(rows),'failed',sum(not x['ok'] for x in rows),flush=True)
