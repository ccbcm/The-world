package net.ccbcm.wallpaper;
import android.app.*;import android.os.*;import android.content.*;import android.view.*;import android.widget.*;import android.graphics.drawable.GradientDrawable;
import java.io.File;
public class PreviewActivity extends Activity implements SurfaceHolder.Callback {
 Playback playback;SurfaceView surface;TextView status;Button apply,alternate,retry;File file;boolean active,compatibility;
 int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}
 void enabled(boolean value){apply.setEnabled(value);alternate.setEnabled(value);}
 @Override public void onCreate(Bundle state){super.onCreate(state);
  try{file=new File(getIntent().getStringExtra("path"));if(!file.getCanonicalFile().getParentFile().equals(getFilesDir().getCanonicalFile())||!file.isFile())throw new Exception();}catch(Exception e){finish();return;}
  LinearLayout layout=new LinearLayout(this);layout.setOrientation(LinearLayout.VERTICAL);layout.setPadding(dp(20),dp(30),dp(20),dp(24));layout.setBackgroundColor(0xff191820);
  TextView title=new TextView(this);title.setText("CCBCM · 壁纸预览 0.3");title.setTextSize(20);title.setTextColor(0xffeee9f5);layout.addView(title);
  status=new TextView(this);status.setTextSize(14);status.setTextColor(0xffeee9f5);status.setPadding(0,dp(12),0,dp(12));layout.addView(status);
  surface=new SurfaceView(this);layout.addView(surface,new LinearLayout.LayoutParams(-1,0,1));surface.getHolder().addCallback(this);
  apply=new Button(this);apply.setText("设为壁纸");GradientDrawable bg=new GradientDrawable();bg.setColor(0xffd3c2f7);bg.setCornerRadius(dp(28));apply.setBackground(bg);apply.setTextColor(0xff252031);LinearLayout.LayoutParams params=new LinearLayout.LayoutParams(-1,dp(52));params.topMargin=dp(18);layout.addView(apply,params);apply.setOnClickListener(v->choose(false));
  alternate=new Button(this);alternate.setText("系统壁纸列表");alternate.setOnClickListener(v->choose(true));layout.addView(alternate);
  retry=new Button(this);retry.setText("重新预览");retry.setVisibility(View.GONE);retry.setOnClickListener(v->{release();compatibility=false;play();});layout.addView(retry);enabled(false);setContentView(layout);
 }
 void play(){if(!active||playback!=null||!surface.getHolder().getSurface().isValid())return;enabled(false);retry.setVisibility(View.GONE);status.setText("正在打开预览…");
  playback=new Playback(this,file,surface.getHolder(),compatibility,new Playback.Events(){
   public void ready(boolean mode){compatibility=mode;status.setText(mode?"预览正常 · 兼容播放":"预览正常");enabled(true);}
   public void status(String message){status.setText(message);}
   public void failed(String code){status.setText("无法显示视频："+code+"\n"+Build.MANUFACTURER+" "+Build.MODEL+" · Android "+Build.VERSION.RELEASE);enabled(false);retry.setVisibility(View.VISIBLE);}
  });playback.setPlaying(true);playback.start();
 }
 void release(){if(playback!=null){playback.close();playback=null;}}
 void choose(boolean list){if(playback==null||!apply.isEnabled())return;
  release();enabled(false);
  getSharedPreferences("wallpaper",0).edit().putBoolean("compatibility",compatibility).putString("path",file.getAbsolutePath()).remove("playback_error").apply();
  try{Intent intent=list?new Intent(WallpaperManager.ACTION_LIVE_WALLPAPER_CHOOSER):new Intent(WallpaperManager.ACTION_CHANGE_LIVE_WALLPAPER).putExtra(WallpaperManager.EXTRA_LIVE_WALLPAPER_COMPONENT,new ComponentName(this,VideoWallpaper.class));startActivity(intent);}
  catch(Exception e){play();status.setText("系统未打开设置，请尝试系统壁纸列表。");}
 }
 @Override protected void onResume(){super.onResume();active=true;if(surface!=null)play();}
 @Override protected void onPause(){active=false;release();super.onPause();}
 @Override public void surfaceCreated(SurfaceHolder h){play();}
 @Override public void surfaceChanged(SurfaceHolder h,int f,int w,int height){play();}
 @Override public void surfaceDestroyed(SurfaceHolder h){release();}
}
