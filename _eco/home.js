/* Japan caller: shared search/URL policy, seasonal cards and browse facets. */
(()=>{'use strict';
const $=s=>document.querySelector(s),grid=$('#article-grid'),state=$('#feed-state'),status=$('#result-status'),pagination=$('#pagination'),category=document.body.dataset.category||'',U=EcoURL;
const original=grid.innerHTML,originalPagination=pagination.innerHTML,subtitleNode=$('#result-subtitle'),originalSubtitle=subtitleNode?.innerHTML;
const rawPage=document.body.dataset.page,page=/^[1-9]\d*$/.test(rawPage)&&Number.isSafeInteger(Number(rawPage))?Number(rawPage):1;
const labels={food:'食',see:'遊',play:'玩',move:'行',buy:'買',stay:'住',wellness:'身心','life-biz':'生活與商業'};
const icons={food:'food',see:'see',play:'play',move:'move',buy:'buy',stay:'stay',wellness:'well','life-biz':'biz'};
const regions=['','北海道','東北','關東','中部','近畿','中國','四國','九州沖繩'];
const cities=['','東京','大阪','金澤','福岡','京都','奈良','神戶','札幌','橫濱','臺東','高雄'];
const policy={lens:['','春','夏','秋','冬'],q:{max:200},cat:['',...Object.keys(labels)],city:cities,region:regions};
let ticket=0,selected='',currentQuery='',ready=false,taxonomy,search,restoringHash=false;
// Shared motion emits eco:lens on hashchange; the full hash belongs to restore().
window.addEventListener('hashchange',()=>{restoringHash=true;},true);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const svg=name=>'<svg class="i" aria-hidden="true"><use href="/_eco/icons.svg#i-'+name+'"></use></svg>';
const text=s=>esc(s).replace(/([ぁ-ゖァ-ヺー]+)/g,'<span lang="ja">$1</span>');
function setState(kind){state.hidden=kind==='ready';state.className=kind==='error'?'state err':kind==='empty'?'state empty':'';state.setAttribute('role',kind==='error'?'alert':'status');
if(kind==='loading')state.innerHTML='<p class="loading-note"><span class="spinner" aria-hidden="true"></span>整理讀物中…</p>';
if(kind==='error')state.innerHTML='<div><h3>讀物索引暫時用唔到</h3><p>預覽文章仍可閱讀。你可以重試，或使用分類連結。</p><button class="btn" id="feed-retry" type="button">再試一次</button></div>';
if(kind==='empty')state.innerHTML='<div><h3>條件太窄／本站冇</h3><p>試另一個字詞，或清除篩選。</p><button class="btn sec" id="feed-reset" type="button">清除篩選</button><a class="btn sec" href="https://world-encyclopedia.vercel.app/">去世界總圖</a></div>';
}
async function load(url){if(!/^\/idx\/(taxonomy\.json|page-[1-9]\d*\.json|c\/[\w-]+\/[1-9]\d*\.json|views\/(%[\dA-F]{2})+\.json|facets\/[\w-]+-\d\.json|clusters\/[1-9]\d*\.json)$/.test(url))throw Error('Index path');const r=await fetch(url,{redirect:'error'});if(!r.ok)throw Error('HTTP '+r.status);return r.json();}
function draw(rows){const seen=new Set(),ids=new Set();const html=rows.filter(a=>{const k=a.cluster_key;if(k&&seen.has(k)||ids.has(a.id))return false;if(k)seen.add(k);ids.add(a.id);return true;}).map(a=>{
const url=U.safePath(a.url);if(!url)throw Error('Article path');const level=['L1','L2','L3','L4'].includes(a.verification_record?.level)?a.verification_record.level:'L0';
const badge=level==='L0'?'':'<span class="trust" data-level="'+level+'">'+svg('shield')+level+'</span>';
const stack=a.cluster_count?'<span class="stack-tag">'+svg('stack')+'同題 '+a.cluster_count+' 篇</span>':'';
const body='<a class="card" data-id="'+a.id+'" href="'+esc(url)+'"><div class="card-top"><span class="cat"><span class="ico">'+svg(icons[a.cat]||'grid')+'</span>'+esc(labels[a.cat]||'其他')+'</span>'+stack+'</div><h3>'+text(a.title)+'</h3><div class="meta"><span>'+esc(a.city||'日本')+'</span><time datetime="'+esc(a.date)+'">'+esc(a.date)+'</time></div><div class="card-foot">'+badge+'</div></a>';
return '<div class="stackgroup"><div class="stackwrap">'+(a.cluster_count?'<span class="ly ly2" aria-hidden="true"></span><span class="ly ly1" aria-hidden="true"></span>':'')+body+'</div>'+(a.cluster_count?'<details class="cluster-details" data-cluster="'+a.cluster_key+'"><summary>展開同題 '+a.cluster_count+' 篇</summary><ul></ul></details>':'<div class="cluster-slot" aria-hidden="true"></div>')+'</div>';
}).join('');grid.innerHTML=html;}
function hash(values){const v=U.safeHash('#'+new URLSearchParams(values),policy);history.replaceState(null,'','#'+new URLSearchParams(Object.entries(v).filter(([,x])=>x)));return v;}
function seasonArt(value){document.documentElement.dataset.season=value||'秋';const rect=$('.season-mark rect');if(!rect)return;rect.setAttribute('fill',({'春':'#9A4A5C','夏':'#24476B','秋':'#A2462A','冬':'#4A5560'})[value]||'#A2462A');$('#season-book').textContent=(value?value+'季':'四季')+'讀本';$('#season-stamp').textContent=value||'季';}
function lens(value){selected=value;document.querySelectorAll('[data-lens]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.lens===value)));seasonArt(value);}
function subtitle(n,label){if(!subtitleNode)return;subtitleNode.innerHTML=esc(label)+' <span id="result-count">'+n.toLocaleString('en')+'</span> 篇（全站 <span id="site-total">'+taxonomy.total.toLocaleString('en')+'</span> 篇）';}
function show(rows,total,label,limited=false){draw(rows.slice(0,24));subtitle(total,label);$('#results').textContent=label;status.textContent=(limited?'有限搜尋結果，':'')+'共 '+total.toLocaleString('en')+' 篇'+(rows.length>24?'，同題合併後先列 24 張':'');pagination.hidden=true;setState(total?'ready':'empty');
if(rows.length>24){pagination.hidden=false;pagination.innerHTML='<button class="btn sec" id="season-more" type="button">更多讀物</button>';let shown=24;$('#season-more').onclick=()=>{shown+=24;draw(rows.slice(0,shown));if(shown>=rows.length)pagination.hidden=true;};}}
function markFacets(r){const nav=document.querySelector('.region-facets');if(!nav)return;if(!nav.querySelector('[data-region-all]'))nav.insertAdjacentHTML('afterbegin','<a class="fchip" data-region-facet="" data-region-all href="#region=">全部地方</a>');nav.querySelectorAll('[data-region-facet]').forEach(a=>a.setAttribute('aria-current',(a.dataset.regionFacet||'')===(r||'')?'true':'false'));}
async function apply(value='',query='',facet=null,region=''){markFacets(region);
value=U.safeHash('#lens='+encodeURIComponent(value),policy).lens;currentQuery=query;const n=++ticket;lens(value);setState('loading');grid.setAttribute('aria-busy','true');
try{if(!ready){const [t,p]=await Promise.all([load('/idx/taxonomy.json'),load('/idx/page-1.json')]);if(t.total!==p.total||t.total!==Object.values(t.counts).reduce((a,b)=>a+b,0))throw Error('Index mismatch');taxonomy=t;ready=true;}if(n!==ticket)return;
if(region){const data=await load('/idx/facets/'+(category||'all')+'-'+(regions.indexOf(region)-1)+'.json');if(n!==ticket)return;show(data.articles,data.total,region+' · '+(labels[category]||'全部'));}
else if(query){const result=await search.client.search(query,24);if(n!==ticket)return;if(result.state==='error')throw Error('Search unavailable');const rows=result.articles.filter(a=>!facet||(a.city===facet.city&&a.cat===facet.cat));show(rows,rows.length,facet?facet.city+' × '+labels[facet.cat]:'搜尋「'+query+'」',result.state==='partial');}
else if(value){const data=await load('/idx/views/'+encodeURIComponent(value)+'.json');if(!Array.isArray(data.articles)||data.total<data.articles.length)throw Error('Invalid season');if(n!==ticket)return;show(data.articles,data.total,value+'季讀物');}
else{const data=await load(category?'/idx/c/'+category+'/'+page+'.json':'/idx/page-'+page+'.json');if(n!==ticket)return;show(data.articles,data.total,'日本讀物 · '+(labels[category]||'全部'));pagination.innerHTML=originalPagination;pagination.hidden=false;status.textContent='第 '+page+' 頁，共 '+data.pages.toLocaleString('en')+' 頁';}
}catch(e){if(n!==ticket)return;grid.innerHTML=original;if(subtitleNode)subtitleNode.innerHTML=originalSubtitle;pagination.hidden=false;pagination.innerHTML=originalPagination;setState('error');status.textContent='索引載入失敗，保留預覽文章';console.error('Index unavailable:',e.message);}
finally{if(n===ticket)grid.removeAttribute('aria-busy');}}
grid.addEventListener('toggle',async e=>{const el=e.target;if(!el.matches('details[data-cluster]')||!el.open||el.dataset.loaded)return;const list=el.querySelector('ul');list.textContent='載入同題清單…';try{const data=await load('/idx/clusters/'+el.dataset.cluster+'.json');if(data.count!==data.articles.length)throw Error('Invalid cluster');const nodes=data.articles.map(a=>{const path=U.safePath(a.url);if(!path)throw Error('Article path');const li=document.createElement('li'),link=document.createElement('a');link.href=path;link.textContent=a.title;li.append(link);return li;});list.replaceChildren(...nodes);el.dataset.loaded='true';}catch{list.textContent='同題清單暫時載入唔到，關閉後再展開重試。';}},true);
function clear(){const v=hash({lens:''});$('#site-search').value='';apply(v.lens);}
search=EcoSearch.mount($('.search'),{prefetchPopular:true,onSubmit(query,facet){const v=hash({q:query,lens:'',...(facet?{city:facet.city,cat:facet.cat}:{})});apply('',v.q,facet);$('#results').focus();},onClear:clear});
document.addEventListener('eco:lens',e=>{if(restoringHash)return;const v=hash({lens:e.detail.value||''});apply(v.lens);});
document.addEventListener('click',e=>{const a=e.target.closest('[data-region-facet]');if(!a)return;e.preventDefault();const v=hash({region:a.dataset.regionFacet,lens:''});apply('','',null,v.region);$('#results').focus();});
state.addEventListener('click',e=>{if(e.target.id==='feed-retry'){ready=false;apply(selected,currentQuery);}if(e.target.id==='feed-reset')clear();});
function restore(){const raw=new URLSearchParams(location.hash.slice(1)),v=U.safeHash(location.hash,policy),query=U.safeHash(location.search,{q:{max:200}}).q;const month=+new Intl.DateTimeFormat('en',{timeZone:'Asia/Tokyo',month:'numeric'}).format(new Date()),def=category||document.body.dataset.page!=='1'?'':month>=3&&month<=5?'春':month>=6&&month<=8?'夏':month>=9&&month<=11?'秋':'冬';if(!raw.has('lens')&&!v.q&&!v.region&&!query)v.lens=def;v.q=v.q||query;hash(v);$('#site-search').value=v.q;apply(v.lens,v.q,v.city&&v.cat?{city:v.city,cat:v.cat}:null,v.region);}
function openTrust(){const el=document.getElementById('trust-info');if(el?.tagName==='DETAILS')el.open=true;}
document.addEventListener('click',e=>{if(e.target.closest('.trust-note a')?.getAttribute('href')==='#trust-info')openTrust();});
window.addEventListener('hashchange',()=>{try{if(location.hash==='#trust-info')openTrust();else restore();}finally{restoringHash=false;}});if(location.hash==='#trust-info')openTrust();restore();
})();
