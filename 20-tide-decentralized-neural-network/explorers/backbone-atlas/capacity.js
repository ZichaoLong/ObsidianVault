'use strict';
// All values come from the same Python inventory as the downloadable CSV.
const cap=ATLAS.capacity;
const capRows=cap.rows.map(values=>Object.fromEntries(cap.fields.map((key,i)=>[key,values[i]])));
const capFamilies={fc:'FC',lattice:'HB-Lattice',exchange:'HB-Exchange',multiscale:'HB-Multiscale · Timed / Settle'};
const capNumber=x=>(x/1e6).toLocaleString('zh-CN',{minimumFractionDigits:2,maximumFractionDigits:3});
const capGraph=new Map(Object.values(ATLAS.cases).map(c=>[`${c.profile}/${c.ordinary}/${c.hubs}`,c.key]));
function capacityProfiles(preferred='all'){
 const family=$('#cap-family').value;
 $('#cap-profile').innerHTML=option('all','全部轮廓')+Object.values(cap.profiles).filter(p=>family==='all'||p.family===family).map(p=>option(p.key,p.label)).join('');
 $('#cap-profile').value=[...$('#cap-profile').options].some(o=>o.value===preferred)?preferred:'all';
 const canHub=!['fc','lattice'].includes(family);
 $('#cap-h').disabled=!canHub;if(!canHub)$('#cap-h').value='0';
 capacityMemory();
}
function capacityMemory(){
 const old=$('#cap-memory').value,h=+$('#cap-h').value;
 $('#cap-memory').innerHTML=option('K','K · 全 KV')+option('S','S · 全 SSD')+(h?option('X','X · 普通 KV / hub SSD'):'');
 $('#cap-memory').value=h&&old==='X'?'X':old==='S'?'S':'K';
}
function capacityBudgets(){
 const n=+$('#cap-n').value,previous=$('#cap-k').value;
 const ks=cap.budgets.filter(k=>k<=n);
 $('#cap-k').innerHTML=ks.map(k=>option(k,`k=${k} · ${100*k/n}%`)).join('')+option('pool','pool · 稠密对照');
 $('#cap-k').value=previous==='pool'||ks.includes(+previous)?previous:'1';
}
function renderCapacity(){
 const n=+$('#cap-n').value,h=+$('#cap-h').value,d=$('#cap-d').value;
 const share=$('#cap-sharing').value,rank=share==='shared'?+$('#cap-rank').value:0;
 $('#cap-rank').disabled=share!=='shared';
 const k=$('#cap-k').value,ratio=k==='pool'?1:+k/n;
 const family=$('#cap-family').value,profile=$('#cap-profile').value,memory=$('#cap-memory').value;
 const limit=$('#cap-limit').value==='256'?256e6:Infinity;
 const rows=capRows.filter(r=>r.n===n&&r.h===h&&r.memory===memory&&r.sharing===share&&r.rank===rank&&
  (d==='all'||r.d===+d)&&(family==='all'||cap.profiles[r.profile].family===family)&&
  (profile==='all'||r.profile===profile)&&r.total<=limit).sort((a,b)=>a.total-b.total||a.profile.localeCompare(b.profile));
 $('#capacity-summary').textContent=`${rows.length} 个配置 · 每普通区 ${n} 节点 · ${k==='pool'?'pool 稠密对照':`k=${k}，预算比例 ${100*ratio}%`} · ${share}${rank?`，适配秩 ${rank}`:''}。以下单位为百万参数（M）。`;
 $('#capacity-formula').innerHTML=mathBlock(sub(mi('P'),textMath('总'))+mo('=')+mi('B')+mo('+')+sub(mi('P'),mi('D'))+mo('+')+sub(mi('P'),mi('H')))+
  mathBlock(sub(mi('P'),textMath('活跃代理'))+mo('=')+mi('B')+mo('+')+mn(ratio)+sub(mi('P'),mi('D'))+mo('+')+sub(mi('P'),mi('H')));
 let table='<thead><tr><th>空间图</th><th>层数</th><th>d</th><th>D / H 节点</th><th>总参数 M</th><th>活跃代理 M</th><th>代理 / 总参数</th><th>连接</th></tr></thead><tbody>';
 for(const r of rows){
  const p=cap.profiles[r.profile],a=r.base+ratio*r.D+r.H,graph=capGraph.get(`${r.profile}/${n}/${h}`);
  table+=`<tr data-profile="${E(r.profile)}" data-d="${r.d}" data-total="${r.total}" data-active="${a}"><td>${E(p.label)}</td><td>${p.depth}</td><td>${r.d}</td><td>${r.nodes_D} / ${r.nodes_H}</td><td>${capNumber(r.total)}</td><td>${capNumber(a)}</td><td>${(100*a/r.total).toFixed(2)}%</td><td>${graph?`<button data-cap-case="${E(graph)}">查看</button>`:'—'}</td></tr>`;
 }
 $('#capacity-table').innerHTML=table+'</tbody>';
}
$('#cap-family').innerHTML=option('all','全部空间图')+Object.entries(capFamilies).map(([key,label])=>option(key,label)).join('');
$('#cap-n').innerHTML=cap.node_sizes.map(n=>option(n)).join('');$('#cap-n').value='32';
$('#cap-d').innerHTML=option('all','全部维度')+cap.dimensions.map(d=>option(d)).join('');
$('#cap-family').addEventListener('change',()=>{capacityProfiles();renderCapacity();});
$('#cap-n').addEventListener('change',()=>{capacityBudgets();renderCapacity();});
$('#cap-h').addEventListener('change',()=>{capacityMemory();renderCapacity();});
for(const name of ['profile','d','memory','sharing','rank','k','limit'])$('#cap-'+name).addEventListener('change',renderCapacity);
$('#cap-use-graph').addEventListener('click',()=>{
 $('#cap-family').value=current.family;capacityProfiles(current.profile);
 $('#cap-n').value=current.ordinary;$('#cap-h').value=current.hubs;capacityMemory();capacityBudgets();renderCapacity();
});
$('#capacity-table').addEventListener('click',e=>{const button=e.target.closest('[data-cap-case]');if(button){mountCase(button.dataset.capCase);$('#regions').scrollIntoView({behavior:'smooth'});}});
capacityProfiles();capacityBudgets();renderCapacity();
window.atlasCapacityDebug={renderCapacity,budgets:capacityBudgets};
