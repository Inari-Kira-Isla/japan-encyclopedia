"""Offline, deterministic v2 renderer. No DB / network / live script mutations.
Run from the site root after refreshing the approved F2 index pack.
"""
from pathlib import Path
import html,json,math,re,sys
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
H=lambda x:html.escape(str(x),quote=True)
def text(x):return re.sub(r'([ぁ-ゖァ-ヺー]+)', r'<span lang="ja">\1</span>', H(x))
LABELS={'food':'食','stay':'住','move':'行','see':'遊','buy':'買','play':'玩','wellness':'身心','life-biz':'生活與商業'}
ICONS={'food':'food','stay':'stay','move':'move','see':'see','buy':'buy','play':'play','wellness':'well','life-biz':'biz'}

def icon(name):return f'<svg class="i" aria-hidden="true"><use href="/_eco/icons.svg#i-{name}"></use></svg>'
SEASON_WORDS={'春':['春季','春天','櫻花','賞櫻'],'夏':['夏季','夏天','花火','煙火','薰衣草'],'秋':['秋季','秋天','紅葉','賞楓'],'冬':['冬季','冬天','滑雪','雪祭']}
REGIONS={'北海道':['札幌'],'東北':[],'關東':['東京','橫濱'],'中部':['金澤'],'近畿':['大阪','京都','奈良','神戶'],'中國':[],'四國':[],'九州沖繩':['福岡']}
def default_season():
 month=datetime.now(ZoneInfo('Asia/Tokyo')).month
 return '春' if 3<=month<=5 else '夏' if 6<=month<=8 else '秋' if 9<=month<=11 else '冬'
def safe_path(url):
 path=urlsplit(url).path
 if not path.startswith('/articles/') or any(x in ('.','..') for x in path.split('/')):raise ValueError('BLOCKED: article path')
 return path

def unique_cards(rows,mapping):
 # Cluster first, then id: the selected representative need not itself match the lens.
 output=[];clusters=set();ids=set()
 for a in rows:
  group=mapping.get(a['id']);key=group['representative_id'] if group else None
  if key is not None and key in clusters:continue
  if group:
   clusters.add(key);a=group['members'][key]
  if a['id'] in ids:continue
  ids.add(a['id']);output.append(dict(a,cluster_key=key,cluster_count=group['count'] if group else 0))
 return output

def season_data(root,season):
 taxonomy,first,cats,mapping,all_rows=inputs(root)
 matches=[a for a in all_rows if any(w in a['title'] for w in SEASON_WORDS[season])]
 return {'total':len(matches),'counts':{c['id']:sum(a['cat']==c['id'] for a in matches) for c in cats},'articles':unique_cards(matches,mapping),'rule':SEASON_WORDS[season]}

def clean_archive(raw):
 # Remove the invalid trend card in the display archive; JSON-LD is separate.
 pattern=r'<div class="trend-item">(?:(?!<div class="trend-item">).)*?<h3 class="trend-title">時間範圍無法確認</h3>.*?</div>'
 return re.sub(pattern,'',raw,flags=re.S)

def card(a,cluster=None):
 # F2 level, dates, quality and sources are never evidence of verification.
 record=a.get('verification_record');level=record.get('level','L0') if isinstance(record,dict) else 'L0'
 level=level if level in ('L0','L1','L2','L3','L4') else 'L0'
 labels={'L0':'未有來源','L1':'有引用','L2':'來源可追溯','L3':'人工核實','L4':'官方紀錄'}
 url=safe_path(a['url'])
 badge=f'<span class="trust" data-level="{level}">{icon("shield")}{level} {labels[level]}</span>' if level!='L0' else ''
 tag=f'<span class="stack-tag">{icon("stack")}同題 {cluster["count"]} 篇</span>' if cluster else ''
 body=f'''<a class="card" href="{H(url)}" data-id="{a['id']}"><div class="card-top"><span class="cat"><span class="ico">{icon(ICONS.get(a['cat'],'grid'))}</span>{LABELS.get(a['cat'],'其他')}</span>{tag}</div><h3>{text(a['title'])}</h3><div class="meta"><span>{H(a['city'] or '日本')}</span><time datetime="{H(a['date'])}">{H(a['date'])}</time></div><div class="card-foot">{badge}</div></a>'''
 return f'<div class="stackgroup"><div class="stackwrap"><span class="ly ly2" aria-hidden="true"></span><span class="ly ly1" aria-hidden="true"></span>{body}</div><details class="cluster-details"><summary>展開同題 {cluster["count"]} 篇</summary><ul>'+''.join(f'<li><a href="{H(safe_path(cluster['members'][i]["url"]))}">{H(cluster['members'][i]["title"])}</a></li>' for i in cluster['article_ids'])+'</ul></details></div>' if cluster else f'<div class="stackgroup"><div class="stackwrap">{body}</div><div class="cluster-slot" aria-hidden="true"></div></div>'

