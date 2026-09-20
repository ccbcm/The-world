using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Windows;
using System.Windows.Threading;
using Forms=System.Windows.Forms;
namespace Ccbcm {
 // Small UI-thread adapter over the public libVLC 3 ABI. Native callbacks never touch WPF.
 public sealed class VlcPlayer:Forms.Panel {
  const string D="libvlc.dll";
  [DllImport("kernel32",CharSet=CharSet.Unicode,SetLastError=true)] static extern bool SetDllDirectory(string path);
  [DllImport(D,CallingConvention=CallingConvention.Cdecl)] static extern IntPtr libvlc_new(int n,IntPtr args);
  [DllImport(D,CallingConvention=CallingConvention.Cdecl)] static extern void libvlc_release(IntPtr p);
  [DllImport(D,CallingConvention=CallingConvention.Cdecl)] static extern IntPtr libvlc_media_new_path(IntPtr p,byte[] path);
  [DllImport(D,CallingConvention=CallingConvention.Cdecl)] static extern void libvlc_media_add_option(IntPtr p,byte[] option);
  [DllImport(D,CallingConvention=CallingConvention.Cdecl)] static extern void libvlc_media_release(IntPtr p);
  [DllImport(D,CallingConvention=CallingConvention.Cdecl)] static extern IntPtr libvlc_media_player_new(IntPtr p);
  [DllImport(D,CallingConvention=CallingConvention.Cdecl)] static extern void libvlc_media_player_release(IntPtr p);
  [DllImport(D,CallingConvention=CallingConvention.Cdecl)] static extern void libvlc_media_player_set_media(IntPtr p,IntPtr m);
  [DllImport(D,CallingConvention=CallingConvention.Cdecl)] static extern void libvlc_media_player_set_hwnd(IntPtr p,IntPtr h);
  [DllImport(D,CallingConvention=CallingConvention.Cdecl)] static extern int libvlc_media_player_play(IntPtr p);
  [DllImport(D,CallingConvention=CallingConvention.Cdecl)] static extern void libvlc_media_player_set_pause(IntPtr p,int paused);
  [DllImport(D,CallingConvention=CallingConvention.Cdecl)] static extern void libvlc_media_player_stop(IntPtr p);
  [DllImport(D,CallingConvention=CallingConvention.Cdecl)] static extern int libvlc_media_player_get_state(IntPtr p);
  [DllImport(D,CallingConvention=CallingConvention.Cdecl)] static extern long libvlc_media_player_get_time(IntPtr p);
  [DllImport(D,CallingConvention=CallingConvention.Cdecl)] static extern long libvlc_media_player_get_length(IntPtr p);
  [DllImport(D,CallingConvention=CallingConvention.Cdecl)] static extern void libvlc_media_player_set_time(IntPtr p,long ms);
  [DllImport(D,CallingConvention=CallingConvention.Cdecl)] static extern void libvlc_video_set_mouse_input(IntPtr p,uint enabled);
  [DllImport(D,CallingConvention=CallingConvention.Cdecl)] static extern void libvlc_video_set_key_input(IntPtr p,uint enabled);
  [DllImport(D,CallingConvention=CallingConvention.Cdecl)] static extern void libvlc_video_set_crop_geometry(IntPtr p,byte[] geometry);
  [DllImport(D,CallingConvention=CallingConvention.Cdecl)] static extern void libvlc_video_set_scale(IntPtr p,float scale);
  [DllImport(D,CallingConvention=CallingConvention.Cdecl)] static extern uint libvlc_media_player_has_vout(IntPtr p);
  [DllImport(D,CallingConvention=CallingConvention.Cdecl)] static extern IntPtr libvlc_video_get_crop_geometry(IntPtr p);
  [DllImport(D,CallingConvention=CallingConvention.Cdecl)] static extern void libvlc_free(IntPtr p);
  IntPtr instance,player;DispatcherTimer poll;bool notified,wantsPause;Uri source;uint outputs;string crop="";
  // Crop to the host ratio, then auto-scale. Aspect-ratio override would stretch people.
  void FillSurface(bool force){if(player==IntPtr.Zero||ClientSize.Width<1||ClientSize.Height<1)return;int w=ClientSize.Width,h=ClientSize.Height,a=w,b=h;while(b!=0){int n=a%b;a=b;b=n;}string next=(w/a)+":"+(h/a);if(!force&&next==crop)return;libvlc_video_set_crop_geometry(player,Utf8(next));libvlc_video_set_scale(player,0);crop=next;}
  protected override void OnClientSizeChanged(EventArgs e){base.OnClientSizeChanged(e);FillSurface(true);}
  public string AppliedCrop {get{if(player==IntPtr.Zero)return "";IntPtr p=libvlc_video_get_crop_geometry(player);try{return p==IntPtr.Zero?"":Marshal.PtrToStringAnsi(p);}finally{if(p!=IntPtr.Zero)libvlc_free(p);}}}
  public event EventHandler MediaOpened,MediaEnded;
  public event Action<string> MediaFailed;
  static byte[] Utf8(string s){return System.Text.Encoding.UTF8.GetBytes(s+"\0");}
  public VlcPlayer(){Dock=Forms.DockStyle.Fill;BackColor=System.Drawing.Color.Black;}
  void Ensure(){if(player!=IntPtr.Zero)return;string root=Path.Combine(AppDomain.CurrentDomain.BaseDirectory,"vlc");if(!File.Exists(Path.Combine(root,"libvlc.dll")))throw new Exception("解码组件尚未安装，请安装官网新版插件。");SetDllDirectory(root);Environment.SetEnvironmentVariable("VLC_PLUGIN_PATH",Path.Combine(root,"plugins"));instance=libvlc_new(0,IntPtr.Zero);if(instance==IntPtr.Zero)throw new Exception("无法启动视频解码组件。");player=libvlc_media_player_new(instance);if(player==IntPtr.Zero)throw new Exception("无法创建视频播放器。");libvlc_media_player_set_hwnd(player,Handle);libvlc_video_set_mouse_input(player,0);libvlc_video_set_key_input(player,0);poll=new DispatcherTimer{Interval=TimeSpan.FromMilliseconds(100)};poll.Tick+=delegate{int state=libvlc_media_player_get_state(player);uint count=libvlc_media_player_has_vout(player);if(count!=outputs){outputs=count;if(count>0)FillSurface(true);}if(state==3&&!notified){FillSurface(true);notified=true;if(MediaOpened!=null)MediaOpened(this,EventArgs.Empty);if(wantsPause)Pause();}if(state==6){if(MediaEnded!=null)MediaEnded(this,EventArgs.Empty);}if(state==7){poll.Stop();if(MediaFailed!=null)MediaFailed("视频无法解码或文件已损坏，请尝试其他原文件。");}};}
  public Uri Source {get{return source;}set{Ensure();Close();source=value;if(value==null)return;IntPtr m=libvlc_media_new_path(instance,Utf8(value.LocalPath));if(m==IntPtr.Zero)throw new Exception("视频路径无法读取。");try{libvlc_media_add_option(m,Utf8(":no-audio"));libvlc_media_add_option(m,Utf8(":input-repeat=65535"));libvlc_media_add_option(m,Utf8(":avcodec-hw=any"));libvlc_media_player_set_media(player,m);}finally{libvlc_media_release(m);}notified=false;}}
  public TimeSpan Position {get{return TimeSpan.FromMilliseconds(player==IntPtr.Zero?0:Math.Max(0,libvlc_media_player_get_time(player)));}set{if(player!=IntPtr.Zero)libvlc_media_player_set_time(player,(long)value.TotalMilliseconds);}}
  public Duration NaturalDuration {get{long n=player==IntPtr.Zero?0:libvlc_media_player_get_length(player);return n>0?new Duration(TimeSpan.FromMilliseconds(n)):Duration.Automatic;}}
  public void Play(){if(player==IntPtr.Zero)return;wantsPause=false;int state=libvlc_media_player_get_state(player);if(state==4)libvlc_media_player_set_pause(player,0);else if(state!=3&&libvlc_media_player_play(player)!=0)throw new Exception("无法开始视频播放。");poll.Start();}
  public void Pause(){wantsPause=true;if(player!=IntPtr.Zero)libvlc_media_player_set_pause(player,1);}
  public void Close(){if(poll!=null)poll.Stop();if(player!=IntPtr.Zero){libvlc_media_player_stop(player);libvlc_media_player_set_media(player,IntPtr.Zero);}notified=false;outputs=0;crop="";}
  protected override void Dispose(bool disposing){Close();if(player!=IntPtr.Zero){libvlc_media_player_release(player);player=IntPtr.Zero;}if(instance!=IntPtr.Zero){libvlc_release(instance);instance=IntPtr.Zero;}base.Dispose(disposing);}
 }
}
