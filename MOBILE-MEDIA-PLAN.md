# 高清壁纸与手机端进度

## 2026-09-20 本轮

- 用户确认先完成安卓和手机网站；iPhone / 原生鸿蒙安装包暂缓。
- 原有六件公开视频已从原文件提取高清 JPEG（长边最多 1920），未放大旧缩略图。新增上传单独保存 R2 封面及宽高，审核/下架权限与原作品一致。
- 网页接受 MP4 / MOV / WebM / MKV / PNG / JPG，200 MiB 单文件。浏览器不能解码的视频仍可上传，可另外补封面；这不表示浏览器已支持全部编码。
- Windows 改为动态链接 VideoLAN LibVLC 3.0.23.1。小型实际测试片 HEVC / VP9 / AV1 均成功打开、暂停、继续和循环；未宣称所有文件、DRM、损坏文件或所有显卡都兼容。
- 安装器下载三个固定校验值的原生组件分段，只从官网获取；在修改旧安装之前完成下载校验。保留静态壁纸、遮挡暂停、电池暂停、用户自启动选项。
- 安卓原生预览版直接使用 Android WallpaperService。通过固定官网清单与 SHA256 校验自动缓存公开作品；图片提供桌面/锁屏选择，视频打开系统动态壁纸确认页。隐藏、省电时暂停。编译和 lint 已通过；没有连接真机，品牌锁屏和视频解码能力尚未实机验收。
- 安卓 APK 为独立 preview 包名和调试签名，仅用于试用，不作为正式签名渠道；后续正式版需稳定保管发布签名。不要用本预览版的临时签名承诺无缝升级。
- 手机发现页只选竖屏作品；个人主页和下载不隐藏横屏作品。没有竖屏作品时显示空状态，不自动裁切创作者作品。所有端使用同一个账号和云端记录。

## 借鉴与边界

- Alynx Live Wallpaper：Apache-2.0，https://github.com/AlynxZhou/alynx-live-wallpaper 。参考视频裁切、后台暂停和独立 WallpaperService 思路，未复制其图标或视频。
- Android 官方服务：https://developer.android.com/reference/android/service/wallpaper/WallpaperService 。锁屏选项以系统实际提供为准。
- Apple：https://support.apple.com/en-us/120734 。iOS 17+ 可用 Live Photo 动态锁屏；普通 MP4 不是 Live Photo，网站不能自动设置系统壁纸。
- OpenHarmony 官方系统 API：https://github.com/openharmony/docs/blob/master/en/application-dev/reference/apis-basic-services-kit/js-apis-wallpaper-sys.md 。setVideo 为系统 API，普通第三方应用不能据此承诺可设置动态壁纸。
- VideoLAN 包与许可证见 authoring/wallpaper-player/VLC-NOTICE.txt，保留 COPYING.LIB 和可替换动态库。

## 仍待完成

- 安卓真机设置/重启/品牌锁屏/解码与耗电验证，正式发布签名。
- iPhone Live Photo 导出与原生鸿蒙可行入口（本轮用户暂缓）。
- 高分辨率视频硬件解码长时间压力测试、网页不支持编码的兼容预览转码任务。
- 原项目流程的多账号实机验收和插件状态回执仍保留，不因本次发布而标记全流程结束。
