# CCBCM 作品社区样板

首页提供壁纸浏览、搜索、分类、作品详情与本地收藏；创作者页面分开陈列站内作品和注明出处的开源收录。注册、上传、审核和多人后台尚未接入。

- `/`：轻量作品首页，只加载封面与界面。
- `/#creator/ccbcm`：CCBCM 创作者主页。
- `/city.html`：原陆家嘴三维场景，主动进入才会加载。
- `/gallery/preview.html?id=waves`：隔离的动态预览页面。
- `gallery/app.js`：作品与作者目录。
- `authoring/上海陆家嘴.blend`：Blender 源工程。

运行 `npm run build`，Cloudflare Pages 发布 `dist/`。作品许可见 `licenses/gallery-sources.md` 和 `licenses/素材来源.md`。动态背景为网页效果；静态壁纸可下载 SVG。收藏保存在当前浏览器，不代表账号同步。
