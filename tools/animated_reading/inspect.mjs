import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {pathToFileURL} from 'node:url';
import {createRequire} from 'node:module';
const require=createRequire('F:/hyperframes-v3/renderers/hyperframes/package.json');
const puppeteer=require('puppeteer-core');
const folder=path.resolve(process.argv[2]);
const data=JSON.parse(fs.readFileSync(path.join(folder,'page-data.json'),'utf8'));
const runtime=JSON.parse(fs.readFileSync('F:/hyperframes-v3/config/local-runtime.json','utf8'));
const errors=[],observations=[];
const browser=await puppeteer.launch({executablePath:runtime.CHROME_BIN,headless:true,args:['--allow-file-access-from-files','--disable-gpu']});
console.log('Browser ready');
const output=path.join(folder,'inspection');fs.mkdirSync(output,{recursive:true});
try {
  const page=await browser.newPage();console.log('Page ready');await page.setViewport({width:1080,height:1140,deviceScaleFactor:1});
  page.on('pageerror',error=>errors.push(error.message));
  await page.goto(pathToFileURL(path.join(folder,'index.html')).href,{waitUntil:'load'});
  console.log('Composition loaded');
  await page.evaluate(async()=>{await document.fonts.load('700 46px Arabic');await document.fonts.load('750 46px Arabic');await document.fonts.ready;});
  console.log('Fonts ready');
  const seek=async t=>{await page.evaluate(async t=>{window.__timelines.main.seek(t,false);await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));return true;},t);};
  for(const p of data.pages){
    const settledTime=p.writing_end ? p.writing_end+.035 : p.start+1.3;
    await seek(settledTime);
    const geometry=await page.evaluate(p=>{
      const section=document.getElementById(p.id);
      return {page:p.id,fontLoaded:document.fonts.check('700 46px Arabic'),lines:p.lines.map(line=>{
        const e=document.getElementById(line.id);const box=e.getBoundingClientRect();
        const texts=[...e.querySelectorAll('text')].map(t=>{const b=t.getBoundingClientRect();return {text:t.textContent,left:b.left,right:b.right,top:b.top,bottom:b.bottom};});
        return {id:line.id,opacity:Number(getComputedStyle(e).opacity),box:{top:box.top,bottom:box.bottom},texts};
      }),visible:[...document.querySelectorAll('.page')].filter(e=>getComputedStyle(e).visibility==='visible').map(e=>e.id)};
    },p);
    if(!geometry.fontLoaded)errors.push('Arabic font missing');
    if(JSON.stringify(geometry.visible)!==JSON.stringify([p.id]))errors.push(`Overlapping pages at ${settledTime}`);
    for(const line of geometry.lines){
      if(line.opacity<.999)errors.push(`${line.id} not visible at final reading hold`);
      for(const t of line.texts)if(t.left<70||t.right>940||t.top<0||t.bottom>900)errors.push(`Text exceeds region: ${line.id}: ${t.text}`);
      for(let i=1;i<line.texts.length;i++)if(line.texts[i].right>line.texts[i-1].left+.5)errors.push(`Adjacent text segments overlap: ${line.id}`);
    }
    observations.push(geometry);
    if(p.words){
      const completed=()=>page.evaluate(p=>p.words.filter(w=>Number(getComputedStyle(document.getElementById(w.id+'-complete')).opacity)>.999).length,p);
      if(await completed()!==p.words.length)errors.push(`Incomplete written words at ${settledTime}`);
      await seek(p.start+1.3);
      const early=await completed();
      if(early===0||early>=p.words.length*.4)errors.push(`Writing is not spread across page ${p.id}`);
      const middle=(p.writing_start+p.writing_end)/2;
      await seek(middle);const halfway=await completed();
      if(halfway<=early||halfway>=p.words.length)errors.push(`Writing progression fails at ${p.id}`);
      observations.push({page:p.id,early_completed_words:early,middle_completed_words:halfway,total_units:p.words.length,writing_start:p.writing_start,writing_end:p.writing_end});
    }
    const times=[p.start+.2,p.start+1.3,(p.start+p.end)/2,...p.markers.map(m=>m.at+m.duration/2),p.end-.25,p.end-.08];
    for(const time of times){await seek(time);await page.screenshot({path:path.join(output,`${p.id}-${time.toFixed(3)}.png`)});}
    for(const m of p.markers){
      const state=async t=>{await seek(t);return page.evaluate(id=>getComputedStyle(document.getElementById(id)).clipPath,m.id);};
      const before=await state(m.at-.05),during=await state(m.at+m.duration/2),after=await state(m.at+m.duration+.05);
      if(before===during||during===after||before===after)errors.push(`Marker does not progress: ${m.id}`);
    }
  }
  for(const t of data.pages.slice(1).map(p=>p.start)){
    await seek(t);
    const visible=await page.evaluate(()=>[...document.querySelectorAll('.page')].filter(e=>getComputedStyle(e).visibility==='visible').map(e=>e.id));
    if(visible.length!==1)errors.push(`Invalid page boundary at ${t}`);
  }
  await seek(data.duration);
  const endingVisible=await page.evaluate(()=>[...document.querySelectorAll('.page')].some(e=>getComputedStyle(e).visibility==='visible'));
  if(endingVisible)errors.push('Reading page remains at ending handoff');
  await seek(22);const first=await page.screenshot();await seek(33);await seek(.1);await seek(22);const second=await page.screenshot();
  if(!first.equals(second))errors.push('Repeated seek changes pixels');
  const result={composition_sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(folder,'index.html'))).digest('hex'),
    repeated_seek_pixels_equal:first.equals(second),errors,observations};
  fs.writeFileSync(path.join(folder,'inspection.json'),JSON.stringify(result,null,2));
  console.log(JSON.stringify({errors,pages:observations.length,repeated_seek_pixels_equal:first.equals(second)}));
  if(errors.length)process.exitCode=1;
} finally {await browser.close();}
