"""Exercise the generated offline page in an isolated headless Firefox."""
import base64
import json
import os
from pathlib import Path
import socket
import subprocess
import time
import tempfile
import argparse

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output-dir', type=Path)
args = parser.parse_args()
OUT = args.output_dir or Path(tempfile.mkdtemp(prefix='hb-atlas-browser-'))
OUT.mkdir(parents=True, exist_ok=True)
profile = OUT / 'browser-profile'
profile.mkdir(exist_ok=True)
with socket.socket() as probe:
    probe.bind(('127.0.0.1', 0))
    port = probe.getsockname()[1]
(profile/'user.js').write_text(
    'user_pref("marionette.port", %d);\n'
    'user_pref("browser.shell.checkDefaultBrowser", false);\n'
    'user_pref("browser.startup.page", 0);\n' % port)
log=(OUT/'browser.log').open('w')
process=subprocess.Popen(['firefox','--headless','--no-remote','--profile',str(profile),'--marionette','about:blank'],stdout=log,stderr=log)
sock=None
try:
    for attempt in range(100):
        try:
            sock=socket.create_connection(('127.0.0.1',port),timeout=.3)
            break
        except OSError:
            if process.poll() is not None:raise RuntimeError('Firefox exited; see browser.log')
            time.sleep(.15)
    if sock is None:raise RuntimeError('Marionette did not start')
    sock.settimeout(30)
    def receive():
        header=b''
        while not header.endswith(b':'):
            part=sock.recv(1)
            if not part:raise EOFError('Firefox disconnected')
            header+=part
        size=int(header[:-1]);raw=b''
        while len(raw)<size:
            part=sock.recv(size-len(raw))
            if not part:raise EOFError('Firefox disconnected')
            raw+=part
        return json.loads(raw)
    greeting=receive();counter=0
    def command(name,parameters=None):
        global counter
        counter+=1
        raw=json.dumps([0,counter,name,parameters or {}]).encode()
        sock.sendall(str(len(raw)).encode()+b':'+raw)
        response=receive()
        assert response[0]==1 and response[1]==counter,response
        if response[2] is not None:raise RuntimeError(response[2])
        return response[3]
    def script(code):
        code=code.replace('window.atlasDebug','window.wrappedJSObject.atlasDebug')
        code=code.replace('window.atlasFormulaDebug','window.wrappedJSObject.atlasFormulaDebug')
        r=command('WebDriver:ExecuteScript',{'script':code,'args':[], 'newSandbox':False,'sandbox':'default'})
        return r['value'] if isinstance(r,dict) and 'value' in r else r
    command('WebDriver:NewSession',{'capabilities':{'alwaysMatch':{'acceptInsecureCerts':True}}})
    command('WebDriver:SetWindowRect',{'width':1510,'height':1150})
    command('WebDriver:Navigate',{'url':(ROOT/'generated'/'index.html').as_uri()})
    initial=script('return {title:document.title,metrics:document.querySelector("#metrics").textContent,graphs:document.querySelectorAll(".canvas svg").length,debug:typeof window.atlasDebug};')
    assert initial['graphs']==3 and initial['debug']=='object',initial
    script('window.atlasErrors=[];window.addEventListener("error",e=>window.atlasErrors.push(e.message));return true;')
    records=[]
    for key in ['5','5-dd4','7','9','13','15','17']:
        code='''
        window.atlasDebug.mountCase(%s);
        const c=window.atlasDebug.case;
        const choose=(s,v)=>{const el=document.querySelector(s);el.value=v;el.dispatchEvent(new Event('change',{bubbles:true}));};
        choose('#scope','all');document.querySelector('#preset-detail').click();
        const visible=[...document.querySelectorAll('#region-canvas .bundle')].filter(e=>e.style.display!=='none');
        const visibleKinds=[...new Set(visible.map(e=>e.dataset.kind))].sort();
        document.querySelector('#example-h').click();
        const hSummary=document.querySelector('#node-summary').textContent;
        document.querySelector('#example-d').click();
        const dSummary=document.querySelector('#node-summary').textContent;
        const point=document.querySelector('#matrix-canvas [data-jump]');point.dispatchEvent(new MouseEvent('click',{bubbles:true}));
        return {key:c.key,nodes:c.nodes.length,edges:c.edges.length,visibleKinds,hSummary,dSummary,
                dd4Visible:getComputedStyle(document.querySelector('#dd4-label')).display!=='none',
                mathCount:document.querySelectorAll('.formula-side math').length,
                nodeFormula:document.querySelector('#node-formulas .formula-state').textContent,
                matrices:document.querySelectorAll('#matrix-canvas .matrix-hit').length,
                matrixCircles:document.querySelectorAll('#matrix-canvas g circle').length,
                phaseRows:document.querySelectorAll('#depth-table tbody tr').length,
                errors:window.atlasErrors.slice()};
        ''' % json.dumps(key)
        result=script(code)
        assert result['matrices']==400 and result['phaseRows']==12 and not result['errors'],result
        assert result['visibleKinds']==(['DD1','DD2','DD4'] if key=='5-dd4' else ['DD1','DD2']),result
        assert result['dd4Visible']==(key=='5-dd4'),result
        assert result['mathCount']>=20 and result['nodeFormula'].startswith('D('),result
        records.append(result)
    # Check actual region-click and edge-click navigation, then restore the main view.
    interactions=script('''
      window.atlasDebug.mountCase('9');document.querySelector('#preset-all').click();
      document.querySelector('#scope').value='near';document.querySelector('#scope').dispatchEvent(new Event('change'));
      document.querySelector('#region-canvas [data-pos="3,2"]').dispatchEvent(new MouseEvent('click',{bubbles:true}));
      const selected=window.atlasDebug.state.focus.join(',');
      const edge=[...document.querySelectorAll('#region-canvas .bundle')].find(e=>e.dataset.src==='3,2'&&e.dataset.dst==='4,2');
      edge.dispatchEvent(new MouseEvent('click',{bubbles:true}));
      const pair=document.querySelector('#matrix-summary').textContent;
      document.querySelector('#pair-source').value='4,3';document.querySelector('#pair-source').dispatchEvent(new Event('change'));
      document.querySelector('#pair-target').value='8,0';document.querySelector('#pair-target').dispatchEvent(new Event('change'));
      const skipPair=document.querySelector('#matrix-summary').textContent;
      window.atlasDebug.mountCase('9');window.scrollTo({top:0,behavior:'instant'});
      return {selected,pair,skipPair,errors:window.atlasErrors.slice(),horizontalOverflow:document.documentElement.scrollWidth>window.innerWidth};
    ''')
    assert interactions['selected']=='3,2' and interactions['pair'].startswith('56 条') and not interactions['errors'],interactions
    assert not interactions['horizontalOverflow'],interactions
    formula_checks=script('''
      let checked=0;const failures=[];
      for(const key of ['5','5-dd4','7','9','13','15','17']){
        window.atlasDebug.mountCase(key);const c=window.atlasDebug.case;
        for(const b of c.bundles){
          const [l,p,r,m,q,t,k,count]=b,s=m-l,f=window.atlasFormulaDebug.targetFormula;
          let modes;
          if(k==='DD1'||k==='DH1')modes=['base','near'];
          else if(k.startsWith('DD'))modes=['cross'];
          else if(k.startsWith('HH'))modes=['base','cross'];
          else modes=s===1?['base']:['cross'];
          const valid=modes.some(mode=>Array.from(f(l,s,p,mode)).includes(q));
          if(!valid)failures.push([key,Array.from(b)]);checked++;
        }
      }
      window.atlasDebug.mountCase('9');
      const toggle=document.querySelector('#formulas-toggle');toggle.click();
      const hidden=getComputedStyle(document.querySelector('#region-formulas')).display==='none';toggle.click();
      const visible=getComputedStyle(document.querySelector('#region-formulas')).display!=='none';
      const math=document.querySelector('#region-formulas math').getBoundingClientRect();
      return {checked,failures,hidden,visible,mathWidth:math.width,mathHeight:math.height,errors:window.atlasErrors.slice()};
    ''')
    assert formula_checks['checked']>1000 and not formula_checks['failures'] and not formula_checks['errors'],formula_checks
    assert formula_checks['hidden'] and formula_checks['visible'] and formula_checks['mathWidth']>0 and formula_checks['mathHeight']>0,formula_checks
    timing_checks=script("""
      window.atlasDebug.mountCase('9');
      const el=document.querySelector('#timing-mode'),result=[];
      for(const mode of ['timed','aligned','settle']){
        el.value=mode;el.dispatchEvent(new Event('change',{bubbles:true}));
        result.push({mode,rows:document.querySelectorAll('#timing-table tbody tr').length,
          summary:document.querySelector('#timing-summary').textContent});
      }
      el.value='timed';el.dispatchEvent(new Event('change',{bubbles:true}));return result;
    """)
    assert timing_checks[0]['rows'] > 3 and timing_checks[1]['rows'] == timing_checks[2]['rows'] == 3, timing_checks
    mixing_check=script("""
      const c=window.atlasDebug.case;
      const u=c.nodes.findIndex((n,i)=>n[0]===8&&n[2]==='d'&&c.delays[i].includes(2)&&c.delays[i].includes(6));
      window.atlasDebug.chooseNode(u);
      const row=[...document.querySelectorAll('#timing-table tbody tr')].find(r=>r.children[0].textContent==='7');
      const contents=row.children[1].textContent;
      window.atlasDebug.mountCase('9');return contents;
    """)
    assert '输入 0，路径时延 6' in mixing_check and '输入 1，路径时延 2' in mixing_check, mixing_check
    # Actual Settle spatial candidates, including the g=1 boundary and no-hub UI.
    settle_checks=script("""
      const results=[],failures=[];
      const choose=(s,v)=>{const el=document.querySelector(s);el.value=v;el.dispatchEvent(new Event('change',{bubbles:true}));};
      for(const key of ['lattice-5','lattice-7','lattice-9','exchange-7','exchange-7-h','exchange-10','exchange-10-h','exchange-13','exchange-13-h']){
        window.atlasDebug.mountCase(key);const c=window.atlasDebug.case;
        const size=c.ordinary+c.hubs;
        const cells=document.querySelectorAll('#matrix-canvas .matrix-hit').length;
        const circles=document.querySelectorAll('#matrix-canvas g circle').length;
        const pair=window.atlasDebug.state.source+'>'+window.atlasDebug.state.target;
        const expected=c.edges.filter(([u,v])=>c.nodes[u].slice(0,2).join(',')+'>'+c.nodes[v].slice(0,2).join(',')===pair).length;
        if(cells!==size*size||circles!==expected)failures.push(['matrix',key,cells,circles,expected]);
        if(document.querySelector('#node-role').options.length!==(c.hubs?2:1))failures.push(['roles',key]);
        if(document.querySelector('#timing-mode').value!=='settle'||!document.querySelector('#timing-mode').disabled)failures.push(['timing',key]);
        let checked=0;
        for(const b of c.bundles){
          const [l,p,r,m,q,t,k,count]=b;
          const exchange=c.family==='exchange'&&k!=='HD1';
          if(!Array.from(window.atlasFormulaDebug.settleTargets(l,p,exchange)).includes(q))failures.push(['region',key,Array.from(b)]);
          checked++;
        }
        if(c.family==='exchange')for(const [u,v,k] of c.edges){
          const a=c.nodes[u],b=c.nodes[v];
          if(a[2]==='d'&&b[2]==='d'&&b[3]!==a[3]&&b[3]!==(a[3]^(1<<(a[0]%4))))failures.push(['node-bit',key,u,v]);
        }
        choose('#node-layer','0');choose('#node-position','0');
        const atBoundary=document.querySelector('#region-formulas').textContent;
        if(/NaN|Infinity|undefined/.test(atBoundary))failures.push(['boundary',key]);
        const edge=document.querySelector('#region-canvas .bundle');
        edge.dispatchEvent(new MouseEvent('click',{bubbles:true}));
        const matrixSummary=document.querySelector('#matrix-summary').textContent;
        document.querySelector('#preset-detail').click();
        if(window.atlasDebug.case.nodes.length!==c.nodes.length)failures.push(['filter-mutated-graph',key]);
        results.push({key,cells,circles,checked,period:c.settle_period,nodes:c.nodes.length,matrixSummary});
      }
      // Family select changes the actual model, not only the displayed edge families.
      choose('#family-select','lattice');const latticeKey=window.atlasDebug.case.key;
      choose('#family-select','exchange');const exchangeKey=window.atlasDebug.case.key;
      choose('#family-select','multiscale');const multiscaleKey=window.atlasDebug.case.key;
      return {results,failures,latticeKey,exchangeKey,multiscaleKey,errors:window.atlasErrors.slice()};
    """)
    assert not settle_checks['failures'] and not settle_checks['errors'],settle_checks
    assert (settle_checks['latticeKey'],settle_checks['exchangeKey'],settle_checks['multiscaleKey']) == ('lattice-7','exchange-10','9'),settle_checks
    terminal_checks=script("""
      const results=[],failures=[];
      const choose=(s,v)=>{const el=document.querySelector(s);el.value=v;el.dispatchEvent(new Event('change',{bubbles:true}));};
      const keys=['5','5-dd4','7','9','13','15','17','lattice-5','lattice-7','lattice-9',
                  'exchange-7','exchange-7-h','exchange-10','exchange-10-h','exchange-13','exchange-13-h'];
      for(const key of keys){
        window.atlasDebug.mountCase(key);const c=window.atlasDebug.case,last=c.depth-1;
        if(c.hubs)document.querySelector('#example-h').click();
        choose('#node-layer',String(last));choose('#node-position','0');
        if(document.querySelector('#node-role').options.length!==1||window.atlasDebug.state.role!=='d')failures.push(['terminal-role',key]);
        if(c.nodes.some(n=>n[0]===last&&n[2]==='h'))failures.push(['terminal-hub',key]);
        const box=document.querySelector(`#region-canvas [data-pos="${last},0"]`);
        if(box.textContent.includes('H4'))failures.push(['drawn-hub',key]);
        choose('#pair-source',`${last-1},0`);choose('#pair-target',`${last},0`);
        const cells=document.querySelectorAll('#matrix-canvas .matrix-hit').length;
        const circles=document.querySelectorAll('#matrix-canvas g circle').length;
        const rows=c.nodes.filter(n=>n[0]===last-1&&n[1]===0).length;
        const columns=c.nodes.filter(n=>n[0]===last&&n[1]===0).length;
        const expected=c.edges.filter(([u,v])=>c.nodes[u][0]===last-1&&c.nodes[u][1]===0&&c.nodes[v][0]===last&&c.nodes[v][1]===0).length;
        if(cells!==rows*columns||circles!==expected||columns!==16)failures.push(['terminal-matrix',key,cells,rows,columns,circles,expected]);
        if(/NaN|Infinity|undefined/.test(document.querySelector('#matrix-canvas').textContent+document.querySelector('#region-formulas').textContent))failures.push(['terminal-text',key]);
        const point=document.querySelector('#matrix-canvas g[data-jump]');
        point.dispatchEvent(new MouseEvent('click',{bubbles:true}));
        if(window.atlasDebug.state.focus[0]!==last)failures.push(['terminal-navigation',key]);
        results.push({key,rows,columns,edges:circles});
      }
      return {results,failures,errors:window.atlasErrors.slice()};
    """)
    assert not terminal_checks['failures'] and not terminal_checks['errors'],terminal_checks
    # Exercise every newly registered width / node-count / optional-hub case.
    compact_checks=[]
    all_keys=list(json.loads((ROOT/'generated'/'checks.json').read_text()))
    assert len(all_keys)==58,all_keys
    for key in [k for k in all_keys if k.startswith('compact-') or k.startswith('exchange-m')]:
        result=script('''
          window.atlasDebug.mountCase(%s);const c=window.atlasDebug.case,failures=[];
          const choose=(s,v)=>{const el=document.querySelector(s);el.value=String(v);el.dispatchEvent(new Event('change',{bubbles:true}));};
          const pair=window.atlasDebug.state.source+'>'+window.atlasDebug.state.target;
          const count=c.edges.filter(([u,v])=>c.nodes[u].slice(0,2).join(',')+'>'+c.nodes[v].slice(0,2).join(',')===pair).length;
          const cells=document.querySelectorAll('#matrix-canvas .matrix-hit').length;
          if(cells!==(c.ordinary+c.hubs)**2||document.querySelectorAll('#matrix-canvas g circle').length!==count)failures.push('matrix');
          for(const b of c.bundles){
            const [l,p,r,m,q,t,k]=b,s=m-l;
            if(c.family==='multiscale'){
              const modes=(k==='DD1'||k==='DH1')?['base','near']:k.startsWith('DD')?['cross']:k.startsWith('HH')?['base','cross']:s===1?['base']:['cross'];
              if(!modes.some(mode=>Array.from(window.atlasFormulaDebug.targetFormula(l,s,p,mode)).includes(q)))failures.push(['mapping',Array.from(b)]);
            }else if(!Array.from(window.atlasFormulaDebug.settleTargets(l,p,k!=='HD1')).includes(q))failures.push(['mapping',Array.from(b)]);
          }
          choose('#node-layer',0);choose('#node-position',0);
          if(/NaN|Infinity|undefined/.test(document.querySelector('#region-formulas').textContent))failures.push('boundary');
          if(c.family==='multiscale'&&Array.from(window.atlasFormulaDebug.targetFormula(0,1,0,'cross')).some(p=>p>=c.widths[1]))failures.push('cross-range');
          const last=c.depth-1;choose('#node-layer',last);choose('#node-position',0);
          if(document.querySelector('#node-role').options.length!==1)failures.push('terminal-role');
          choose('#pair-source',`${last-1},0`);choose('#pair-target',`${last},0`);
          if(document.querySelectorAll('#matrix-canvas .matrix-hit').length!==(c.ordinary+c.hubs)*c.ordinary)failures.push('terminal-matrix');
          return {key:c.key,n:c.ordinary,h:c.hubs,cells,failures,errors:window.atlasErrors.slice()};
        ''' % json.dumps(key))
        assert not result['failures'] and not result['errors'],result
        compact_checks.append(result)
    capacity_checks=script('''
      const choose=(s,v)=>{const el=document.querySelector(s);el.value=String(v);el.dispatchEvent(new Event('change',{bubbles:true}));};
      const original=window.atlasDebug.case.key;
      choose('#cap-family','multiscale');choose('#cap-profile','multiscale-compact-9');
      choose('#cap-n',8);choose('#cap-h',0);choose('#cap-d',64);choose('#cap-memory','K');choose('#cap-sharing','independent');
      const smallBudgets=[...document.querySelector('#cap-k').options].map(o=>o.value);
      const row=document.querySelector('#capacity-table tbody tr'),total=+row.dataset.total;
      choose('#cap-k',8);const dense=+document.querySelector('#capacity-table tbody tr').dataset.active;
      choose('#cap-k','pool');const pool=+document.querySelector('#capacity-table tbody tr').dataset.active;
      const unchanged=window.atlasDebug.case.key===original;
      document.querySelector('#capacity-table [data-cap-case]').click();const linked=window.atlasDebug.case.key;
      choose('#cap-n',128);const largeBudgets=[...document.querySelector('#cap-k').options].map(o=>o.value);
      choose('#cap-n',32);choose('#cap-h',4);choose('#cap-memory','X');choose('#cap-profile','multiscale-17');choose('#cap-d',128);
      choose('#cap-limit','all');const large=+document.querySelector('#capacity-table tbody tr').dataset.total;
      choose('#cap-limit','256');const hiddenLarge=document.querySelectorAll('#capacity-table tbody tr').length===0;
      choose('#cap-family','fc');const noHub=document.querySelector('#cap-h').disabled&&document.querySelector('#cap-h').value==='0';
      choose('#cap-profile','fc-4');choose('#cap-sharing','shared');choose('#cap-rank',4);
      const p4=+document.querySelector('#capacity-table tbody tr').dataset.total;
      choose('#cap-rank',16);const p16=+document.querySelector('#capacity-table tbody tr').dataset.total;
      choose('#cap-sharing','independent');const rankDisabled=document.querySelector('#cap-rank').disabled;
      return {smallBudgets,largeBudgets,total,dense,pool,unchanged,linked,large,hiddenLarge,noHub,p4,p16,rankDisabled,errors:window.atlasErrors.slice()};
    ''')
    assert capacity_checks['smallBudgets']==['1','2','4','8','pool'],capacity_checks
    assert capacity_checks['largeBudgets']==['1','2','4','8','16','32','64','pool'],capacity_checks
    assert round(capacity_checks['total']/1e6,3)==9.139,capacity_checks
    assert capacity_checks['dense']==capacity_checks['pool']==capacity_checks['total'],capacity_checks
    assert capacity_checks['unchanged'] and capacity_checks['linked']=='compact-9-n8-h0',capacity_checks
    assert capacity_checks['large']>256e6 and capacity_checks['hiddenLarge'] and capacity_checks['noHub'],capacity_checks
    assert capacity_checks['p4']<capacity_checks['p16'] and capacity_checks['rankDisabled'] and not capacity_checks['errors'],capacity_checks
    script("document.querySelector('#matrix').scrollIntoView({behavior:'instant'});return true;")
    shot=command('WebDriver:TakeScreenshot',{'id':None,'full':False,'hash':False,'scroll':False})
    (OUT/'terminal-matrix-preview.png').write_bytes(base64.b64decode(shot['value'] if isinstance(shot,dict) else shot))
    timing_sync=script("""
      window.atlasDebug.mountCase('9');
      const select=document.querySelector('#pair-source');select.value='4,3';select.dispatchEvent(new Event('change'));
      const target=document.querySelector('#pair-target');target.value='8,0';target.dispatchEvent(new Event('change'));
      const rows=[];
      for(const mode of ['timed','aligned','timed-common','settle']){
        window.atlasDebug.setTiming(mode);
        const edge=[...document.querySelectorAll('#region-canvas .bundle')].find(e=>e.dataset.src==='4,3'&&e.dataset.dst==='8,0');
        rows.push({mode,title:edge.querySelector('title').textContent,
          matrix:document.querySelector('#matrix-summary').textContent,
          formula:document.querySelector('#pair-formulas math').textContent,
          timing:document.querySelector('#timing-summary').textContent});
      }
      return rows;
    """)
    for item in timing_sync:
        delta=1 if item['mode'] in ('timed','timed-common') else 4
        assert f'δ={delta}' in item['title'] and f'时延均为 {delta}' in item['matrix'],item
        assert f'δ={delta}' in item['formula'],item
    assert '输入间隔 10' in timing_sync[2]['timing'] and '输入间隔 10' in timing_sync[3]['timing'],timing_sync
    preserved_timing=script("""
      const el=document.querySelector('#case-select');el.value='17';el.dispatchEvent(new Event('change'));
      return {key:window.atlasDebug.case.key,mode:window.atlasDebug.state.timing,summary:document.querySelector('#timing-summary').textContent};
    """)
    assert preserved_timing['key']=='17' and preserved_timing['mode']=='settle' and 'D=18>M=17' in preserved_timing['summary'],preserved_timing
    # Inspect each new family visually; external temporary evidence, not tracked outputs.
    for key in ('lattice-7','exchange-10','exchange-10-h','compact-9-n8-h0','compact-9-two-inputs-n32-h4'):
        script("window.atlasDebug.mountCase(%s);document.querySelector('#regions').scrollIntoView({behavior:'instant'});return true;" % json.dumps(key))
        shot=command('WebDriver:TakeScreenshot',{'id':None,'full':False,'hash':False,'scroll':False})
        (OUT/(key+'-preview.png')).write_bytes(base64.b64decode(shot['value'] if isinstance(shot,dict) else shot))
    command('WebDriver:SetWindowRect',{'width':850,'height':1100})
    small_layout=script("window.atlasDebug.mountCase('exchange-10');return {overflow:document.documentElement.scrollWidth>window.innerWidth,math:document.querySelector('#region-formulas math').getBoundingClientRect().width,errors:window.atlasErrors.slice()};")
    assert not small_layout['overflow'] and small_layout['math']>0 and not small_layout['errors'],small_layout
    capacity_layout=script("document.querySelector('#capacity').scrollIntoView({behavior:'instant'});return {overflow:document.documentElement.scrollWidth>window.innerWidth};")
    assert not capacity_layout['overflow'],capacity_layout
    shot=command('WebDriver:TakeScreenshot',{'id':None,'full':False,'hash':False,'scroll':False})
    (OUT/'capacity-preview.png').write_bytes(base64.b64decode(shot['value'] if isinstance(shot,dict) else shot))
    command('WebDriver:SetWindowRect',{'width':1510,'height':1150})
    script("window.atlasDebug.mountCase('9');window.scrollTo({top:0,behavior:'instant'});return true;")
    # Check all local document/download targets after formula rendering.
    from urllib.parse import urlparse, unquote
    hrefs=script('return [...document.querySelectorAll("a[href]")].map(a=>a.href);')
    for href in hrefs:
        url=urlparse(href)
        if url.scheme == 'file':
            assert Path(unquote(url.path)).is_file(), href
    # Ensure the embedded ladder image decoded successfully.
    image_status=script('return {complete:document.querySelector("img.ladder").complete,width:document.querySelector("img.ladder").naturalWidth};')
    assert image_status['complete'] and image_status['width']==1640,image_status
    shot=command('WebDriver:TakeScreenshot',{'id':None,'full':False,'hash':False,'scroll':False})
    (OUT/'browser-preview.png').write_bytes(base64.b64decode(shot['value'] if isinstance(shot,dict) else shot))
    script('document.querySelector("#regions").scrollIntoView({behavior:"instant"});return true;')
    shot=command('WebDriver:TakeScreenshot',{'id':None,'full':False,'hash':False,'scroll':False})
    (OUT/'formula-preview.png').write_bytes(base64.b64decode(shot['value'] if isinstance(shot,dict) else shot))
    result={'initial':initial,'cases':records,'interactions':interactions,'formulas':formula_checks,'timing':timing_checks,'mixing':mixing_check,'settle':settle_checks,'terminal':terminal_checks,'compact':compact_checks,'capacity':capacity_checks,'timing_sync':timing_sync,'preserved_timing':preserved_timing,'small_layout':small_layout,'capacity_layout':capacity_layout,'embedded_image':image_status}
    (OUT/'browser-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    command('Marionette:Quit',{'flags':['eForceQuit']})
finally:
    print('Browser evidence:', OUT)
    if sock:sock.close()
    if process.poll() is None:
        process.terminate()
        try:process.wait(timeout=5)
        except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
    log.close()
