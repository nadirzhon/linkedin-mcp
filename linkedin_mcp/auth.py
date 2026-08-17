"""
One-time OAuth flow to authorize the tool to post on your LinkedIn.

Run once:  python -m linkedin_mcp.auth

It opens LinkedIn's consent page in your browser, catches the redirect on a
tiny local server, exchanges the code for a token and saves it to
~/.linkedin-mcp/token.json. After that the MCP server and scheduler can post.

Requires LINKEDIN_CLIENT_ID / LINKEDIN_CLIENT_SECRET (env or token.json) and the
redirect URI to be registered in your LinkedIn app (default
http://localhost:8710/callback).
"""

from __future__ import annotations

import secrets
import sys
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

from . import client, config

_STATE = secrets.token_urlsafe(16)
_result: dict[str, str] = {}


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.urlparse(self.path)
        if not q.path.startswith("/callback"):
            self.send_response(404)
            self.end_headers()
            return
        params = urllib.parse.parse_qs(q.query)
        _result["code"] = (params.get("code") or [""])[0]
        _result["state"] = (params.get("state") or [""])[0]
        _result["error"] = (params.get("error_description") or params.get("error") or [""])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        msg = "Готово — можно вернуться в терминал и закрыть эту вкладку." if _result.get("code") \
            else f"Ошибка авторизации: {_result.get('error')}"
        self.wfile.write(f"<html><body style='font:16px sans-serif;padding:3rem'>{msg}</body></html>".encode())

    def log_message(self, *a):
        pass


def run() -> int:
    cid, secret, redirect = config.client_credentials()
    if not cid or not secret:
        sys.stderr.write(
            "Не заданы LINKEDIN_CLIENT_ID / LINKEDIN_CLIENT_SECRET.\n"
            "Задайте их в переменных окружения или в ~/.linkedin-mcp/token.json,\n"
            "и зарегистрируйте redirect URI в приложении LinkedIn (см. README).\n")
        return 2

    parsed = urllib.parse.urlparse(redirect)
    port = parsed.port or 8710

    auth_url = config.AUTH_URL + "?" + urllib.parse.urlencode({
        "response_type": "code",
        "client_id": cid,
        "redirect_uri": redirect,
        "state": _STATE,
        "scope": config.SCOPES,
    })
    print("Открываю LinkedIn для авторизации…\nЕсли не открылось — перейдите вручную:\n" + auth_url)
    try:
        webbrowser.open(auth_url)
    except Exception:
        pass

    srv = HTTPServer(("127.0.0.1", port), _Handler)
    srv.handle_request()  # обслуживаем один редирект и выходим
    srv.server_close()

    if _result.get("error"):
        sys.stderr.write(f"Авторизация отклонена: {_result['error']}\n")
        return 1
    if _result.get("state") != _STATE:
        sys.stderr.write("Несовпадение state — прерываю ради безопасности.\n")
        return 1
    if not _result.get("code"):
        sys.stderr.write("Не получен код авторизации.\n")
        return 1

    try:
        client.exchange_code(_result["code"])
        who = client.userinfo()
        name = who.get("name") or who.get("given_name") or "профиль"
        print(f"✓ Авторизовано как: {name}. Токен сохранён в {config.TOKEN_FILE}")
        return 0
    except client.LinkedInError as e:
        sys.stderr.write(f"Ошибка получения токена: {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(run())
