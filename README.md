# linkedin-mcp

**MCP server for publishing and scheduling LinkedIn posts through LinkedIn's official API.**

This project connects an AI assistant to a real external business platform through OAuth, MCP tools and the official LinkedIn API.

![MCP](https://img.shields.io/badge/MCP-server-8b5cf6?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10%2B-5ac8fa?style=for-the-badge)
![Official API](https://img.shields.io/badge/LinkedIn-official_API-0a66c2?style=for-the-badge)

## What it demonstrates

The interesting part is not posting text. It is the integration boundary:

```
AI assistant
    ↓
MCP tools
    ↓
OAuth / local token
    ↓
LinkedIn official API
    ↓
publish / schedule / history
```

The server handles authorization, structured tool calls, scheduling and local token storage without relying on scraping.

## Tools

| Tool | Purpose |
|---|---|
| `auth_status` | Inspect authorization state |
| `publish_now` | Publish immediately |
| `schedule_post` | Queue a post for later |
| `list_posts` | Read scheduled/published posts |
| `cancel_scheduled` | Cancel a queued post |
| `post_brief` | Create a structured content brief |
| `content_calendar` | Generate a sustainable posting cadence |

## Deliberate boundaries

The project does **not** implement:

- automated connection requests
- scraping
- mass messaging
- auto-like/comment bots
- engagement manipulation

It uses the official API and is intended for operating the owner's own LinkedIn account within LinkedIn's rules.

## Setup

Create a LinkedIn application and configure the OAuth credentials:

```bash
export LINKEDIN_CLIENT_ID=...
export LINKEDIN_CLIENT_SECRET=...
export LINKEDIN_REDIRECT_URI=http://localhost:8710/callback
```

Install:

```bash
git clone https://github.com/nadirzhon/linkedin-mcp
cd linkedin-mcp

python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Authorize:

```bash
python -m linkedin_mcp.auth
```

The token is stored locally under `~/.linkedin-mcp/`, not in the repository.

## MCP configuration

Example client configuration:

```json
{
  "mcpServers": {
    "linkedin": {
      "command": "python",
      "args": ["-m", "linkedin_mcp.server"],
      "env": {
        "LINKEDIN_CLIENT_ID": "...",
        "LINKEDIN_CLIENT_SECRET": "..."
      }
    }
  }
}
```

After connection, an assistant can compose content, request a structured brief and publish or schedule it through the MCP interface.

## Scheduling

Queued posts can be published by the included scheduler:

```cron
*/15 * * * * cd /path/to/linkedin-mcp && .venv/bin/python -m linkedin_mcp.scheduler >> ~/.linkedin-mcp/scheduler.log 2>&1
```

## Engineering highlights

- MCP tool design
- OAuth 2.0 / OpenID Connect integration
- official REST API integration
- local secure token storage
- scheduled background execution
- explicit capability boundaries
- AI-to-business-system integration

## Security

- credentials are loaded from environment/local token storage
- tokens are not committed to the repository
- actions are performed as the authorized account
- no scraping or unofficial automation layer

## License

MIT © nadirzhon
