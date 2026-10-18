import urllib.request,json,concurrent.futures
urls=['https://help.openai.com/en/articles/6825453-chatgpt-release-notes','https://learn.chatgpt.com/docs/changelog','https://openai.com/news/rss.xml','https://www.anthropic.com/news','https://deepmind.google/blog/rss.xml','https://huggingface.co/blog/feed.xml','https://blogs.nvidia.com/feed/','https://blogs.microsoft.com/ai/feed/','https://qwenlm.github.io/blog/']
def run(u):
 try:
  r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=30);b=r.read();p='data/source-'+str(urls.index(u))+'.txt';open(p,'wb').write(b);return [u,r.status,len(b),p]
 except Exception as e:return [u,str(e)]
with concurrent.futures.ThreadPoolExecutor(max_workers=9) as ex:
 for r in ex.map(run,urls):print(json.dumps(r))
