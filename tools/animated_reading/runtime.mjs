import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

export const repositoryRoot=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');

export function loadRuntime(){
  const file=path.join(repositoryRoot,'.runtime','render-runtime.json');
  if(!fs.existsSync(file))throw new Error('Renderer setup is missing. Run python scripts/setup.py or npm ci.');
  const runtime=JSON.parse(fs.readFileSync(file,'utf8'));
  if(path.resolve(runtime.PROJECT_ROOT)!==repositoryRoot)throw new Error('This checkout moved. Run npm run setup:renderer.');
  for(const key of ['CHROME_BIN','FFMPEG_BIN','FFPROBE_BIN'])runtime[key]=process.env[key] || runtime[key];
  for(const key of ['CHROME_BIN','FFMPEG_BIN','FFPROBE_BIN','HYPERFRAMES_CLI','GSAP_JS']){
    if(!runtime[key] || !fs.existsSync(runtime[key]))throw new Error(`Missing ${key}; run npm ci.`);
  }
  return runtime;
}

export function renderEnvironment(runtime){
  return {...process.env,CHROME_BIN:runtime.CHROME_BIN,PUPPETEER_EXECUTABLE_PATH:runtime.CHROME_BIN,
    FFMPEG_PATH:runtime.FFMPEG_BIN,FFMPEG_BIN:runtime.FFMPEG_BIN,FFPROBE_PATH:runtime.FFPROBE_BIN,FFPROBE_BIN:runtime.FFPROBE_BIN,
    PATH:[path.dirname(runtime.FFMPEG_BIN),path.dirname(runtime.FFPROBE_BIN),process.env.PATH || ''].join(path.delimiter)};
}