from functools import lru_cache
@lru_cache(maxsize=1)
def inputs(root):
 taxonomy=json.loads((root/'idx/taxonomy.json').read_text());first=json.loads((root/'idx/page-1.json').read_text())
 cats=sorted(taxonomy['categories'],key=lambda c:['food','see','play','move','buy','stay','wellness','life-biz'].index(c['id']));clusters=json.loads((root/'idx/clusters.json').read_text())['clusters'];byid={};mapping={}
 for p in (root/'idx/c').glob('*/*.json'):
  for a in json.loads(p.read_text())['articles']:byid[a['id']]=a
 if len(byid)!=taxonomy['total'] or sum(taxonomy['counts'].values())!=len(byid):raise RuntimeError('BLOCKED: index/taxonomy mismatch')
 for c in clusters:
  c['members']={i:byid[i] for i in c['article_ids']}
  for i in c['article_ids']:mapping[i]=c
 all_rows=sorted(byid.values(),key=lambda a:a['id'])
 return taxonomy,first,cats,mapping,all_rows

def render(root=ROOT,category=None,page=1):
 taxonomy,first,cats,mapping,all_rows=inputs(root)
 season=default_season() if not category and page==1 else ''
 if category:
  data=json.loads((root/f'idx/c/{category}/{page}.json').read_text());rows=data['articles'];total=data['total'];pages=data['pages'];title=LABELS[category]
 else:
  rows=first['articles'] if page==1 else all_rows[(page-1)*24:page*24];total=taxonomy['total'];pages=math.ceil(total/24);title='全部'
 if season:
  data=season_data(root,season);rows=data['articles'][:24];total=data['total']
 head=(root/'_eco/home-head.html').read_text()
 if category or page>1:
  path=f'/c/{category}/{page}/' if category else f'/p/{page}/';base='https://japan-encyclopedia.vercel.app'
  head=re.sub(r'<link rel="canonical"[^>]*>',f'<link rel="canonical" href="{base+path}" />',head)
  # New browsing URLs have their own metadata and do not reuse homepage JSON-LD.
  head=re.sub(r'<script type="application/ld\+json">.*?</script>','',head,flags=re.S)
  head=head.replace('<title>','<title>'+title+' · 第 '+str(page)+' 頁 | ')
  head=re.sub(r'<meta property="og:url"[^>]*>',f'<meta property="og:url" content="{base+path}" />',head)
 # Static assets use one render-blocking CSS, no runtime import.
 head+='\n<link rel="stylesheet" href="/_eco/home.css" />\n<script src="/_eco/eco-url.js" defer></script>\n<script src="/_eco/eco-motion.js" defer></script>\n<script src="/_eco/eco-shell.js" defer></script>\n<script src="/_eco/eco-search.js" defer></script>\n<script src="/_eco/home.js" defer></script>\n</head>'
 eco=json.loads((root/'_eco/ecosystem.json').read_text())
 doors=''.join(f'<a class="door" href="{H(s["url"])}" data-door="{s["id"]}"'+(' aria-current="page"' if s['id']=='japan' else '')+f'>{H(s["short"])}</a>' for s in eco)
 nav=''.join(f'<a href="/c/{c["id"]}/1/">{icon(ICONS[c["id"]])}{c["label"]}</a>' for c in cats if c['count']>=30)
 filters=f'<a class="fchip" href="/#results"'+(' aria-current="page"' if not category else '')+f'>全部 <span class="n">{taxonomy["total"]:,}</span></a>'
 filters+=''.join(f'<a class="fchip" href="/c/{c["id"]}/1/"'+(' aria-current="page"' if category==c['id'] else '')+f'>{icon(ICONS[c["id"]])}{c["label"]}<span class="n">{c["count"]:,}</span></a>' for c in cats if c['count']>=30)
 more=''.join(f'<a class="fchip" href="/c/{c["id"]}/1/">{c["label"]} {c["count"]}</a>' for c in cats if c['count']<30)
 filters+=f'<details><summary class="fchip more">更多</summary><div class="more-cats">{more}</div></details>'
 lens=''.join(f'<button class="lens-chip" type="button" data-lens="{s}" aria-pressed="{str(s==season).lower()}">{s}<small>{m}</small></button>' for s,m in [('春','3–5月'),('夏','6–8月'),('秋','9–11月'),('冬','12–2月')])
 links=[]
 for n in sorted(set([1,page-1,page,page+1,pages])):
  if 1<=n<=pages:
   url=f'/c/{category}/{n}/' if category else '/' if n==1 else f'/p/{n}/'
   links.append(f'<a class="btn sec" href="{url}"'+(' aria-current="page"' if n==page else '')+f'>{n}</a>')
 cards='\n'.join(card(a,mapping.get(a['id'])) for a in rows)
 archive='<template id="legacy-dynamic">'+clean_archive((root/'_eco/legacy-dynamic.html').read_text())+'</template>' if not category and page==1 else ''
 faq=''
 if not category and page==1:
  for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>',head,re.S):
   for g in json.loads(raw).get('@graph',[]):
    if g.get('@type')=='FAQPage':
     faq='<section class="faq-section" aria-label="常見問題"><h2>常見問題</h2>'+''.join(f'<details class="faq-item"><summary>{H(x["name"])}</summary><p>{H(x["acceptedAnswer"]["text"])}</p></details>' for x in g['mainEntity'])+'</section>'
 covers=''.join(f'<a class="cover" href="/c/{cat}/1/"><picture><source type="image/avif" srcset="/_eco/img/cover-{cat}-800.avif"><img src="/_eco/img/cover-{cat}-800.webp" width="800" height="450" loading="lazy" alt="{alt}"></picture><span>{label}</span><small>AI 氛圍插畫，非實景</small></a>' for cat,label,alt in [('food','食 · 季節之味','木枱上的串燒長碟、靛藍陶碗與一片秋葉。'),('see','遊 · 慢讀風景','庭園步道的季節氛圍插畫。'),('move','行 · 城市之間','暮色中的鄉郊月台，一列短火車停在暖燈旁。')])
 ecobar=(root/'_eco/partials/ecobar.html').read_text();bottomnav=(root/('_eco/partials/bottomnav-categories.html' if category else '_eco/partials/bottomnav.html')).read_text()
 trust_note='<p class="trust-note"><a href="#trust-info">本站文章暫時未有核實紀錄</a></p>'
 search=f'<div class="search" data-index="/idx/"><label class="sr" for="site-search">搜尋日本百科文章</label><div class="search-field">{icon("search")}<input id="site-search" type="search" autocomplete="off" placeholder="搜尋 {taxonomy["total"]:,} 篇，例如大阪 晚餐"><kbd>/</kbd><button class="search-go" type="button">搜尋</button></div></div>'
 facets=''.join(f'<a class="fchip" data-region-facet="{H(region)}" href="#region={H(region)}">{H(region)}</a>' for region in REGIONS)
 small=f'<header class="browse-header wrap"><nav aria-label="麵包屑"><a href="/">首頁</a> / {title}</nav><h1>{title} · {total:,} 篇</h1>{trust_note}<nav class="region-facets" aria-label="八地方 facet">{facets}</nav>{search}</header>'
 subtitle=f'{season}季讀物 <span id="result-count">{total:,}</span> 篇（全站 <span id="site-total">{taxonomy["total"]:,}</span> 篇）' if season else f'<span id="result-count">{total:,}</span> 篇讀物（全站 <span id="site-total">{taxonomy["total"]:,}</span> 篇）'
 result_subtitle='' if category else f'<p id="result-subtitle">{subtitle}</p>'
 result_heading=f'<div class="sec-head"><div><h2 id="results" tabindex="-1">{season+"季讀物" if season else "日本讀物 · "+title}</h2>{result_subtitle}</div>'
 result_status=f'<p id="result-status" role="status">{str(total)+" 篇季節讀物，同題合併後先列 24 張" if season else "第 "+str(page)+" 頁，共 "+format(pages,",")+" 頁"}</p>'
 result_heading+=('</div>'+result_status) if category else (result_status+'</div>')
 filter_note='以下分類數字係全站；地方按索引城市欄整理，未有城市資料嘅文章未歸入地方。' if category else '以下分類數字係全站'
 season_note='' if category else '<p class="note" id="season-rule">季節讀物只按標題明示嘅季節詞整理；日期、文章評分唔代表核實。</p>'
 entry=f'''<section class="stage" aria-labelledby="stage-title" data-play><div class="wrap"><div class="stage-copy"><p class="eyebrow">JAPAN · 日本</p><h1 id="stage-title"><span class="ln">跟住季節，</span><span class="ln">慢慢讀日本。</span></h1><p class="lede">美食、寺社、住宿、交通——先排今季嘅讀物。</p><div class="search" data-index="/idx/"><label class="sr" for="site-search">搜尋日本百科文章</label><div class="search-field">{icon('search')}<input id="site-search" type="search" autocomplete="off" placeholder="搜尋 {taxonomy['total']:,} 篇，例如金澤 燒鳥"><kbd>/</kbd><button class="search-go" type="button">搜尋</button></div></div>{trust_note}<div class="lens"><p class="lens-label">季節（按日本今日日期自動選定，可改）</p><div class="lens-row" role="group" aria-label="季節">{lens}</div></div></div><div class="art" aria-hidden="true"><div class="art-japan">{(root/'_eco/stage-japan.svg').read_text()}</div></div></div></section>''' if not category and page==1 else small
 return head+f'''\n<body data-eco-v2 data-category="{category or ''}" data-page="{page}" data-season="{season}">
<a class="skip" href="#results">跳到文章</a>
{ecobar}
<div class="site-head" role="region" aria-label="日本百科"><div class="wrap"><a class="wordmark" href="/"><strong>日本百科</strong><small>Japan</small></a><nav class="catnav" aria-label="主要分類">{nav}</nav></div></div>
{entry}
<main><div class="wrap">{result_heading}<p class="note">{filter_note}</p><nav class="filters" id="filters" aria-label="文章分類">{filters}</nav><div id="feed-state" hidden></div><div class="grid" id="article-grid">{cards}</div><nav id="pagination" class="pagination" aria-label="分頁">{''.join(links)}</nav>{season_note}<section class="region-index" id="trust-info"><h2>資料同來源</h2><dl><dt>L0 · 未有來源</dt><dd>未有核實紀錄；請以原文來源查證。</dd><dt>L1 · 有引用</dt><dd>文章提供引用，未等於已核實。</dd><dt>L2 · 來源可追溯</dt><dd>記錄可追溯來源。</dd><dt>L3 · 人工核實</dt><dd>有人工核實紀錄。</dd><dt>L4 · 官方紀錄</dt><dd>有官方紀錄支持。</dd></dl></section><section class="region-index"><h2>八地方 · 文字索引</h2><p>北海道 · 東北 · 關東 · 中部 · 近畿 · 中國 · 四國 · 九州與沖繩</p><p>由搜尋輸入地方或城市名稱，揀選讀物。</p></section><section class="covers" aria-label="分類讀本">{covers}</section>{faq}{archive}</div></main>
<footer class="ecosystem-footer"><div class="wrap"><h2>一本索引，六道門</h2><nav class="footer-links" aria-label="生態系六站">{doors}</nav><p><a href="/llms.txt">LLMs.txt</a> · <a href="/sitemap.xml">網站地圖</a> · <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a></p><p>文章原稿未有核實紀錄時標記 L0，請以原文來源查證。</p></div></footer>
{bottomnav}</body></html>'''

