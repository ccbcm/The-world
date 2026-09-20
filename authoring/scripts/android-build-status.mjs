import {execFileSync} from 'node:child_process';
import {writeFile} from 'node:fs/promises';
const credentials=execFileSync('git',['-c','credential.interactive=false','credential','fill'],{input:'protocol=https\nhost=github.com\nusername=ccbcm\n\n',encoding:'utf8',stdio:['pipe','pipe','pipe']});
const token=credentials.split(/\r?\n/).find(x=>x.startsWith('password='))?.slice(9);if(!token)throw Error('GitHub authentication unavailable');
const headers={Authorization:'Bearer '+token,Accept:'application/vnd.github+json'};
const response=await fetch('https://api.github.com/repos/ccbcm/The-world/actions/workflows/android-preview.yml/runs?per_page=1',{headers});
if(!response.ok)throw Error('GitHub status '+response.status);const run=(await response.json()).workflow_runs[0];
console.log(JSON.stringify({id:run?.id,status:run?.status,conclusion:run?.conclusion,url:run?.html_url}));
if(run?.conclusion==='failure'){
 const jobs=await fetch(run.jobs_url,{headers}).then(r=>r.json());console.log(JSON.stringify(jobs.jobs.map(j=>({id:j.id,steps:j.steps.map(s=>({name:s.name,conclusion:s.conclusion}))}))));
 if(process.argv.includes('--logs')){const logs=await fetch(run.logs_url,{headers});if(logs.ok){await writeFile('android-build-logs.zip',Buffer.from(await logs.arrayBuffer()));console.log('Saved android-build-logs.zip');}}
}
if(run?.conclusion==='success'&&process.argv.includes('--download')){
 const artifacts=await fetch(run.artifacts_url,{headers}).then(r=>r.json());const artifact=artifacts.artifacts.find(a=>a.name==='CCBCM-Android-preview');if(!artifact)throw Error('Missing APK artifact');
 const file=await fetch(artifact.archive_download_url,{headers});if(!file.ok)throw Error('Artifact '+file.status);await writeFile('android-preview-artifact.zip',Buffer.from(await file.arrayBuffer()));console.log('Saved android-preview-artifact.zip');
}
