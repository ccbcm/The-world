# ccbcm.net · 上海陆家嘴三维漫游

ccbcm.net 首页是可交互的上海陆家嘴三维场景，支持俯瞰、自由飞行、第三人称漫游、昼夜切换与画质选择。

Cloudflare Pages 执行 `npm run build`，并发布 `dist/`。`assets/` 是网页用的分块 glTF、角色、贴图与 HDRI；`authoring/` 保存 Blender 源文件和生成脚本，不会进入网站发布目录。

操作：WASD 移动，Shift 跑步，空格跳跃，鼠标拖动转动视角，滚轮调整第三人称距离。

资产许可和来源见 `licenses/素材来源.md`。地理数据来自 OpenStreetMap contributors。

