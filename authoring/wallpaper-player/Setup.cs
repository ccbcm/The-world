using System;
using System.IO;
using System.Reflection;
using System.Diagnostics;
using System.Windows.Forms;
using Microsoft.Win32;
using System.Security.Cryptography;

class Setup {
 static string Target=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"Programs","CCBCMWallpaper");
 static byte[] Resource(string name){using(var s=Assembly.GetExecutingAssembly().GetManifestResourceStream(name)){if(s==null)throw new Exception("安装文件不完整。");using(var m=new MemoryStream()){s.CopyTo(m);return m.ToArray();}}}
 static void Install(){
  string exe=Path.Combine(Target,"CCBCMWallpaper.exe");
  foreach(var p in Process.GetProcessesByName("CCBCMWallpaper")){using(p){try{if(String.Equals(p.MainModule.FileName,exe,StringComparison.OrdinalIgnoreCase)){using(var command=Process.Start(new ProcessStartInfo(exe,"--exit"){UseShellExecute=false,CreateNoWindow=true})){command.WaitForExit(3000);}if(!p.WaitForExit(5000))throw new Exception("请先从托盘退出 CCBCM 壁纸，再安装。");}}catch(System.ComponentModel.Win32Exception){throw new Exception("无法更新正在运行的壁纸，请先退出它。");}}}
  Directory.CreateDirectory(Target);
  File.WriteAllBytes(exe,Resource("player"));
  File.WriteAllBytes(Path.Combine(Target,"demo.mp4"),Resource("demo"));
  File.WriteAllText(Path.Combine(Target,"Blue.ccbwall"),"{\"video\":\"demo.mp4\"}");
  using(var k=Registry.CurrentUser.CreateSubKey(@"Software\Classes\CCBCM.Wallpaper\shell\open\command"))k.SetValue("","\""+exe+"\" \"%1\"");
  using(var k=Registry.CurrentUser.CreateSubKey(@"Software\Classes\.ccbwall")){if(k.GetValue("")==null)k.SetValue("","CCBCM.Wallpaper");}
  using(var k=Registry.CurrentUser.CreateSubKey(@"Software\Classes\.ccbwall\OpenWithProgids"))k.SetValue("CCBCM.Wallpaper","");
  dynamic shell=Activator.CreateInstance(Type.GetTypeFromProgID("WScript.Shell"));
  foreach(string folder in new[]{Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory),Environment.GetFolderPath(Environment.SpecialFolder.Programs)}){
   dynamic shortcut=shell.CreateShortcut(Path.Combine(folder,"CCBCM Wallpaper.lnk"));shortcut.TargetPath=exe;shortcut.Arguments="--settings";shortcut.WorkingDirectory=Target;shortcut.Description="选择视频，放到桌面上";shortcut.Save();
  }
  // Never add or change the user's auto-start preference during installation.
 }
 [STAThread] static int Main(string[] args){
  try{
   if(args.Length>0&&args[0]=="--verify"){using(var sha=SHA256.Create()){File.WriteAllText(Path.Combine(Path.GetTempPath(),"ccbcm-setup-verify.txt"),BitConverter.ToString(sha.ComputeHash(Resource("player"))).Replace("-","")+"\n"+Resource("demo").Length);}return 0;}
   if(args.Length>0&&args[0]=="--install"){Install();return 0;}
   Application.EnableVisualStyles();
   var form=new Form{Text="安装 CCBCM 壁纸",Width=470,Height=310,FormBorderStyle=FormBorderStyle.FixedDialog,MaximizeBox=false,MinimizeBox=false,StartPosition=FormStartPosition.CenterScreen};
   var title=new Label{Text="把喜欢的视频放到桌面上",Left=25,Top=25,Width=415,Height=40,Font=new System.Drawing.Font("Microsoft YaHei UI",15)};
   var note=new Label{Text="安装后，双击桌面的 CCBCM Wallpaper 就能使用。\n\n开机启动由你选择，默认不会开启。\n当前为视频壁纸预览版，暂不支持网页壁纸。",Left=25,Top=80,Width=410,Height=110};
   var button=new Button{Text="安装并打开",Left=25,Top=202,Width=410,Height=40};
   button.Click+=delegate{button.Enabled=false;try{Install();Process.Start(new ProcessStartInfo(Path.Combine(Target,"CCBCMWallpaper.exe"),"--settings"){UseShellExecute=true});form.Close();}catch(Exception e){MessageBox.Show(e.Message,"安装未完成");button.Enabled=true;}};
   form.Controls.AddRange(new Control[]{title,note,button});Application.Run(form);return 0;
  }catch(Exception e){MessageBox.Show(e.Message,"CCBCM 安装未完成");return 1;}
 }
}
