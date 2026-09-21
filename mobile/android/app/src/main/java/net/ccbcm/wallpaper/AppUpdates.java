package net.ccbcm.wallpaper;
import android.app.*;import android.content.*;import android.net.Uri;import android.provider.Settings;
import androidx.core.content.FileProvider;
import java.io.*;import java.net.*;import org.json.*;

/** User-initiated, HTTPS-only updates. Android still verifies the APK signature. */
final class AppUpdates {
 final MainActivity activity;File pending;boolean waitingPermission;
 AppUpdates(MainActivity activity){this.activity=activity;}
 void check(){if(activity.busy)return;activity.busy=true;activity.message("正在检查更新…");
  activity.jobs.execute(()->{try{
   JSONObject release=new JSONObject(new String(MainActivity.fetch("https://ccbcm.net/downloads/latest.json?t="+System.currentTimeMillis(),16384),"UTF-8")).getJSONObject("android");
   int current=activity.getPackageManager().getPackageInfo(activity.getPackageName(),0).versionCode;
   int next=release.getInt("versionCode");String version=release.getString("version"),url=release.getString("url"),sha=release.getString("sha256");long size=release.getLong("size");
   if(!url.matches("https://ccbcm\\.net/downloads/releases/CCBCM-Android-[0-9.]+\\.apk")||!sha.matches("[a-f0-9]{64}")||size<100000||size>100L*1024*1024)throw new IOException("更新信息无效");
   activity.runOnUiThread(()->{activity.busy=false;if(activity.isFinishing()||activity.isDestroyed())return;
    if(next<=current){activity.message("已经是最新版本。");return;}
    activity.message("有新版本 "+version);
    new AlertDialog.Builder(activity).setTitle("更新 CCBCM "+version).setMessage("下载后由系统确认安装，保留现有设置。").setNegativeButton("稍后",null).setPositiveButton("更新",(d,w)->download(url,sha,size,next)).show();
   });
  }catch(Exception e){activity.busy=false;activity.message("检查更新失败，请稍后重试。");}});
 }
 void download(String url,String sha,long size,int version){if(activity.busy)return;activity.busy=true;activity.message("正在下载更新…");activity.jobs.execute(()->{File part=null;try{
  File dir=new File(activity.getCacheDir(),"updates");if(!dir.isDirectory()&&!dir.mkdirs())throw new IOException();
  File apk=new File(dir,"CCBCM-"+version+".apk");part=new File(dir,"CCBCM-"+version+".part");
  HttpURLConnection connection=MainActivity.connect(url);
  try(InputStream input=connection.getInputStream();OutputStream output=new FileOutputStream(part)){byte[] buffer=new byte[65536];int n;long total=0;while((n=input.read(buffer))!=-1){total+=n;if(total>size)throw new IOException();output.write(buffer,0,n);}if(total!=size)throw new IOException();}finally{connection.disconnect();}
  if(!MainActivity.digest(part).equals(sha))throw new IOException("校验失败");
  if(apk.exists()&&!apk.delete())throw new IOException();if(!part.renameTo(apk))throw new IOException();
  activity.runOnUiThread(()->{activity.busy=false;if(activity.isFinishing()||activity.isDestroyed())return;pending=apk;install();});
 }catch(Exception e){activity.busy=false;activity.message("更新下载失败，请重试。");}finally{if(part!=null)part.delete();}});}
 void install(){if(pending==null)return;
  try{if(!activity.getPackageManager().canRequestPackageInstalls()){
   waitingPermission=true;activity.message("请允许 CCBCM 安装更新，然后返回。");
   activity.startActivity(new Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,Uri.parse("package:"+activity.getPackageName())));return;}
   Uri uri=FileProvider.getUriForFile(activity,activity.getPackageName()+".updates",pending);
   activity.startActivity(new Intent(Intent.ACTION_VIEW).setDataAndType(uri,"application/vnd.android.package-archive").addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION));
   pending=null;activity.message("请在系统窗口确认更新。");
  }catch(Exception e){activity.message("无法打开系统安装程序，请从 ccbcm.net 获取新版。");}
 }
 void resume(){if(waitingPermission){waitingPermission=false;if(activity.getPackageManager().canRequestPackageInstalls())install();else activity.message("未开启安装更新权限，当前版本仍可正常使用。");}}
}
