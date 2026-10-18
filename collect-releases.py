# -*- coding: utf-8 -*-
import subprocess,json,concurrent.futures
from pathlib import Path
def gh(page):
 p=Path('data/codex-history-'+str(page)+'.json')
 for attempt in range(4):
  try:
   if p.exists():return json.loads(p.read_text(encoding='utf-8-sig'))
   r=subprocess.run(['gh','api','repos/openai/codex/releases?per_page=100&page='+str(page),'--jq','[.[]|{name,tag_name,html_url,published_at,prerelease,body}]'],capture_output=True,encoding='utf8',timeout=100)
   if r.returncode:raise Exception('gh request failed')
   rows=json.loads(r.stdout);p.write_text(json.dumps(rows,ensure_ascii=False),encoding='utf8');return rows
  except Exception as e:
   if attempt==3:raise
for start in range(6,24,3):
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex: pages=list(ex.map(gh,range(start,start+3)))
 print(start,'through',start+2,'oldest',min([r['published_at'] for page in pages for r in page]or['empty']),flush=True)
 if any(not p for p in pages) or min(r['published_at'] for p in pages for r in p)<'2025-09-01':break
