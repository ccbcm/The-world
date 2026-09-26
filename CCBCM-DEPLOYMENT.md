# CCBCM 项目归属与继续开发

## 主项目

- GitHub 仓库：`https://github.com/ccbcm/The-world.git`
- 生产分支：`main`
- Cloudflare Pages 项目：`ccbcm`
- 自定义域名：`https://ccbcm.net`
- Pages 构建：`npm run build`，输出目录 `dist`
- 已核验仓库所有权：`ccbcm` 会话可见“你拥有 ccbcm/The-world”；Cloudflare Pages 的 Git 仓库也显示为 `ccbcm/The-world`。
- Pages 生产分支为 `main`，自动部署已启用，GitHub App 安装绑定在 CCBCM 账户侧。
- 本地仓库的 Git 身份已单独设置为 `ccbcm <ccbcm4263@gmail.com>`；只作用于本仓库，系统全局身份仍保留给其他项目。

## 云端资源

- D1：`ccbcm-accounts`
- R2：`ccbcm-creator-assets`
- Resend 发信域名：`ccbcm.net`
- 生产环境变量：`EMAIL_FROM`、加密的 `RESEND_API_KEY`
- GitHub OAuth 密钥和 Resend 密钥只保存在 Cloudflare，不写入 Git。

## 账号和旧项目

CCBCM 主项目统一在 `ccbcm` GitHub 账号下维护。`piorunkulaga174` 账号的陆家嘴旧项目暂不删除，先保持独立并在确认没有 Cloudflare、域名、对象存储或其他项目依赖后再归档/设为私有。删除旧仓库前必须先导出历史和素材备份，并获得单独确认。

桌面 Chrome 当前会话访问仓库设置返回 404，不能据此判断项目归属错误；应以已登录 `ccbcm` 会话中显示的仓库所有权和 Cloudflare Pages 绑定为准。

## 换电脑继续工作

登录有权限的 GitHub 账号后克隆主仓库，先阅读 `AGENTS.md` 和 `PROJECT-WORKFLOW.md`，再按流程继续。网站数据不在 Git 中：D1、R2、Cloudflare 环境变量和 Resend 域名仍由线上账号管理。

Codex/Codex Web 的 GitHub 授权属于登录会话或连接器层面，不由项目代码决定。继续 CCBCM 时应使用已能访问 `ccbcm/The-world` 的 `ccbcm` 会话；病例项目仍使用它自己的 `piorunkulaga174` 会话。两者通过仓库远程地址和本地 Git 身份分流，不共享提交目标。
