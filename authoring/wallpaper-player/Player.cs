using System;
using System.IO;
using System.IO.Pipes;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Threading;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Interop;
using System.Windows.Media;
using System.Windows.Threading;
using Microsoft.Win32;
using System.Web.Script.Serialization;
using Forms=System.Windows.Forms;

namespace Ccbcm {
 public class Config { public string LastFile=""; public bool PauseCovered=true; public bool PauseBattery=true; }
 public class Package { public string video; }
 public class Native {
  public delegate bool EnumProc(IntPtr h,IntPtr l);
  [StructLayout(LayoutKind.Sequential)] public struct Rect { public int Left,Top,Right,Bottom; }
  [DllImport("user32.dll",CharSet=CharSet.Unicode)] public static extern IntPtr FindWindow(string c,string t);
  [DllImport("user32.dll",CharSet=CharSet.Unicode)] public static extern IntPtr FindWindowEx(IntPtr p,IntPtr a,string c,string t);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc p,IntPtr l);
  [DllImport("user32.dll")] public static extern bool IsWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr h);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h,out Rect r);
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h,out uint p);
  [DllImport("user32.dll",CharSet=CharSet.Unicode)] public static extern int GetClassName(IntPtr h,System.Text.StringBuilder b,int n);
  [DllImport("user32.dll")] public static extern IntPtr SetParent(IntPtr c,IntPtr p);
  [DllImport("user32.dll")] public static extern bool SetLayeredWindowAttributes(IntPtr h,uint key,byte alpha,uint flags);
  [DllImport("user32.dll")] public static extern IntPtr GetParent(IntPtr h);
  [DllImport("user32.dll")] public static extern int GetWindowLong(IntPtr h,int i);
  [DllImport("user32.dll")] public static extern int SetWindowLong(IntPtr h,int i,int v);
  [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr h,IntPtr a,int x,int y,int w,int z,uint f);
  [DllImport("user32.dll")] public static extern IntPtr SendMessageTimeout(IntPtr h,uint m,IntPtr w,IntPtr l,uint f,uint t,out IntPtr r);
  [DllImport("dwmapi.dll")] public static extern int DwmGetWindowAttribute(IntPtr h,int a,out int v,int n);
  public static IntPtr Desktop() {
   IntPtr prog=FindWindow("Progman",null),result;if(prog==IntPtr.Zero)return IntPtr.Zero;
   SendMessageTimeout(prog,0x052C,IntPtr.Zero,IntPtr.Zero,2,1000,out result);
   if(FindWindowEx(prog,IntPtr.Zero,"SHELLDLL_DefView",null)!=IntPtr.Zero && FindWindowEx(prog,IntPtr.Zero,"WorkerW",null)!=IntPtr.Zero) return prog;
   IntPtr worker=IntPtr.Zero;
   EnumWindows(delegate(IntPtr h,IntPtr l){if(FindWindowEx(h,IntPtr.Zero,"SHELLDLL_DefView",null)!=IntPtr.Zero){IntPtr w=FindWindowEx(IntPtr.Zero,h,"WorkerW",null);if(w!=IntPtr.Zero)worker=w;}return true;},IntPtr.Zero);
   if(worker==IntPtr.Zero && FindWindowEx(prog,IntPtr.Zero,"SHELLDLL_DefView",null)!=IntPtr.Zero && FindWindowEx(prog,IntPtr.Zero,"WorkerW",null)!=IntPtr.Zero) return prog;
   return worker;
  }
  public static bool Covered(IntPtr own) {
   var screen=Forms.Screen.PrimaryScreen.Bounds;bool[] cells=new bool[160];int count=0;
   EnumWindows(delegate(IntPtr h,IntPtr l){
    if(h==own||!IsWindowVisible(h)||IsIconic(h))return true;
    uint pid;GetWindowThreadProcessId(h,out pid);if(pid==Process.GetCurrentProcess().Id)return true;
    var sb=new System.Text.StringBuilder(128);GetClassName(h,sb,128);string c=sb.ToString();if(c=="Progman"||FindWindowEx(h,IntPtr.Zero,"SHELLDLL_DefView",null)!=IntPtr.Zero)return false;if(c=="WorkerW"||c=="Progman"||c=="Shell_TrayWnd"||c=="Shell_SecondaryTrayWnd")return true;
    int cloaked; if(DwmGetWindowAttribute(h,14,out cloaked,4)==0&&cloaked!=0)return true;
    int ex=GetWindowLong(h,-20);if((ex&0x20)!=0)return true;
    Rect r;if(!GetWindowRect(h,out r))return true;
    for(int y=0;y<10;y++)for(int x=0;x<16;x++){int px=screen.Left+(int)((x+.5)*screen.Width/16),py=screen.Top+(int)((y+.5)*screen.Height/10),i=y*16+x;if(!cells[i]&&px>=r.Left&&px<r.Right&&py>=r.Top&&py<r.Bottom){cells[i]=true;count++;}}
    return count<152;
   },IntPtr.Zero);return count>=152;
  }
 }
 public class Surface:Forms.Form { protected override bool ShowWithoutActivation {get{return true;}} }
 public class Player:Application {
  static string Dir=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"CCBCM","Wallpaper");
  static string Settings=Path.Combine(Dir,"settings.json"),Sid=WindowsIdentity.GetCurrent().User.Value,Pipe="CCBCM.Wallpaper."+Sid;
  Config config=new Config();Surface wallpaper;Window settingsWindow;MediaElement media;Forms.NotifyIcon tray;DispatcherTimer timer;IntPtr hwnd,parent;
  string path="",reason="未选择壁纸";bool manual,locked,paused=true,released,test,desktopTest;int ticks;TimeSpan resume;DateTime pauseAt;Stopwatch launch=Stopwatch.StartNew(),switchWatch=new Stopwatch();double openedMs=-1;bool opened;TextBlock status;
  static JavaScriptSerializer Json=new JavaScriptSerializer();
  static void Log(string s){try{Directory.CreateDirectory(Dir);File.AppendAllText(Path.Combine(Dir,"player.log"),DateTime.Now.ToString("s")+" "+s+Environment.NewLine);}catch{}}
  [STAThread] public static void Main(string[] args){
   bool created;using(var mutex=new Mutex(true,"Local\\"+Pipe,out created)){
    string arg=args.Length>0?args[0]:"--settings";
    if(!created){try{using(var client=new NamedPipeClientStream(".",Pipe,PipeDirection.Out)){client.Connect(1800);using(var w=new BinaryWriter(client)){w.Write(arg);}}}catch(Exception e){Forms.MessageBox.Show("壁纸组件暂时没有响应，请稍后再试。\n"+e.Message,"CCBCM");}return;}
    if(arg=="--exit")return;
    try{var app=new Player();app.desktopTest=arg=="--desktop-test";app.test=arg=="--test"||app.desktopTest;app.Startup+=delegate{app.Init(app.test?(args.Length>1?args[1]:""):arg);};app.Run();}catch(Exception e){Log(e.ToString());Forms.MessageBox.Show(e.Message,"CCBCM 壁纸");}
   }
  }
  void Save(){Directory.CreateDirectory(Dir);string temp=Settings+".tmp";File.WriteAllText(temp,Json.Serialize(config));if(File.Exists(Settings))File.Replace(temp,Settings,null);else File.Move(temp,Settings);}
  public static string Resolve(string input){
   if(String.IsNullOrWhiteSpace(input)||input.StartsWith("\\\\")||input.Contains("://"))throw new Exception("请选择电脑里的视频文件。");
   string p=Path.GetFullPath(input);
   if(Path.GetExtension(p).Equals(".ccbwall",StringComparison.OrdinalIgnoreCase)){
    if(new FileInfo(p).Length>32768)throw new Exception("壁纸描述文件过大。");
    Package pack=Json.Deserialize<Package>(File.ReadAllText(p));if(pack==null||String.IsNullOrWhiteSpace(pack.video))throw new Exception("壁纸包缺少 video 字段。");
    p=Path.GetFullPath(Path.Combine(Path.GetDirectoryName(p),pack.video));
   }
   string ext=Path.GetExtension(p).ToLowerInvariant();if(p.StartsWith("\\\\")||!(ext==".mp4"||ext==".m4v"||ext==".wmv"))throw new Exception("第一版支持本地 MP4、M4V、WMV 视频。");
   if(!File.Exists(p))throw new Exception("找不到视频，可能已被移动。请重新选择。");return p;
  }
  void Init(string arg){
   ShutdownMode=ShutdownMode.OnExplicitShutdown;try{if(File.Exists(Settings))config=Json.Deserialize<Config>(File.ReadAllText(Settings))??new Config();}catch{Log("settings reset");}
   var menu=new Forms.ContextMenuStrip();menu.Items.Add("选择壁纸…",null,delegate{Pick();});menu.Items.Add("暂停 / 继续",null,delegate{manual=!manual;Update();});menu.Items.Add("设置",null,delegate{ShowSettings();});menu.Items.Add("退出",null,delegate{Shutdown();});
   tray=new Forms.NotifyIcon{Icon=System.Drawing.SystemIcons.Application,Text="CCBCM 轻壁纸",ContextMenuStrip=menu,Visible=!test};tray.DoubleClick+=delegate{ShowSettings();};
   wallpaper=new Surface{Text="CCBCM Wallpaper Surface",FormBorderStyle=Forms.FormBorderStyle.None,ShowInTaskbar=false,BackColor=System.Drawing.Color.Black,Width=960,Height=540};
   media=new MediaElement{LoadedBehavior=MediaState.Manual,UnloadedBehavior=MediaState.Manual,Stretch=Stretch.UniformToFill,Volume=0,IsMuted=true};var host=new System.Windows.Forms.Integration.ElementHost{Dock=Forms.DockStyle.Fill,Child=media};wallpaper.Controls.Add(host);
   media.MediaOpened+=delegate{opened=true;openedMs=switchWatch.Elapsed.TotalMilliseconds;Log("media_open_ms="+openedMs.ToString("F1")+" process_ready_ms="+launch.ElapsedMilliseconds);if(resume>TimeSpan.Zero){media.Position=resume;resume=TimeSpan.Zero;}if(paused)media.Pause();else if(!wallpaper.Visible){wallpaper.Show();FixComposition();}};
   media.MediaEnded+=delegate{media.Position=TimeSpan.Zero;if(!paused)media.Play();};media.MediaFailed+=delegate(object sender,ExceptionRoutedEventArgs e){reason="无法播放：请使用 H.264 MP4 视频";Log(e.ErrorException.ToString());wallpaper.Hide();if(!test)Forms.MessageBox.Show(reason,"CCBCM");};
   hwnd=wallpaper.Handle;
   if(!test){var thread=new Thread(Listen){IsBackground=true};thread.Start();SystemEvents.SessionSwitch+=Session;SystemEvents.DisplaySettingsChanged+=Display;}
   timer=new DispatcherTimer{Interval=TimeSpan.FromSeconds(1)};timer.Tick+=delegate{ticks++;Update();if(test){if(ticks==3){manual=true;Update();Log("test_pause="+paused);}if(ticks==5){manual=false;Update();Log("test_resume="+!paused);}if(ticks==8){File.WriteAllText(Path.Combine(Dir,"test-result.json"),Json.Serialize(new{opened,openedMs,position=media.Position.TotalSeconds,workingSet=Process.GetCurrentProcess().WorkingSet64,desktopAttached=parent!=IntPtr.Zero&&Native.GetParent(hwnd)==parent,paused}));Shutdown();}}};timer.Start();
   if(test)Open(arg);else if(arg=="--settings"){if(File.Exists(config.LastFile))Open(config.LastFile);ShowSettings();}else if(arg=="--background"){if(File.Exists(config.LastFile))Open(config.LastFile);}else Open(arg);
  }
  void Listen(){while(true){try{var security=new PipeSecurity();security.AddAccessRule(new PipeAccessRule(WindowsIdentity.GetCurrent().User,PipeAccessRights.FullControl,AccessControlType.Allow));using(var server=new NamedPipeServerStream(Pipe,PipeDirection.In,1,PipeTransmissionMode.Byte,PipeOptions.None,4096,4096,security)){server.WaitForConnection();using(var reader=new BinaryReader(server)){string arg=reader.ReadString();Dispatcher.BeginInvoke(new Action(delegate{if(arg=="--exit")Shutdown();else if(arg=="--settings")ShowSettings();else if(arg=="--pause"){manual=true;Update();}else if(arg=="--resume"){manual=false;Update();}else Open(arg);}));}}}catch{Thread.Sleep(300);}}}
  void Attach(){parent=Native.Desktop();if(parent==IntPtr.Zero)throw new Exception("没有找到兼容的桌面层。播放器已停止，不会覆盖你的桌面。可以先使用测试预览。");int style=Native.GetWindowLong(hwnd,-16);Native.SetWindowLong(hwnd,-16,(style&~unchecked((int)0x80000000))|0x40000000);if(Native.FindWindowEx(parent,IntPtr.Zero,"SHELLDLL_DefView",null)!=IntPtr.Zero){Native.SetWindowLong(hwnd,-20,Native.GetWindowLong(hwnd,-20)|0x80000|0x08000000);}Native.SetParent(hwnd,parent);if(Native.GetParent(hwnd)!=parent)throw new Exception("桌面挂载失败，已停止播放。");var r=Forms.Screen.PrimaryScreen.Bounds;Native.SetWindowPos(hwnd,Native.FindWindowEx(parent,IntPtr.Zero,"SHELLDLL_DefView",null),r.Left,r.Top,r.Width,r.Height,0x10);Dispatcher.BeginInvoke(DispatcherPriority.ContextIdle,new Action(FixComposition));Log("desktop_attached");}
  void FixComposition(){if(parent!=IntPtr.Zero&&Native.FindWindowEx(parent,IntPtr.Zero,"SHELLDLL_DefView",null)!=IntPtr.Zero){Native.SetWindowLong(hwnd,-20,Native.GetWindowLong(hwnd,-20)|0x80000|0x08000000);Log("layered="+Native.SetLayeredWindowAttributes(hwnd,0,255,2));}}
  void Open(string input){try{string file=Resolve(input);if((!test||desktopTest)&&!Native.IsWindow(parent))Attach();switchWatch.Restart();media.Close();path=file;resume=TimeSpan.Zero;released=false;manual=false;paused=false;media.Source=new Uri(file);wallpaper.Show();Dispatcher.BeginInvoke(DispatcherPriority.ContextIdle,new Action(FixComposition));if(!test){var r=Forms.Screen.PrimaryScreen.Bounds;Native.SetWindowPos(hwnd,Native.FindWindowEx(parent,IntPtr.Zero,"SHELLDLL_DefView",null),r.Left,r.Top,r.Width,r.Height,0x10);}media.Play();if(!test){config.LastFile=file;Save();}Update();}catch(Exception e){Log(e.Message);if(!test)Forms.MessageBox.Show(e.Message,"CCBCM 壁纸");}}
  void Update(){if(path=="")return;bool battery=config.PauseBattery&&Forms.SystemInformation.PowerStatus.PowerLineStatus==Forms.PowerLineStatus.Offline;bool covered=!test&&config.PauseCovered&&Native.Covered(hwnd);bool stop=manual||locked||battery||covered;
   reason=manual?"已暂停":locked?"锁屏暂停":battery?"电池模式暂停":covered?"桌面被遮挡，已暂停":"正在播放";
   if(!test&&!Native.IsWindow(parent)){media.Pause();wallpaper.Hide();reason="桌面已重启，请重新选择壁纸";stop=true;}
   if(stop&&!paused){media.Pause();paused=true;pauseAt=DateTime.UtcNow;Log("pause: "+reason);}
   if(stop&&paused&&!released&&(DateTime.UtcNow-pauseAt).TotalSeconds>30){resume=media.Position;wallpaper.Hide();media.Close();released=true;Log("media released");}
   if(!stop&&paused){if(released){switchWatch.Restart();media.Source=new Uri(path);released=false;}media.Play();paused=false;Log("resume");}
   if(status!=null)status.Text=reason+"\n"+(path==""?"还没有选择壁纸":Path.GetFileName(path));
  }
  void Session(object s,SessionSwitchEventArgs e){Dispatcher.BeginInvoke(new Action(delegate{if(e.Reason==SessionSwitchReason.SessionLock)locked=true;if(e.Reason==SessionSwitchReason.SessionUnlock)locked=false;Update();}));}
  void Display(object s,EventArgs e){Dispatcher.BeginInvoke(new Action(delegate{if(path!="")try{Attach();}catch{media.Pause();wallpaper.Hide();}}));}
  void Pick(){var f=new OpenFileDialog{Title="选一段喜欢的视频",Filter="视频与壁纸|*.mp4;*.m4v;*.wmv;*.ccbwall"};if(f.ShowDialog()==true)Open(f.FileName);}
  bool StartupEnabled(){using(var k=Registry.CurrentUser.OpenSubKey("Software\\Microsoft\\Windows\\CurrentVersion\\Run")){return k!=null&&k.GetValue("CCBCM Wallpaper")!=null;}}
  void StartupSet(bool enabled){using(var k=Registry.CurrentUser.CreateSubKey("Software\\Microsoft\\Windows\\CurrentVersion\\Run")){if(enabled)k.SetValue("CCBCM Wallpaper","\""+Process.GetCurrentProcess().MainModule.FileName+"\" --background");else k.DeleteValue("CCBCM Wallpaper",false);}}
  void ShowSettings(){if(settingsWindow!=null){settingsWindow.Activate();return;}settingsWindow=new Window{Title="CCBCM · 轻壁纸",Width=440,Height=400,ResizeMode=ResizeMode.NoResize,WindowStartupLocation=WindowStartupLocation.CenterScreen,Background=new SolidColorBrush(Color.FromRgb(27,27,34)),Foreground=Brushes.White};var panel=new StackPanel{Margin=new Thickness(28)};panel.Children.Add(new TextBlock{Text="换个喜欢的风景",FontSize=25,Margin=new Thickness(0,0,0,14)});status=new TextBlock{Text=reason+"\n视频在本机播放，关掉此窗口后仍可运行。",TextWrapping=TextWrapping.Wrap,Margin=new Thickness(0,0,0,18)};panel.Children.Add(status);
   var pick=new Button{Content="选择视频…",Padding=new Thickness(12),Margin=new Thickness(0,0,0,15)};pick.Click+=delegate{Pick();};panel.Children.Add(pick);
   AddCheck(panel,"开机时自动播放",StartupEnabled(),StartupSet);AddCheck(panel,"桌面被遮住时暂停",config.PauseCovered,delegate(bool b){config.PauseCovered=b;Save();Update();});AddCheck(panel,"使用电池时暂停",config.PauseBattery,delegate(bool b){config.PauseBattery=b;Save();Update();});
   var quit=new Button{Content="退出壁纸组件",Padding=new Thickness(8),Margin=new Thickness(0,18,0,0)};quit.Click+=delegate{Shutdown();};panel.Children.Add(quit);settingsWindow.Content=panel;settingsWindow.Closed+=delegate{settingsWindow=null;status=null;};settingsWindow.Show();Update();}
  void AddCheck(StackPanel p,string title,bool state,Action<bool> change){var c=new CheckBox{Content=title,IsChecked=state,Foreground=Brushes.White,Margin=new Thickness(0,6,0,6)};c.Checked+=delegate{change(true);};c.Unchecked+=delegate{change(false);};p.Children.Add(c);}
  protected override void OnExit(ExitEventArgs e){if(timer!=null)timer.Stop();SystemEvents.SessionSwitch-=Session;SystemEvents.DisplaySettingsChanged-=Display;if(media!=null)media.Close();if(wallpaper!=null)wallpaper.Dispose();if(tray!=null){tray.Visible=false;tray.Dispose();}Log("exit");base.OnExit(e);}
 }
}
