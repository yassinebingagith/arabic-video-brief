import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
import {spawnSync} from 'node:child_process';
import {Readable} from 'node:stream';
import {pipeline} from 'node:stream/promises';
import {createGunzip} from 'node:zlib';
import {Browser, detectBrowserPlatform, install} from '@puppeteer/browsers';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const require=createRequire(path.join(root,'package.json'));
const file=path.join(root,'.runtime','render-runtime.json');
const pkg=JSON.parse(fs.readFileSync(path.join(root,'package.json'),'utf8'));
const check=process.argv.includes('--check');

function executable(binary,args){
  if(!binary || !fs.existsSync(binary))throw new Error(`Executable missing: ${binary}`);
  const result=spawnSync(binary,args,{encoding:'utf8',windowsHide:true,timeout:30000});
  if(result.error || result.status!==0)throw new Error(`${path.basename(binary)} cannot run: ${result.error?.message ?? result.stderr}`);
  return (result.stdout || result.stderr).split(/\r?\n/)[0];
}

async function ensureFFmpeg(binary){
  try{executable(binary,['-version']);return;}catch(error){
    const expected=path.join(root,'node_modules','ffmpeg-static')+path.sep;
    if(!binary || !path.resolve(binary).startsWith(expected))throw error;
    console.log('FFmpeg download is incomplete; retrying the same pinned binary release.');
  }
  const metadata=require('ffmpeg-static/package.json')['ffmpeg-static'];
  const url=`https://github.com/eugeneware/ffmpeg-static/releases/download/${metadata['binary-release-tag']}/ffmpeg-${process.platform}-${process.arch}.gz`;
  for(let attempt=1;attempt<=2;attempt++){
    try{
      const response=await fetch(url,{signal:AbortSignal.timeout(240000)});
      if(!response.ok)throw new Error(`FFmpeg download returned HTTP ${response.status}`);
      const temporary=binary+'.download';
      await pipeline(Readable.fromWeb(response.body),createGunzip(),fs.createWriteStream(temporary));
      fs.chmodSync(temporary,0o755);
      executable(temporary,['-version']);
      fs.renameSync(temporary,binary);
      return;
    }catch(error){if(attempt===2)throw error;console.log('Retrying interrupted FFmpeg download...');}
  }
}

try{
  if(Number(process.versions.node.split('.')[0])<22)throw new Error('Node.js 22 or later is required.');
  let runtime;
  if(check){
    if(!fs.existsSync(file))throw new Error('Renderer setup is missing. Run npm ci, or npm run setup:renderer.');
    runtime=JSON.parse(fs.readFileSync(file,'utf8'));
    if(runtime.PROJECT_ROOT!==root)throw new Error('This checkout moved. Run npm run setup:renderer to refresh its local paths.');
  }else{
    const platform=detectBrowserPlatform();
    let browser=process.env.CHROME_BIN || process.env.PUPPETEER_EXECUTABLE_PATH;
    if(!browser){
      if(!platform)throw new Error(`No rendering browser is available for ${process.platform}/${process.arch}. Set CHROME_BIN to a compatible installed Chromium browser.`);
      console.log(`Installing/caching Chrome Headless Shell ${pkg.renderBrowser.buildId} for ${platform}...`);
      let result;
      for(let attempt=1;attempt<=2;attempt++){
        try{result=await install({browser:Browser.CHROMEHEADLESSSHELL,buildId:pkg.renderBrowser.buildId,
          platform,cacheDir:path.join(root,'.runtime','browsers')});break;}
        catch(error){if(attempt===2)throw error;console.log('Retrying interrupted browser download...');}
      }
      browser=result.executablePath;
    }
    runtime={schema:1,PROJECT_ROOT:root,NODE_BIN:process.execPath,
      CHROME_BIN:path.resolve(browser),FFMPEG_BIN:require('ffmpeg-static'),FFPROBE_BIN:process.env.FFPROBE_BIN || require('ffprobe-static').path,
      HYPERFRAMES_CLI:path.join(path.dirname(require.resolve('hyperframes/package.json')),'bin','hyperframes.mjs'),
      GSAP_JS:require.resolve('gsap/dist/gsap.min.js'),BROWSER_BUILD:(process.env.CHROME_BIN || process.env.PUPPETEER_EXECUTABLE_PATH) ? 'explicit-override' : pkg.renderBrowser.buildId};
    await ensureFFmpeg(runtime.FFMPEG_BIN);
  }
  const versions={node:process.versions.node,ffmpeg:executable(runtime.FFMPEG_BIN,['-version']),
    ffprobe:executable(runtime.FFPROBE_BIN,['-version']),browser:executable(runtime.CHROME_BIN,['--version'])};
  for(const key of ['HYPERFRAMES_CLI','GSAP_JS'])if(!fs.existsSync(runtime[key]))throw new Error(`Missing ${key}; run npm ci.`);
  if(!check){fs.mkdirSync(path.dirname(file),{recursive:true});fs.writeFileSync(file,JSON.stringify(runtime,null,2)+'\n');}
  console.log(JSON.stringify({ready:true,configuration:file,versions},null,2));
}catch(error){
  console.error(`Renderer setup failed: ${error.message}`);
  if(process.platform==='linux')console.error('On Linux the Chromium system libraries must also be installed; see README.md.');
  process.exitCode=1;
}
