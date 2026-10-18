# -*- coding: utf-8 -*-
import urllib.request,concurrent.futures,json
from pathlib import Path
urls={'deepmind-old':'https://deepmind.google/blog/rss.xml?page=2','nvidia-2':'https://blogs.nvidia.com/feed/?paged=2','anthropic-map':'https://www.anthropic.com/sitemap.xml','qwen-feed':'https://qwenlm.github.io/feed.xml','google-ai':'https://blog.google/technology/ai/rss/','microsoft-ai':'https://blogs.microsoft.com/blog/tag/ai/feed/','deepseek':'https://api.github.com/repos/deepseek-ai/DeepSeek-V3.2/contents/README.md','deepmind-map':'https://deepmind.google/sitemap.xml'}
def run(k):
 try:
  b=urllib.request.urlopen(urllib.request.Request(urls[k],headers={'User-Agent':'Mozilla/5.0'}),timeout=30).read();Path('data/'+k+'.txt').write_bytes(b);return [k,len(b)]
 except Exception as e:return [k,str(e)]
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
 for r in ex.map(run,urls):print(json.dumps(r),flush=True)
