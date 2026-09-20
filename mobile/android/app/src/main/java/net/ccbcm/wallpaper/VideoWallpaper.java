package net.ccbcm.wallpaper;
import android.service.wallpaper.WallpaperService;
import android.view.SurfaceHolder;
import android.os.PowerManager;
import android.content.*;
import java.io.File;
public class VideoWallpaper extends WallpaperService {
 @Override public Engine onCreateEngine(){return new VideoEngine();}
 class VideoEngine extends Engine implements SharedPreferences.OnSharedPreferenceChangeListener {
  Playback playback;SharedPreferences prefs;SurfaceHolder holder;boolean visible,failed;
  final BroadcastReceiver battery=new BroadcastReceiver(){public void onReceive(Context c,Intent i){sync();}};
  @Override public void onCreate(SurfaceHolder h){super.onCreate(h);prefs=getSharedPreferences("wallpaper",0);prefs.registerOnSharedPreferenceChangeListener(this);registerReceiver(battery,new IntentFilter(PowerManager.ACTION_POWER_SAVE_MODE_CHANGED));}
  @Override public void onSurfaceCreated(SurfaceHolder h){super.onSurfaceCreated(h);holder=h;failed=false;sync();}
  @Override public void onSurfaceChanged(SurfaceHolder h,int format,int w,int height){super.onSurfaceChanged(h,format,w,height);holder=h;sync();}
  void release(){if(playback!=null){playback.close();playback=null;}}
  void load(){String path=prefs.getString("path","");if(path.isEmpty()||holder==null||!holder.getSurface().isValid())return;
   playback=new Playback(VideoWallpaper.this,new File(path),holder,prefs.getBoolean("compatibility",false),new Playback.Events(){
    public void ready(boolean mode){prefs.edit().remove("playback_error").apply();}
    public void status(String message){}
    public void failed(String code){failed=true;prefs.edit().putString("playback_error",code).apply();}
   });playback.setPlaying(true);playback.start();
  }
  void sync(){PowerManager power=(PowerManager)getSystemService(POWER_SERVICE);
   // Free hidden engines before app/system preview requests another decoder.
   if(!visible||(!isPreview()&&(!power.isInteractive()||power.isPowerSaveMode()))){release();return;}
   if(playback==null&&!failed)load();
  }
  @Override public void onVisibilityChanged(boolean v){visible=v;if(v)failed=false;sync();}
  @Override public void onSurfaceDestroyed(SurfaceHolder h){release();holder=null;super.onSurfaceDestroyed(h);}
  @Override public void onSharedPreferenceChanged(SharedPreferences p,String key){if("path".equals(key)){release();failed=false;sync();}}
  @Override public void onDestroy(){release();prefs.unregisterOnSharedPreferenceChangeListener(this);unregisterReceiver(battery);super.onDestroy();}
 }
}
