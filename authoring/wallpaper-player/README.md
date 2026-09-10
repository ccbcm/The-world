# CCBCM 轻壁纸 · Windows 原型

独立的小型本地视频播放器，不随播放加载网站、作品库或浏览器。需要 Windows 桌面和 .NET Framework 4.x。当前仅支持主显示器；这不是 Windows 设置的原生动态壁纸扩展。

## 使用

1. 用 PowerShell 执行 `build.ps1` 编译，再双击 `Install.cmd` 安装到当前用户目录，无需管理员。
2. 打开桌面上的 CCBCM Wallpaper，选择 H.264 编码 MP4 视频。
3. 开机启动默认不新增；在设置中自行选择。关闭设置窗口后播放器继续运行，通过托盘退出可完全停止。
4. 可以将 `example.ccbwall` 中的 video 改为同目录视频文件名；安装后双击此文件切换壁纸。不会修改 MP4 默认打开方式。

支持循环、静音、单实例切换、手动暂停、锁屏暂停、电池暂停、主屏幕约 95% 被窗口覆盖时暂停。暂停超过 30 秒关闭媒体资源，恢复时重新打开并尝试回到之前位置；资源释放时显示原来的系统壁纸，恢复视频后重新显示动态层。覆盖检测为网格近似，不是游戏识别，透明窗口和特殊全屏程序仍需实测。解码是否硬件加速取决于系统、驱动及视频编码，不能承诺零资源占用。

桌面挂载依赖 Explorer WorkerW 窗口约定，并非微软承诺稳定的动态壁纸接口。Explorer 重启后当前原型需要重新选择视频；多屏、HDR、休眠恢复和各种 DPI 组合尚待验证。请勿将原型当作已全面验证的正式版本。

设置和日志位于 `%LOCALAPPDATA%\CCBCM\Wallpaper`。退出程序后可删除 `%LOCALAPPDATA%\Programs\CCBCMWallpaper` 中的程序；删除前先在设置关闭开机启动。

## 借鉴与实现

- [Lively Wallpaper](https://github.com/rocksdanister/lively)：GPL-3.0；参考其播放器与界面分离的架构思路，没有复制源代码或打包其组件。
- [Lively 性能文档](https://github.com/rocksdanister/lively/wiki/Performance)：覆盖暂停及视频/网页壁纸性能差异。
- [Microsoft MediaElement](https://learn.microsoft.com/en-us/dotnet/api/system.windows.controls.mediaelement)：系统媒体播放组件。
- [Microsoft SetParent](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setparent)：窗口父子关系 API。

`--test <video>` 运行 8 秒独立预览并写出测试日志，不挂载桌面、不保存壁纸选择。`--settings` 打开设置；`--background` 恢复上次视频；已运行时 `--pause`、`--resume`、`--exit` 通过当前用户的命名管道控制。测试结果中的 media_open_ms 是媒体打开事件时间，不是显示器上首帧出现时间。

## 本机验收（2026-09-10）

已在当前 Windows 11 桌面实测：原生窗口承载 WPF MediaElement，视频处于图标下面；蓝色演示视频播放截图采样变化 332，暂停变化 0，恢复变化 186。媒体打开事件约 0.32 秒，进程内部初始化至媒体打开约 0.56 秒；不是严格冷启动首帧基准。只有一个播放器进程，自启动关闭。播放工作集曾达到约 520 MiB，尚未达到低内存目标。多屏与其他 Windows 版本未验收。

新版桌面层级参考：https://github.com/rocksdanister/lively/issues/2074 。未下载或执行该项目二进制，未复制其实现。demo.mp4 是本地 FFmpeg 公式生成的蓝色渐变循环，没有外部素材。
