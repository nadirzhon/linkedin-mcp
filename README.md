<div align="center">

# linkedin-mcp

**Publish and schedule posts on your own LinkedIn — from an AI assistant, via the official API.**

[![MCP](https://img.shields.io/badge/MCP-server-8b5cf6?style=for-the-badge)](https://modelcontextprotocol.io)
[![Python](https://img.shields.io/badge/python-3.10%2B-5ac8fa?style=for-the-badge)](pyproject.toml)
[![Official API](https://img.shields.io/badge/LinkedIn-official_API-0a66c2?style=for-the-badge)](https://learn.microsoft.com/linkedin/)

An MCP server that lets Claude (or any MCP client) write a post and **publish or
schedule it on your LinkedIn profile** through LinkedIn's official Posts API.
Plus a content-calendar helper so you grow the profile the sustainable way.

</div>

---

## ✅ What it does — and what it deliberately doesn't

**Does:** posts as *you* (immediately or scheduled), lists your queue and
history, and gives you proven post structures + a weekly cadence.

**Does NOT:** auto-connect, auto-like, auto-comment, mass-message, scrape, or
run engagement bots. Those violate [LinkedIn's User Agreement](https://www.linkedin.com/legal/user-agreement)
and get accounts **permanently banned**. There is no official API for them —
only grey scraping — and it's not worth risking your account. Profiles grow from
consistent, valuable content, not automation. That's what this tool supports.

## Tools

| Tool | What it does |
|---|---|
| `auth_status` | Is the tool authorized, and as whom |
| `publish_now(text, visibility)` | Post immediately (PUBLIC / CONNECTIONS) |
| `schedule_post(text, when)` | Queue for later (`+2h`, `+1d`, or ISO time) |
| `list_posts(kind)` | Scheduled queue + published history |
| `cancel_scheduled(id)` | Remove a queued post |
| `post_brief(topic, archetype)` | Structured brief + rules to write a strong post |
| `content_calendar()` | Safe weekly cadence and best-practice rules |

## Setup

### 1. Create a LinkedIn app (once, ~10 min)

1. Go to **[developer.linkedin.com](https://developer.linkedin.com/) → My apps → Create app**.
2. Fill in name, associate a LinkedIn **Page** (create a simple one if you don't have it — required by LinkedIn), upload a logo.
3. Open your app → **Auth** tab:
   - Copy the **Client ID** and **Client Secret**.
   - Under **OAuth 2.0 redirect URLs**, add exactly: `http://localhost:8710/callback`
4. Open the **Products** tab and request:
   - **Sign In with LinkedIn using OpenID Connect** (gives `openid profile`)
   - **Share on LinkedIn** (gives `w_member_social` — the posting scope)

   These are self-serve for personal use and usually approve instantly. If a
   scope isn't yet granted, the auth step below will tell you which one is missing.

### 2. Install

```bash
cd linkedin-mcp
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

### 3. Authorize the tool (once)

Put your credentials in the environment (or `~/.linkedin-mcp/token.json`):

```bash
export LINKEDIN_CLIENT_ID=xxxxxxxx
export LINKEDIN_CLIENT_SECRET=xxxxxxxx
export LINKEDIN_REDIRECT_URI=http://localhost:8710/callback

python -m linkedin_mcp.auth
```

A browser opens LinkedIn's consent page → approve → the token is saved to
`~/.linkedin-mcp/token.json` (chmod 600). Done.

### 4. Connect to Claude

Add to your MCP client config (e.g. Claude Desktop `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "linkedin": {
      "command": "python",
      "args": ["-m", "linkedin_mcp.server"],
      "env": {
        "LINKEDIN_CLIENT_ID": "xxxxxxxx",
        "LINKEDIN_CLIENT_SECRET": "xxxxxxxx"
      }
    }
  }
}
```

Now you can say: *"Write a build-in-public post about my AST taint scanner and
publish it"* — the assistant uses `post_brief` to shape it, then `publish_now`.

### 5. Auto-posting on a schedule

`schedule_post` queues posts; a small scheduler publishes the due ones. Run it
from cron so posts go out even when you're offline:

```cron
*/15 * * * * cd /path/to/linkedin-mcp && .venv/bin/python -m linkedin_mcp.scheduler >> ~/.linkedin-mcp/scheduler.log 2>&1
```

## How growth actually works here

Ask the assistant for `content_calendar()` — it returns a Mon/Wed/Fri cadence
and rules (hook first, be specific, one idea, real numbers, end with a question).
Then generate posts with `post_brief` and schedule a week at a time. Consistency
+ substance is what moves a profile — and it can't be taken away by a ban.

## Security & privacy

- Token and posts are stored locally under `~/.linkedin-mcp/` (chmod 600), never in the repo.
- The tool only calls the official LinkedIn API and only acts as you.
- Access tokens expire (~60 days); the client auto-refreshes when a refresh token is present, otherwise re-run `python -m linkedin_mcp.auth`.

## License

MIT © nadirzhon — for use on your own LinkedIn account, within LinkedIn's terms.
