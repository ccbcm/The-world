package net.ccbcm.wallpaper;
import android.service.wallpaper.WallpaperService;import android.media.MediaPlayer;import android.view.SurfaceHolder;import android.os.PowerManager;import android.content.*;
public class VideoWallpaper extends WallpaperService {
 @Override public Engine onCreateEngine(){return new VideoEngine();}
 class VideoEngine extends Engine implements SharedPreferences.OnSharedPreferenceChangeListener {
  MediaPlayer player;boolean visible,ready;SharedPreferences prefs;SurfaceHolder holder;
  final BroadcastReceiver battery=new BroadcastReceiver(){public void onReceive(Context c,Intent i){sync();}};
  @Override public void onCreate(SurfaceHolder h){super.onCreate(h);prefs=getSharedPreferences("wallpaper",0);prefs.registerOnSharedPreferenceChangeListener(this);registerReceiver(battery,new IntentFilter(PowerManager.ACTION_POWER_SAVE_MODE_CHANGED));}
  @Override public void onSurfaceCreated(SurfaceHolder h){super.onSurfaceCreated(h);holder=h;load();}
  @Override public void onSurfaceChanged(SurfaceHolder h,int format,int width,int height){super.onSurfaceChanged(h,format,width,height);holder=h;fill();}
  void fill(){if(ready&&player!=null)player.setVideoScalingMode(MediaPlayer.VIDEO_SCALING_MODE_SCALE_TO_FIT_WITH_CROPPING);}
  void release(){ready=false;if(player!=null){player.release();player=null;}}
  void load(){release();String path=prefs.getString("path","");if(path.isEmpty()||holder==null)return;try{player=new MediaPlayer();player.setDataSource(path);player.setDisplay(holder);player.setVolume(0,0);player.setLooping(true);player.setOnPreparedListener(p->{ready=true;fill();sync();});player.setOnVideoSizeChangedListener((p,w,h)->fill());player.setOnErrorListener((p,a,b)->{release();return true;});player.prepareAsync();}catch(Exception e){release();}}
  void sync(){if(!ready||player==null)return;PowerManager power=(PowerManager)getSystemService(POWER_SERVICE);if(visible&&power.isInteractive()&&!power.isPowerSaveMode())player.start();else if(player.isPlaying())player.pause();}
  @Override public void onVisibilityChanged(boolean v){visible=v;if(v)fill();sync();}
  @Override public void onSurfaceDestroyed(SurfaceHolder h){release();holder=null;super.onSurfaceDestroyed(h);}
  @Override public void onSharedPreferenceChanged(SharedPreferences p,String key){if("path".equals(key))load();}
  @Override public void onDestroy(){release();prefs.unregisterOnSharedPreferenceChangeListener(this);unregisterReceiver(battery);super.onDestroy();}
 }
}
