using System;
using System.IO;
using System.Reflection;
using System.Diagnostics;
using System.Windows.Forms;
using Microsoft.Win32;
using System.Security.Cryptography;
using System.Net;
using System.IO.Compression;
using System.Web.Script.Serialization;
using System.Threading.Tasks;

class Setup {
 class Part { public string name; public string sha256; public int size; }
 class RuntimePackage { public string version; public Part[] parts; }
 static string Target=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"Programs","CCBCMWallpaper");
 static byte[] Resource(string name){using(var s=Assembly.GetExecutingAssembly().GetManifestResourceStream(name)){if(s==null)throw new Exception("安装文件不完整。");using(var m=new MemoryStream()){s.CopyTo(m);return m.ToArray();}}}
 static string PrepareRuntime(){
  var package=new JavaScriptSerializer().Deserialize<RuntimePackage>(System.Text.Encoding.UTF8.GetString(Resource("runtime")).TrimStart('\uFEFF'));
  string stage=Path.Combine(Path.GetTempPath(),"CCBCM-runtime-"+Guid.NewGuid().ToString("N"));Directory.CreateDirectory(stage);
  string archive=Path.Combine(stage,"runtime.zip"),unpacked=Path.Combine(stage,"vlc");
  try{ServicePointManager.SecurityProtocol=SecurityProtocolType.Tls12;using(var output=File.Create(archive))foreach(var part in package.parts){
   var request=(HttpWebRequest)WebRequest.Create("https://ccbcm.net/downloads/runtime/"+part.name);request.AllowAutoRedirect=false;request.Timeout=60000;request.ReadWriteTimeout=60000;
   using(var response=(HttpWebResponse)request.GetResponse())using(var input=response.GetResponseStream())using(var bytes=new MemoryStream()){
    byte[] buffer=new byte[65536];int n;while((n=input.Read(buffer,0,buffer.Length))>0){if(bytes.Length+n>part.size)throw new Exception("解码组件大小不符。");bytes.Write(buffer,0,n);}byte[] data=bytes.ToArray();
    using(var sha=SHA256.Create())if(data.Length!=part.size||BitConverter.ToString(sha.ComputeHash(data)).Replace("-","").ToLowerInvariant()!=part.sha256)throw new Exception("解码组件校验失败，请重试。");output.Write(data,0,data.Length);
   }
  }
  ZipFile.ExtractToDirectory(archive,unpacked);return stage;
  }catch{Directory.Delete(stage,true);throw;}
 }
 static void Install(){
  string stage=PrepareRuntime();try{InstallFiles(stage);}finally{Directory.Delete(stage,true);}
 }
 static void InstallFiles(string stage){
  string exe=Path.Combine(Target,"CCBCMWallpaper.exe");
  foreach(var p in Process.GetProcessesByName("CCBCMWallpaper")){using(p){try{if(String.Equals(p.MainModule.FileName,exe,StringComparison.OrdinalIgnoreCase)){using(var command=Process.Start(new ProcessStartInfo(exe,"--exit"){UseShellExecute=false,CreateNoWindow=true})){command.WaitForExit(3000);}if(!p.WaitForExit(5000))throw new Exception("请先从托盘退出 CCBCM 壁纸，再安装。");}}catch(System.ComponentModel.Win32Exception){throw new Exception("无法更新正在运行的壁纸，请先退出它。");}}}
  Directory.CreateDirectory(Target);
  foreach(string file in Directory.GetFiles(Path.Combine(stage,"vlc"),"*",SearchOption.AllDirectories)){string relative=file.Substring(Path.Combine(stage,"vlc").Length+1),dest=Path.Combine(Target,"vlc",relative);Directory.CreateDirectory(Path.GetDirectoryName(dest));File.Copy(file,dest,true);}
  File.WriteAllBytes(exe,Resource("player"));
  File.WriteAllBytes(Path.Combine(Target,"demo.mp4"),Resource("demo"));
  File.WriteAllText(Path.Combine(Target,"Blue.ccbwall"),"{\"video\":\"demo.mp4\"}");
  using(var k=Registry.CurrentUser.CreateSubKey(@"Software\Classes\CCBCM.Wallpaper\shell\open\command"))k.SetValue("","\""+exe+"\" \"%1\"");
  using(var k=Registry.CurrentUser.CreateSubKey(@"Software\Classes\.ccbwall")){if(k.GetValue("")==null)k.SetValue("","CCBCM.Wallpaper");}
  using(var k=Registry.CurrentUser.CreateSubKey(@"Software\Classes\.ccbwall\OpenWithProgids"))k.SetValue("CCBCM.Wallpaper","");
  using(var k=Registry.CurrentUser.CreateSubKey(@"Software\Classes\ccbcm-wallpaper")){k.SetValue("","URL:CCBCM Wallpaper");k.SetValue("URL Protocol","");}
  using(var k=Registry.CurrentUser.CreateSubKey(@"Software\Classes\ccbcm-wallpaper\shell\open\command"))k.SetValue("","\""+exe+"\" \"%1\"");
  dynamic shell=Activator.CreateInstance(Type.GetTypeFromProgID("WScript.Shell"));
  foreach(string folder in new[]{Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory),Environment.GetFolderPath(Environment.SpecialFolder.Programs)}){
   dynamic shortcut=shell.CreateShortcut(Path.Combine(folder,"CCBCM 动态壁纸.lnk"));shortcut.TargetPath=exe;shortcut.Arguments="--settings";shortcut.WorkingDirectory=Target;shortcut.Description="打开动态壁纸管理和官网";shortcut.Save();
   string legacy=Path.Combine(folder,"CCBCM Wallpaper.lnk");if(File.Exists(legacy)){dynamic old=shell.CreateShortcut(legacy);if(String.Equals((string)old.TargetPath,exe,StringComparison.OrdinalIgnoreCase))File.Delete(legacy);}
  }
  // Never add or change the user's auto-start preference during installation.
 }
 [STAThread] static int Main(string[] args){
  try{
   if(args.Length>0&&args[0]=="--verify"){using(var sha=SHA256.Create()){File.WriteAllText(Path.Combine(Path.GetTempPath(),"ccbcm-setup-verify.txt"),BitConverter.ToString(sha.ComputeHash(Resource("player"))).Replace("-","")+"\n"+Resource("demo").Length);}return 0;}
   if(args.Length>0&&args[0]=="--install"){Install();return 0;}
   Application.EnableVisualStyles();
   var form=new Form{Text="安装 CCBCM 壁纸",Width=470,Height=310,FormBorderStyle=FormBorderStyle.FixedDialog,MaximizeBox=false,MinimizeBox=false,StartPosition=FormStartPosition.CenterScreen};
   var title=new Label{Text="CCBCM 动态壁纸插件",Left=25,Top=25,Width=415,Height=40,Font=new System.Drawing.Font("Microsoft YaHei UI",15)};
   var note=new Label{Text="安装后，从桌面或官网选择壁纸即可使用。\n\n支持静态图片与多种视频编码。\n首次安装会下载解码组件，开机启动由你选择。",Left=25,Top=80,Width=410,Height=110};
   var button=new Button{Text="安装并打开",Left=25,Top=202,Width=410,Height=40};
   button.Click+=async delegate{button.Enabled=false;button.Text="正在下载并安装解码组件…";try{await Task.Run(()=>Install());Process.Start(new ProcessStartInfo(Path.Combine(Target,"CCBCMWallpaper.exe"),"--settings"){UseShellExecute=true});form.Close();}catch(Exception e){MessageBox.Show(e.Message,"安装未完成");button.Enabled=true;button.Text="重新安装";}};
   form.Controls.AddRange(new Control[]{title,note,button});Application.Run(form);return 0;
  }catch(Exception e){MessageBox.Show(e.Message,"CCBCM 安装未完成");return 1;}
 }
}
