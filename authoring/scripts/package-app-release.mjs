import {readFile,writeFile,mkdir,copyFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const dir=path.join(root,'downloads/releases');await mkdir(dir,{recursive:true});
const gradle=await readFile(path.join(root,'mobile/android/app/build.gradle'),'utf8');
const windows=await readFile(path.join(root,'authoring/wallpaper-player/Updates.cs'),'utf8');
const manifest={schema:1,generatedAt:new Date().toISOString()};
for(const [platform,source,version,versionCode,name] of [
 ['android','CCBCM-Android-preview.apk',gradle.match(/versionName '([^']+)'/)[1],Number(gradle.match(/versionCode (\d+)/)[1]),'Android'],
 ['windows','CCBCM-Wallpaper-Setup.exe',windows.match(/AssemblyFileVersion\("(\d+\.\d+\.\d+)\.\d+"/)[1],Number(windows.match(/const int Current=(\d+)/)[1]),'Windows']
]){
 const bytes=await readFile(path.join(root,'downloads',source));
 const sha256=createHash('sha256').update(bytes).digest('hex');
 const filename=`CCBCM-${name}-${version}.${platform==='android'?'apk':'exe'}`;
 const target=path.join(dir,filename);
 let old;try{old=await readFile(target);}catch(e){if(e.code!=='ENOENT')throw e;}
 if(old&&!old.equals(bytes))throw Error(`Refusing to replace immutable release ${filename}; bump the version first`);
 if(!old)await copyFile(path.join(root,'downloads',source),target);
 manifest[platform]={version,versionCode,url:`https://ccbcm.net/downloads/releases/${filename}`,size:bytes.length,sha256};
}
await writeFile(path.join(root,'downloads/latest.json'),JSON.stringify(manifest,null,2)+'\n');
console.log(JSON.stringify(manifest,null,2));
