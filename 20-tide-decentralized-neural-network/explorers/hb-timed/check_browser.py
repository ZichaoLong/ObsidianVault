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
        assert result['matrices']==400 and result['phaseRows']==7 and not result['errors'],result
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
    for key in ('lattice-7','exchange-10','exchange-10-h'):
        script("window.atlasDebug.mountCase(%s);document.querySelector('#regions').scrollIntoView({behavior:'instant'});return true;" % json.dumps(key))
        shot=command('WebDriver:TakeScreenshot',{'id':None,'full':False,'hash':False,'scroll':False})
        (OUT/(key+'-preview.png')).write_bytes(base64.b64decode(shot['value'] if isinstance(shot,dict) else shot))
    command('WebDriver:SetWindowRect',{'width':850,'height':1100})
    small_layout=script("window.atlasDebug.mountCase('exchange-10');return {overflow:document.documentElement.scrollWidth>window.innerWidth,math:document.querySelector('#region-formulas math').getBoundingClientRect().width,errors:window.atlasErrors.slice()};")
    assert not small_layout['overflow'] and small_layout['math']>0 and not small_layout['errors'],small_layout
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
    result={'initial':initial,'cases':records,'interactions':interactions,'formulas':formula_checks,'timing':timing_checks,'mixing':mixing_check,'settle':settle_checks,'timing_sync':timing_sync,'preserved_timing':preserved_timing,'small_layout':small_layout,'embedded_image':image_status}
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
