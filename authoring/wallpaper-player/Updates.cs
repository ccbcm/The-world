using System;
using System.IO;
using System.Net;
using System.Diagnostics;
using System.Reflection;
using System.Security.Cryptography;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
using System.Windows.Forms;
[assembly: AssemblyTitle("CCBCM")]
[assembly: AssemblyProduct("CCBCM")]
[assembly: AssemblyFileVersion("0.4.0.0")]
[assembly: AssemblyVersion("0.4.0.0")]
namespace Ccbcm {
 static class Updates {
  const int Current=4;static bool busy;
  public class Release {public int versionCode;public string version,url,sha256;public long size;}
  public class Manifest {public Release windows;}
  static HttpWebResponse Request(string url){ServicePointManager.SecurityProtocol=SecurityProtocolType.Tls12;var r=(HttpWebRequest)WebRequest.Create(url);r.AllowAutoRedirect=false;r.Timeout=30000;r.ReadWriteTimeout=30000;r.CachePolicy=new System.Net.Cache.RequestCachePolicy(System.Net.Cache.RequestCacheLevel.NoCacheNoStore);return (HttpWebResponse)r.GetResponse();}
  static Release Latest(){using(var response=Request("https://ccbcm.net/downloads/latest.json?t="+DateTime.UtcNow.Ticks))using(var input=response.GetResponseStream())using(var bytes=new MemoryStream()){
   byte[] b=new byte[4096];int n;while((n=input.Read(b,0,b.Length))>0){if(bytes.Length+n>16384)throw new Exception("更新信息过大。");bytes.Write(b,0,n);}
   var release=new JavaScriptSerializer().Deserialize<Manifest>(System.Text.Encoding.UTF8.GetString(bytes.ToArray())).windows;
   if(release==null||!Regex.IsMatch(release.url??"",@"^https://ccbcm\.net/downloads/releases/CCBCM-Windows-[0-9.]+\.exe$")||!Regex.IsMatch(release.sha256??"",@"^[a-f0-9]{64}$")||release.size<100000||release.size>100L*1024*1024)throw new Exception("更新信息无效。");return release;
  }}
  static string Download(Release release){string folder=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"CCBCM","Updates");Directory.CreateDirectory(folder);string file=Path.Combine(folder,"CCBCM-"+release.versionCode+".exe"),part=file+".part";
   try{using(var response=Request(release.url))using(var input=response.GetResponseStream())using(var output=File.Create(part)){
    byte[] buffer=new byte[65536];int n;long total=0;while((n=input.Read(buffer,0,buffer.Length))>0){total+=n;if(total>release.size)throw new Exception("更新大小不符。");output.Write(buffer,0,n);}if(total!=release.size)throw new Exception("更新未下载完整。");
   }
   using(var sha=SHA256.Create())using(var input=File.OpenRead(part))if(BitConverter.ToString(sha.ComputeHash(input)).Replace("-","").ToLowerInvariant()!=release.sha256)throw new Exception("更新校验失败。");
   File.Copy(part,file,true);return file;
   }finally{if(File.Exists(part))File.Delete(part);}
  }
  public static async void Check(){if(busy)return;busy=true;
   try{var release=await Task.Run(()=>Latest());if(release.versionCode<=Current){MessageBox.Show("已经是最新版本 0.4.0。","CCBCM");return;}
    if(MessageBox.Show("发现新版本 "+release.version+"，现在下载并打开安装程序？现有设置会保留。","CCBCM",MessageBoxButtons.YesNo)!=DialogResult.Yes)return;
    string file=await Task.Run(()=>Download(release));Process.Start(new ProcessStartInfo(file){UseShellExecute=true});
   }catch(Exception e){MessageBox.Show("更新未完成："+e.Message,"CCBCM");}finally{busy=false;}
  }
 }
}
