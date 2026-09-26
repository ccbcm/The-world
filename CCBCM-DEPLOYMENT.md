# CCBCM 项目归属与继续开发

## 主项目

- GitHub 仓库：`https://github.com/ccbcm/The-world.git`
- 生产分支：`main`
- Cloudflare Pages 项目：`ccbcm`
- 自定义域名：`https://ccbcm.net`
- Pages 构建：`npm run build`，输出目录 `dist`

## 云端资源

- D1：`ccbcm-accounts`
- R2：`ccbcm-creator-assets`
- Resend 发信域名：`ccbcm.net`
- 生产环境变量：`EMAIL_FROM`、加密的 `RESEND_API_KEY`
- GitHub OAuth 密钥和 Resend 密钥只保存在 Cloudflare，不写入 Git。

## 账号和旧项目

CCBCM 主项目统一在 `ccbcm` GitHub 账号下维护。`piorunkulaga174` 账号的陆家嘴旧项目暂不删除，先保持独立并在确认没有 Cloudflare、域名、对象存储或其他项目依赖后再归档/设为私有。删除旧仓库前必须先导出历史和素材备份，并获得单独确认。

## 换电脑继续工作

登录有权限的 GitHub 账号后克隆主仓库，先阅读 `AGENTS.md` 和 `PROJECT-WORKFLOW.md`，再按流程继续。网站数据不在 Git 中：D1、R2、Cloudflare 环境变量和 Resend 域名仍由线上账号管理。
