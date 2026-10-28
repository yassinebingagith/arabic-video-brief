import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {loadRuntime,renderEnvironment} from './runtime.mjs';

try{
  const args=process.argv.slice(2);
  const option=name=>args[args.indexOf(name)+1];
  if(!args.includes('--project') || !option('--project'))throw new Error('Usage: node tools/animated_reading/render.mjs --project <Project> [--quality draft|standard|high]');
  const project=path.resolve(option('--project'));
  const quality=args.includes('--quality')?option('--quality'):'high';
  if(!['draft','standard','high'].includes(quality))throw new Error('Unknown render quality.');
  const runtime=loadRuntime(),env=renderEnvironment(runtime);
  for(const command of [
    ['lint',project,'--json'],
    ['render',project,'-o',path.join(path.dirname(project),'reading-pages.mp4'),'--fps','30','--quality',quality,'--workers','1','--low-memory-mode','--strict','--no-best-effort']
  ]){
    const result=spawnSync(process.execPath,[runtime.HYPERFRAMES_CLI,...command],{env,stdio:'inherit',windowsHide:true});
    if(result.error)throw result.error;
    if(result.status!==0)throw new Error(`Hyperframes ${command[0]} failed (${result.status}).`);
  }
}catch(error){console.error(error.message);process.exitCode=1;}
