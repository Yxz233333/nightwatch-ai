# -*- coding: utf-8 -*-
import urllib.request,json,concurrent.futures
from pathlib import Path
urls={'deepseek-updates':'https://api-docs.deepseek.com/updates/','gemini-notes':'https://gemini.google/release-notes/','early-science':'https://openai.com/index/accelerating-science-gpt-5/','qwen-new':'https://qwen.ai/blog'}
def run(k):
 try:
  b=urllib.request.urlopen(urllib.request.Request(urls[k],headers={'User-Agent':'Mozilla/5.0'}),timeout=30).read();Path('data/'+k+'.html').write_bytes(b);return [k,len(b)]
 except Exception as e:return [k,str(e)]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
 for r in ex.map(run,urls):print(json.dumps(r))
