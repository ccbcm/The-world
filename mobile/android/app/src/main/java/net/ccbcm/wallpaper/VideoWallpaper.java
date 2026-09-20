package net.ccbcm.wallpaper;
import android.service.wallpaper.WallpaperService;
import android.view.SurfaceHolder;
import android.os.PowerManager;
import android.content.*;
import androidx.media3.common.*;
import androidx.media3.exoplayer.ExoPlayer;
import java.io.File;
public class VideoWallpaper extends WallpaperService {
 @Override public Engine onCreateEngine(){return new VideoEngine();}
 class VideoEngine extends Engine implements SharedPreferences.OnSharedPreferenceChangeListener {
  ExoPlayer player;SharedPreferences prefs;SurfaceHolder holder;boolean visible;
  final BroadcastReceiver battery=new BroadcastReceiver(){public void onReceive(Context c,Intent i){sync();}};
  @Override public void onCreate(SurfaceHolder h){super.onCreate(h);prefs=getSharedPreferences("wallpaper",0);prefs.registerOnSharedPreferenceChangeListener(this);registerReceiver(battery,new IntentFilter(PowerManager.ACTION_POWER_SAVE_MODE_CHANGED));}
  @Override public void onSurfaceCreated(SurfaceHolder h){super.onSurfaceCreated(h);holder=h;load();}
  @Override public void onSurfaceChanged(SurfaceHolder h,int format,int w,int height){super.onSurfaceChanged(h,format,w,height);holder=h;if(player!=null)player.setVideoSurfaceHolder(h);sync();}
  void release(){if(player!=null){player.release();player=null;}}
  void load(){release();String path=prefs.getString("path","");if(path.isEmpty()||holder==null)return;
   try{player=Playback.open(VideoWallpaper.this,new File(path),holder,new Player.Listener(){
    @Override public void onPlayerError(PlaybackException error){prefs.edit().putString("playback_error",error.getErrorCodeName()).apply();}
    @Override public void onRenderedFirstFrame(){prefs.edit().remove("playback_error").apply();}
   });sync();}catch(Exception error){prefs.edit().putString("playback_error",error.getClass().getSimpleName()).apply();release();}}
  void sync(){if(player==null)return;PowerManager power=(PowerManager)getSystemService(POWER_SERVICE);player.setPlayWhenReady(visible&&(isPreview()||power.isInteractive()&&!power.isPowerSaveMode()));}
  @Override public void onVisibilityChanged(boolean v){visible=v;sync();}
  @Override public void onSurfaceDestroyed(SurfaceHolder h){release();holder=null;super.onSurfaceDestroyed(h);}
  @Override public void onSharedPreferenceChanged(SharedPreferences p,String key){if("path".equals(key))load();}
  @Override public void onDestroy(){release();prefs.unregisterOnSharedPreferenceChangeListener(this);unregisterReceiver(battery);super.onDestroy();}
 }
}
