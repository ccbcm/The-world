package net.ccbcm.wallpaper;
import android.app.*;import android.os.*;import android.content.*;import android.view.*;import android.widget.*;import android.graphics.drawable.GradientDrawable;
import androidx.media3.common.*;import androidx.media3.exoplayer.ExoPlayer;import java.io.File;
public class PreviewActivity extends Activity implements SurfaceHolder.Callback {
 ExoPlayer player;SurfaceView surface;TextView status;Button apply;File file;boolean active;
 int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}
 @Override public void onCreate(Bundle state){super.onCreate(state);
  try{file=new File(getIntent().getStringExtra("path"));if(!file.getCanonicalFile().getParentFile().equals(getFilesDir().getCanonicalFile())||!file.isFile())throw new Exception();}catch(Exception e){finish();return;}
  LinearLayout layout=new LinearLayout(this);layout.setOrientation(LinearLayout.VERTICAL);layout.setPadding(dp(20),dp(30),dp(20),dp(24));layout.setBackgroundColor(0xff191820);
  status=new TextView(this);status.setText("正在打开预览…");status.setTextSize(16);status.setTextColor(0xffeee9f5);status.setPadding(0,dp(12),0,dp(12));layout.addView(status);
  surface=new SurfaceView(this);layout.addView(surface,new LinearLayout.LayoutParams(-1,0,1));surface.getHolder().addCallback(this);
  apply=new Button(this);apply.setText("设为壁纸");apply.setEnabled(false);GradientDrawable bg=new GradientDrawable();bg.setColor(0xffd3c2f7);bg.setCornerRadius(dp(28));apply.setBackground(bg);apply.setTextColor(0xff252031);LinearLayout.LayoutParams params=new LinearLayout.LayoutParams(-1,dp(52));params.topMargin=dp(18);layout.addView(apply,params);apply.setOnClickListener(v->choose(false));
  Button alternate=new Button(this);alternate.setText("系统壁纸列表");alternate.setOnClickListener(v->choose(true));layout.addView(alternate);setContentView(layout);
 }
 void play(){if(!active||player!=null||!surface.getHolder().getSurface().isValid())return;apply.setEnabled(false);
  try{player=Playback.open(this,file,surface.getHolder(),new Player.Listener(){
   @Override public void onRenderedFirstFrame(){status.setText("预览正常");apply.setEnabled(true);}
   @Override public void onPlayerError(PlaybackException error){status.setText("这段视频暂时无法播放："+error.getErrorCodeName()+"\n"+Build.MANUFACTURER+" "+Build.MODEL+" · Android "+Build.VERSION.RELEASE);apply.setEnabled(false);}
  });player.play();}catch(Exception e){status.setText("无法打开预览，请换一张壁纸重试。");}}
 void release(){if(player!=null){player.release();player=null;}}
 void choose(boolean list){if(player==null||!apply.isEnabled())return;
  getSharedPreferences("wallpaper",0).edit().putString("path",file.getAbsolutePath()).remove("playback_error").apply();release();
  try{Intent intent=list?new Intent(WallpaperManager.ACTION_LIVE_WALLPAPER_CHOOSER):new Intent(WallpaperManager.ACTION_CHANGE_LIVE_WALLPAPER).putExtra(WallpaperManager.EXTRA_LIVE_WALLPAPER_COMPONENT,new ComponentName(this,VideoWallpaper.class));startActivity(intent);}
  catch(Exception e){status.setText("系统未打开设置，请尝试系统壁纸列表。");play();}
 }
 @Override protected void onResume(){super.onResume();active=true;if(surface!=null)play();}
 @Override protected void onPause(){active=false;release();super.onPause();}
 @Override public void surfaceCreated(SurfaceHolder h){play();}
 @Override public void surfaceChanged(SurfaceHolder h,int f,int w,int height){if(player!=null)player.setVideoSurfaceHolder(h);else play();}
 @Override public void surfaceDestroyed(SurfaceHolder h){release();}
}
