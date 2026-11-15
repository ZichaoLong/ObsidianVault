'use strict';
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const E=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const kinds=ATLAS.kinds, colors=ATLAS.colors;
const order=['5','5-dd4','7','9','13','15','17'];
let current, outs, ins, ids;
const state={key:'9',focus:[4,3],role:'d',index:0,scope:'near',source:'3,2',target:'4,2'};
const pos=n=>`${n[0]},${n[1]}`;
const nodeName=n=>`${n[2].toUpperCase()}(${n[0]},${n[1]}; ${n[3]})`;
const option=(v,label)=>`<option value="${E(v)}">${E(label===undefined?v:label)}</option>`;
const family=k=>k.startsWith('HH')?'HH':k.startsWith('HD')?'HD':k;
function svgText(x,y,t,size=16,color='#23344b',weight=400,anchor='start',attrs=''){
 return `<text x="${x}" y="${y}" font-family="Noto Sans CJK SC,Droid Sans,Microsoft YaHei,sans-serif" font-size="${size}" fill="${color}" font-weight="${weight}" text-anchor="${anchor}" ${attrs}>${E(t)}</text>`;
}
function svgStart(w,h,label){return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" role="img" aria-label="${E(label)}"><rect width="100%" height="100%" fill="white"/>`;}
function mountCase(key){
 state.key=key;current=ATLAS.cases[key];
 outs=current.nodes.map(()=>[]);ins=current.nodes.map(()=>[]);ids=new Map();
 current.nodes.forEach((n,u)=>ids.set(n.join(','),u));
 current.edges.forEach(([u,v,k])=>{outs[u].push([v,k]);ins[v].push([u,k]);});
 const n=current.nodes[current.selected_d];state.focus=n.slice(0,2);state.role=n[2];state.index=n[3];
 $('#case-select').value=key;
 $('#metrics').innerHTML=`<span><b>${current.depth}</b>层</span><span><b>${current.stats.positions}</b>位置</span><span><b>${current.stats.regions}</b>区域</span><span><b>${current.stats.nodes.toLocaleString()}</b>节点</span><span><b>${current.stats.edges.toLocaleString()}</b>消息边</span>`;
 const ds=current.stats.ordinary_delays;
 $('#case-note').textContent=`普通路径总时延 ${ds.join('、')}；输入周期 T=4。`+(current.add_dd4?'此候选新增普通节点跨度 4 的固定置换边。':current.depth===5?'原连接的 5 层版本缺少普通路径相位 1，保留作浅层对照。':'全部末端普通节点均覆盖四个相位；来源混合程度见下表。');
 $('#dd4-label').hidden=!current.add_dd4;
 $('#region-canvas').innerHTML=current.svg;
 const positions=[];current.widths.forEach((w,l)=>{if(l<current.depth-1)for(let p=0;p<w;p++)positions.push(`${l},${p}`);});
 $('#pair-source').innerHTML=positions.map(p=>option(p,`(${p})`)).join('');
 const sl=Math.max(0,Math.floor(current.depth/2)-1),tl=Math.floor(current.depth/2);
 state.source=`${sl},2`;
 $('#pair-source').value=state.source;
 const sw=current.widths[sl],tw=current.widths[tl],base=tw>=sw?2*(tw/sw):Math.floor(2/(sw/tw));
 updateTargets(`${tl},${base}`);
 syncNodeControls();renderNode();paintRegion();renderDepthTable();
}
function syncNodeControls(){
 $('#node-layer').innerHTML=current.widths.map((_,l)=>option(l)).join('');$('#node-layer').value=state.focus[0];
 $('#node-position').innerHTML=Array.from({length:current.widths[state.focus[0]]},(_,p)=>option(p)).join('');$('#node-position').value=state.focus[1];
 $('#node-role').value=state.role;
 const size=state.role==='d'?current.ordinary:current.hubs;state.index=Math.min(state.index,size-1);
 $('#node-index').innerHTML=Array.from({length:size},(_,i)=>option(i)).join('');$('#node-index').value=state.index;
}
function selectedId(){return ids.get([...state.focus,state.role,state.index].join(','));}
function chooseNode(u){const n=current.nodes[u];state.focus=n.slice(0,2);state.role=n[2];state.index=n[3];syncNodeControls();renderNode();paintRegion();}
function paintRegion(){
 const enabled=new Set($$('[data-family]:checked').map(x=>x.dataset.family));
 state.scope=$('#scope').value;const selected=state.focus.join(','),involved=new Set([selected]);let bundles=0,edges=0;
 $$('#region-canvas .bundle').forEach(path=>{
  const e=path.dataset,valid=enabled.has(family(e.kind));
  const hot=state.scope==='all'||(state.scope==='near'&&(e.src===selected||e.dst===selected))||(state.scope==='out'&&e.src===selected)||(state.scope==='in'&&e.dst===selected);
  path.style.display=valid?'':'none';path.style.opacity=hot?(state.scope==='all'?'.48':'.88'):'.035';path.style.strokeWidth=hot?(state.scope==='all'?'1.5':'2.5'):'1';
  if(valid&&hot){bundles++;edges+=+e.count;involved.add(e.src);involved.add(e.dst);}
 });
 $$('#region-canvas .position').forEach(n=>{const hit=n.dataset.pos===selected,r=n.querySelector('.position-outline');r.style.stroke=hit?'#0f766e':'#dce4ed';r.style.strokeWidth=hit?'3':'1';n.style.opacity=state.scope==='all'||involved.has(n.dataset.pos)?'1':'.48';});
 $('#region-summary').textContent=`选中位置 (${selected}) · 高亮 ${bundles} 组区域连接，对应 ${edges} 条实际消息边。`;
 const svg=$('#region-canvas svg'),v=svg.viewBox.baseVal,z=+$('#zoom').value;svg.setAttribute('width',v.width*z);svg.setAttribute('height',v.height*z);
 if(window.refreshFormulas)window.refreshFormulas();
}
function grouped(es){
 const map=new Map();for(const [v,k] of es){const n=current.nodes[v],key=[n[0],n[1],n[2],k].join(',');if(!map.has(key))map.set(key,{l:n[0],p:n[1],role:n[2],k,vs:[]});map.get(key).vs.push(v);}
 return [...map.values()].sort((a,b)=>a.l-b.l||a.p-b.p||a.role.localeCompare(b.role)||a.k-b.k);
}
function renderNode(){
 const u=selectedId(),n=current.nodes[u],left=grouped(ins[u]),right=grouped(outs[u]);
 const h=Math.max(620,220+Math.max(left.length,right.length)*83),w=1510,cy=(h+100)/2;
 let s=svgStart(w,h,`${nodeName(n)} 完整上下游`)+`<defs>`;
 kinds.forEach(k=>{s+=`<marker id="ego-${k}" viewBox="0 0 10 8" refX="9" refY="4" markerWidth="6" markerHeight="5" orient="auto"><path d="M0 0 L10 4 L0 8 Z" fill="${colors[k]}"/></marker>`;});s+='</defs>';
 s+=svgText(25,37,`${nodeName(n)} · 全部一跳连接`,25,'#23344b',700)+svgText(25,69,'侧卡完整列出端点；数字可点击。曲线按区域、角色与边族归组，不代表额外汇总节点。',16,'#5c6d81');
 s+=svgText(260,108,`全部入边 ${ins[u].length} 条`,18,'#23344b',600,'middle')+svgText(1260,108,`全部出边 ${outs[u].length} 条`,18,'#23344b',600,'middle');
 for(const [side,groups] of [['in',left],['out',right]]){
  const gx=side==='in'?22:1020,top=145+(h-185-groups.length*83)/2;
  groups.forEach((g,row)=>{
   const y=top+row*83,k=kinds[g.k],c=colors[k];let sx,sy,tx,ty;
   if(side==='in'){sx=gx+465;sy=y+32;tx=615;ty=cy;}else{sx=895;sy=cy;tx=gx;ty=y+32;}
   s+=`<path d="M${sx} ${sy} C${sx+54} ${sy} ${tx-54} ${ty} ${tx} ${ty}" fill="none" stroke="${c}" stroke-width="2" opacity=".76" marker-end="url(#ego-${k})"/>`;
   s+=`<rect x="${gx}" y="${y}" width="465" height="66" rx="10" fill="white" stroke="${c}"/>`+svgText(gx+15,y+25,`${g.role.toUpperCase()}(${g.l},${g.p}) · ${k} · ${g.vs.length} 条`,17,c,600);
   s+=`<text x="${gx+15}" y="${y+51}" font-family="Noto Sans CJK SC,sans-serif" font-size="16" fill="#23344b">节点 `;
   g.vs.sort((a,b)=>current.nodes[a][3]-current.nodes[b][3]).forEach((v,i)=>{s+=`${i?', ':''}<tspan class="node-link" data-jump="${v}" tabindex="0" role="button" aria-label="查看 ${E(nodeName(current.nodes[v]))}">${current.nodes[v][3]}</tspan>`;});s+='</text>';
  });
 }
 const color=n[2]==='d'?'#2563eb':'#b57a13';s+=`<rect x="615" y="${cy-95}" width="280" height="190" rx="16" fill="#f5f8fd" stroke="${color}" stroke-width="2"/>`;
 s+=svgText(755,cy-48,nodeName(n),24,color,700,'middle')+svgText(755,cy-12,'每条消息边 δ=1',16,'#23344b',400,'middle')+svgText(755,cy+20,'首层输入的潜在总时延',14,'#5c6d81',400,'middle')+svgText(755,cy+48,current.delays[u].join(', '),18,'#23344b',600,'middle')+svgText(755,cy+77,'Full 沿固定出边广播',14,'#5c6d81',400,'middle');
 s+=svgText(24,h-22,'这里只画该节点的一跳上下游；邻居之间及邻居通往其他节点的边不在此图中。',15,'#5c6d81')+'</svg>';
 $('#node-canvas').innerHTML=s;
 $('#node-summary').textContent=`${nodeName(n)} · 入度 ${ins[u].length}，出度 ${outs[u].length}。`+(n[2]==='d'?`仅经普通路径可达的时延：${current.ordinary_delays[u].join('、')}。`:'Hub 仍依赖自身输入与历史；独立分区不会消除这些依赖。');
 const svg=$('#node-canvas svg');svg.setAttribute('width',w*.88);svg.setAttribute('height',h*.88);
 if(window.refreshFormulas)window.refreshFormulas();
}
function updateTargets(preferred){
 state.source=$('#pair-source').value;
 const targets=[...new Set(current.bundles.filter(b=>`${b[0]},${b[1]}`===state.source).map(b=>`${b[3]},${b[4]}`))].sort((a,b)=>{const x=a.split(',').map(Number),y=b.split(',').map(Number);return x[0]-y[0]||x[1]-y[1];});
 $('#pair-target').innerHTML=targets.map(p=>option(p,`(${p})`)).join('');
 state.target=targets.includes(preferred)?preferred:targets[0];$('#pair-target').value=state.target;renderMatrix();
}
function renderMatrix(){
 state.target=$('#pair-target').value;const src=state.source.split(',').map(Number),dst=state.target.split(',').map(Number),size=current.ordinary+current.hubs;
 const sources=[],targets=[];for(const r of ['d','h'])for(let i=0;i<(r==='d'?current.ordinary:current.hubs);i++){sources.push(ids.get([...src,r,i].join(',')));targets.push(ids.get([...dst,r,i].join(',')));}
 const ti=new Map(targets.map((u,i)=>[u,i])),matrix=new Map(),counts={};sources.forEach((u,i)=>{for(const [v,k]of outs[u])if(ti.has(v)){matrix.set(`${i},${ti.get(v)}`,[u,v,k]);counts[k]=(counts[k]||0)+1;}});
 const cell=29,x0=145,y0=145,w=1220,h=800;
 let s=svgStart(w,h,'完整端点连接矩阵')+svgText(25,36,`位置 (${state.source}) → (${state.target}) · 全部端点`,24,'#23344b',700)+svgText(25,67,'行：源节点。列：目标节点。彩点：消息边。四个块分别为 D→D、D→H、H→D、H→H。',16,'#5c6d81');
 s+=svgText(x0+current.ordinary*cell/2,y0-48,'下游普通区 D',17,'#2563eb',600,'middle')+svgText(x0+(current.ordinary+current.hubs/2)*cell,y0-48,'下游 hub 区 H',16,'#b57a13',600,'middle');
 for(let i=0;i<size;i++){
  const label=i<current.ordinary?'D'+i:'H'+(i-current.ordinary);
  s+=svgText(x0-17,y0+i*cell+20,label,13,'#23344b',400,'end',`class="node-link" data-jump="${sources[i]}"`)+svgText(x0+i*cell+cell/2,y0-14,label,12,'#23344b',400,'middle',`class="node-link" data-jump="${targets[i]}"`);
  for(let j=0;j<size;j++){
   const hit=matrix.get(`${i},${j}`),x=x0+j*cell,y=y0+i*cell,fill=i<current.ordinary&&j<current.ordinary?'#f3f7fe':i>=current.ordinary&&j>=current.ordinary?'#fdf6e9':'#fafbfd';
   s+=`<g ${hit?`data-jump="${hit[1]}" style="cursor:pointer"`:''}><rect class="matrix-hit" x="${x}" y="${y}" width="${cell}" height="${cell}" fill="${fill}" stroke="#dce4ed" stroke-width=".7"/>`;
   if(hit)s+=`<circle cx="${x+cell/2}" cy="${y+cell/2}" r="5.8" fill="${colors[kinds[hit[2]]]}"/>`;
   s+=`<title>${E(nodeName(current.nodes[sources[i]]))} → ${E(nodeName(current.nodes[targets[j]]))}${hit?' · '+kinds[hit[2]]+' · δ=1':' · 无边'}</title></g>`;
  }
 }
 let y=185;Object.entries(counts).sort((a,b)=>+a[0]-b[0]).forEach(([k,n])=>{s+=`<circle cx="825" cy="${y-5}" r="7" fill="${colors[kinds[k]]}"/>`+svgText(845,y,`${kinds[k]}：${n} 条`,19,colors[kinds[k]],600);y+=38;});
 ['DD：普通细节传播','DH：普通结果进入 hub','HH：hub 交换背景','HD：hub 向普通节点投递钩子','','这里只显示这一对位置。','点击编号 / 彩点进入节点图。'].forEach((t,i)=>s+=svgText(815,y+32+i*31,t,16,'#5c6d81'));
 s+=svgText(25,h-20,'每个位置包含两个独立区域；矩阵的行列相邻不表示节点间另有连接。',15,'#5c6d81')+'</svg>';
 $('#matrix-canvas').innerHTML=s;$('#matrix-summary').textContent=`${matrix.size} 条消息边 · 跨 ${dst[0]-src[0]} 层 · 时延均为 1`;
 if(window.refreshFormulas)window.refreshFormulas();
}
function renderDepthTable(){
 let s='<thead><tr><th>候选（点击切换）</th><th>位置 / 节点</th><th>普通路径时延</th><th>普通路径每相位入口数</th><th>全图每相位入口数</th></tr></thead><tbody>';
 order.forEach(key=>{const c=ATLAS.cases[key],st=c.stats;s+=`<tr data-case="${key}" class="${key===state.key?'current':''}"><td>${c.depth} 层${c.add_dd4?' + DD4':''}</td><td>${st.positions} / ${st.nodes.toLocaleString()}</td><td>${st.ordinary_delays.join(', ')}</td><td>${st.ordinary_phase_sources.map(p=>p[0]).join(' / ')}</td><td>${st.all_phase_sources.map(p=>p[0]).join(' / ')}</td></tr>`;});$('#depth-table').innerHTML=s+'</tbody>';
}
$('#case-select').addEventListener('change',e=>mountCase(e.target.value));
$('#scope').addEventListener('change',paintRegion);$('#zoom').addEventListener('change',paintRegion);
$$('[data-family]').forEach(c=>c.addEventListener('change',paintRegion));
for(const [id,predicate]of [['preset-detail',x=>x.startsWith('DD')],['preset-hub',x=>!x.startsWith('DD')],['preset-all',x=>true]])$('#'+id).addEventListener('click',()=>{$$('[data-family]').forEach(c=>c.checked=predicate(c.dataset.family));paintRegion();});
function regionClick(e){
 const p=e.target.closest('.position');if(p){state.focus=p.dataset.pos.split(',').map(Number);if($('#scope').value==='all')$('#scope').value='near';syncNodeControls();renderNode();paintRegion();return;}
 const edge=e.target.closest('.bundle');if(edge){state.source=edge.dataset.src;$('#pair-source').value=state.source;updateTargets(edge.dataset.dst);$('#matrix').scrollIntoView({behavior:'smooth',block:'start'});}
}
$('#region-canvas').addEventListener('click',regionClick);$('#region-canvas').addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();regionClick(e);}});
$('#node-layer').addEventListener('change',e=>{state.focus[0]=+e.target.value;state.focus[1]=Math.min(state.focus[1],current.widths[state.focus[0]]-1);syncNodeControls();renderNode();paintRegion();});
$('#node-position').addEventListener('change',e=>{state.focus[1]=+e.target.value;renderNode();paintRegion();});
$('#node-role').addEventListener('change',e=>{state.role=e.target.value;syncNodeControls();renderNode();});
$('#node-index').addEventListener('change',e=>{state.index=+e.target.value;renderNode();});
$('#example-d').addEventListener('click',()=>chooseNode(current.selected_d));$('#example-h').addEventListener('click',()=>chooseNode(current.selected_h));
for(const host of ['node-canvas','matrix-canvas']){
 const handler=e=>{const el=e.target.closest('[data-jump]');if(el){chooseNode(+el.dataset.jump);if(host==='matrix-canvas')$('#neighbors').scrollIntoView({behavior:'smooth'});}};
 $('#'+host).addEventListener('click',handler);$('#'+host).addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();handler(e);}});
}
$('#pair-source').addEventListener('change',()=>updateTargets());$('#pair-target').addEventListener('change',renderMatrix);
$('#depth-table').addEventListener('click',e=>{const row=e.target.closest('[data-case]');if(row){mountCase(row.dataset.case);$('#regions').scrollIntoView({behavior:'smooth'});}});
$$('[data-export]').forEach(b=>b.addEventListener('click',()=>{const svg=$('#'+b.dataset.export+' svg'),blob=new Blob([new XMLSerializer().serializeToString(svg)],{type:'image/svg+xml;charset=utf-8'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=`hb-timed-${state.key}-${b.dataset.export}.svg`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}));
mountCase('9');
window.atlasDebug={get case(){return current;},get state(){return state;},mountCase,chooseNode};
