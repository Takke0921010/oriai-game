// 使い方: node render.mjs stills 1.5 20 33   /   node render.mjs all 30
import {spawn} from 'node:child_process';
import {mkdirSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const CHROME=process.env.HOME+'/Library/Caches/ms-playwright/chromium_headless_shell-1248/chrome-headless-shell-mac-arm64/chrome-headless-shell';
const mode=process.argv[2],args=process.argv.slice(3).map(Number);
const port=9333+Math.floor(Math.random()*500);
const proc=spawn(CHROME,['--no-sandbox','--disable-gpu','--hide-scrollbars','--force-color-profile=srgb',`--remote-debugging-port=${port}`,'--window-size=1280,720','about:blank'],{stdio:'ignore'});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
let info;for(let i=0;i<50;i++){try{info=await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();if(info.length)break;}catch{}await sleep(200);}
const page=info.find(x=>x.type==='page');
const ws=new WebSocket(page.webSocketDebuggerUrl);await new Promise(r=>ws.onopen=r);
let id=0;const pend=new Map();const events=[];
ws.onmessage=m=>{const d=JSON.parse(m.data);if(d.id&&pend.has(d.id)){pend.get(d.id)(d);pend.delete(d.id);}else events.push(d);};
const send=(method,params={})=>new Promise(r=>{const i=++id;pend.set(i,r);ws.send(JSON.stringify({id:i,method,params}));});
await send('Page.enable');await send('Runtime.enable');
await send('Emulation.setDeviceMetricsOverride',{width:1280,height:720,deviceScaleFactor:1,mobile:false});
const url='file://'+resolve('oriai-v2.0-explainer.html')+'?render';
await send('Page.navigate',{url});await sleep(1500);
const total=(await send('Runtime.evaluate',{expression:'TOTAL',returnByValue:true})).result.result.value;
const err=(await send('Runtime.evaluate',{expression:'typeof seek',returnByValue:true})).result.result.value;
console.log('TOTAL',total,'seek',err);
const shot=async(t,file,fmt='jpeg')=>{
  await send('Runtime.evaluate',{expression:`seek(${t})`});
  const r=await send('Page.captureScreenshot',{format:fmt,quality:fmt==='jpeg'?92:undefined,clip:{x:0,y:0,width:1280,height:720,scale:1}});
  writeFileSync(file,Buffer.from(r.result.data,'base64'));
};
if(mode==='stills'){mkdirSync('build/stills',{recursive:true});for(const t of args){await shot(t,`build/stills/t${String(t).padStart(6,'0')}.png`,'png');}}
else{const fps=args[0]||30;mkdirSync('build/frames',{recursive:true});const n=Math.ceil(total*fps);const t0=Date.now();
  for(let i=0;i<n;i++){await shot(i/fps,`build/frames/f${String(i).padStart(5,'0')}.jpg`);if(i%300===0)console.log(i,'/',n,((Date.now()-t0)/1000).toFixed(0)+'s');}
  writeFileSync('build/frames/meta.json',JSON.stringify({fps,n,total}));}
ws.close();proc.kill();process.exit(0);
