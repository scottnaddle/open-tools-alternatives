(()=>{const q=document.getElementById('hq'),ac=document.getElementById('ac');
if(q){q.addEventListener('input',()=>{const v=q.value.trim().toLowerCase();if(!v){ac.hidden=true;return}
const r=SEARCH.filter(a=>(a.name+' '+a.alts.join(' ')).toLowerCase().includes(v)).slice(0,6);
ac.innerHTML=r.length?r.map(a=>`<li><a href="${a.id==='capcut'?'app-capcut.html':'index.html#app-'+a.id}">${a.name} 대신<small>${a.alts.join(', ')}</small></a></li>`).join(''):'<li><a href="suggest.html">찾는 앱이 없어요. 대안을 요청해 주세요</a></li>';ac.hidden=false})}
const s=document.getElementById('sortSel');if(s)s.addEventListener('change',()=>{const box=document.getElementById('alts');const c=[...box.children];
const k={lv:x=>+x.dataset.lv*10+ +x.dataset.df,df:x=>+x.dataset.df,act:x=>-Date.parse(x.dataset.act)}[s.value];c.sort((a,b)=>k(a)-k(b)).forEach(x=>box.appendChild(x))});
const b=document.getElementById('askBtn'),p=document.getElementById('askPanel'),c=document.getElementById('askClose');
const t=o=>{p.hidden=!o;b.setAttribute('aria-expanded',o)};b.onclick=()=>t(p.hidden);c.onclick=()=>t(false);})();