def write_views(root):
 taxonomy,first,cats,mapping,all_rows=inputs(root)
 views=root/'idx/views';views.mkdir(exist_ok=True)
 directory=root/'idx/clusters';directory.mkdir(exist_ok=True)
 for group in {c['representative_id']:c for c in mapping.values()}.values():
  (directory/f'{group["representative_id"]}.json').write_text(json.dumps({'count':group['count'],'articles':list(group['members'].values())},ensure_ascii=False,separators=(',',':')))
 for season in SEASON_WORDS:
  (views/f'{season}.json').write_text(json.dumps(season_data(root,season),ensure_ascii=False,separators=(',',':')))
 # Facets derive only from explicit structured city/category fields.
 facets=root/'idx/facets';facets.mkdir(exist_ok=True)
 for category in [None]+[c['id'] for c in cats]:
  for n,(region,cities) in enumerate(REGIONS.items()):
   matches=[a for a in all_rows if a['city'] in cities and (not category or a['cat']==category)]
   (facets/f'{category or "all"}-{n}.json').write_text(json.dumps({'total':len(matches),'articles':unique_cards(matches,mapping)},ensure_ascii=False,separators=(',',':')))

def build(root=ROOT):
 root=Path(root)
 inputs.cache_clear()
 write_views(root)
 (root/'_eco/home.css').write_text('\n'.join((root/'_eco'/n).read_text() for n in ['eco-core.css','eco-region-japan.css','home-extra.css']))
 rc=re.sub(r'(?<!\.portal)\[data-region=japan\](\s+)?',lambda m:'' if m[1] else ':root',(root/'_eco/eco-region-japan.css').read_text())
 (root/'article-style.css').write_text((root/'_eco/eco-core.css').read_text()+'\n'+rc+'\n'+(root/'_eco/legacy-bridge.css').read_text())
 # Run once, then reuse render's index input for each static browsing page.
 (root/'index.html').write_text(render(root))
 cats=json.loads((root/'idx/taxonomy.json').read_text())['categories']
 # Rendering every page using the same in-memory function avoids all-JSON rereads.
 for cat in cats:
  for source in sorted((root/'idx/c'/cat['id']).glob('*.json')):
   n=int(source.stem);out=root/f'c/{cat["id"]}/{n}/index.html';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(render(root,cat['id'],n))
 for n in range(2,math.ceil(json.loads((root/'idx/taxonomy.json').read_text())['total']/24)+1):
  out=root/f'p/{n}/index.html';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(render(root,None,n))
 print('v2 homepage and static category / all-pages built')
if __name__=='__main__':
 # Category pagination is generated by fast_build.py, with the same renderer.
 build()
