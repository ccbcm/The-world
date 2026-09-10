# GitHub accounts and download library

The site uses Cloudflare Pages Functions, a D1 binding named `DB`, and GitHub OAuth. No repository/email scopes are requested. GitHub tokens are used only to read the public identity and are not saved. Sessions use hashed random tokens and Secure/HttpOnly/SameSite cookies. Download queries derive the user ID from the server session, never from client input.

1. Create a D1 database and run `authoring/scripts/account-schema.sql`.
2. Bind it as `DB` in the Pages production settings.
3. Register a GitHub OAuth application: homepage `https://ccbcm.net`, callback `https://ccbcm.net/api/auth/callback`, no wildcard, no device flow.
4. Add `GITHUB_CLIENT_ID` and encrypted `GITHUB_CLIENT_SECRET` to Pages production variables. Never commit the secret.
5. Redeploy. Check `/api/account` returns `ready: true`, then sign in, save a wallpaper, log out and sign in again. Test a second account for isolation.

Until credentials are configured the interface clearly reports that login is being configured. Local IndexedDB data from the earlier prototype is not presented as cloud account storage. Wallpaper assets are shared immutable public files; each account stores its own download references instead of duplicating the files.

References reviewed: https://github.com/pilcrowonpaper/arctic ; https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps ; https://developers.cloudflare.com/pages/functions/bindings/ . This small integration uses standard fetch/Web Crypto rather than importing a full application framework.
