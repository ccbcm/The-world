import {mkdir,writeFile} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import path from 'node:path';
// One-time migration of existing public works, from originals rather than old thumbnails.
const dir=path.resolve('gallery/media/hd');await mkdir(dir,{recursive:true});
const {items}=await fetch('https://ccbcm.net/api/published-videos').then(r=>{if(!r.ok)throw Error(r.status);return r.json();});
const result={};
for(const work of items){
 const url=`https://ccbcm.net/api/published-videos/${work.id}/content`;
 const probe=JSON.parse(execFileSync('ffprobe',['-v','error','-select_streams','v:0','-show_entries','stream=width,height,codec_name','-of','json',url],{encoding:'utf8',timeout:90000})).streams[0];
 execFileSync('ffmpeg',['-v','error','-y','-ss','1','-i',url,'-frames:v','1','-vf','scale=w=min(1920\\,iw):h=min(1920\\,ih):force_original_aspect_ratio=decrease','-q:v','2',path.join(dir,work.id+'.jpg')],{timeout:120000});
 result[work.id]={poster:'/gallery/media/hd/'+work.id+'.jpg',width:probe.width,height:probe.height,codec:probe.codec_name};
 console.log(work.title,probe.width,probe.height,probe.codec_name);
}
await writeFile(path.join(dir,'index.json'),JSON.stringify(result,null,2)+'\n');
