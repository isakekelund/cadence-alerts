#!/usr/bin/env python3
"""Cadence Alerts opener on the Mac mini. A tapped notification in Chrome asks
http://127.0.0.1:8799/open?url=<Cadence address>, and this brings up the matching Dock app in ~/Applications
(News, Habits, ...) instead of a plain browser tab. It only listens on this Mac, only opens the ten Cadence
apps, and answers 404 to anything else, so the notification falls back to a normal tab.
Started at login by ~/Library/LaunchAgents/io.github.isakekelund.cadence-opener.plist."""
import http.server, os, subprocess, time, urllib.parse

CADENCE = 'https://claude.ai/artifact/JCcrHbJtuJMPXvsqPoTBSy'
APPS = {'': 'Cadence', 'calendar-app': 'Calendar', 'mail-app': 'Mail', 'reminders-app': 'Reminders',
        'progress-app': 'Pulse', 'cosmos-app': 'Cosmos', 'habits-app': 'Habits', 'money-app': 'Finance',
        'news-app': 'News'}
OTHER = {'https://claude.ai/artifact/4nv5dE8WseyHNCYh7heAhT': 'Hälsotränaren'}


def app_for(url):
    base, _, frag = url.partition('#')
    if base in OTHER: return OTHER[base]
    if base == CADENCE: return APPS.get(frag)
    return None


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        print(time.strftime('%H:%M:%S'), 'GET', self.path[:160], 'origin', self.headers.get('Origin'), flush=True)
        q = urllib.parse.urlparse(self.path)
        if q.path == '/ping':  # the Alerts page checks that it may reach this helper
            self.send_response(204)
            self.send_header('Access-Control-Allow-Origin', 'https://isakekelund.github.io')
            self.send_header('Access-Control-Allow-Private-Network', 'true')
            self.end_headers()
            return
        name = app_for(urllib.parse.parse_qs(q.query).get('url', [''])[0]) if q.path == '/open' else None
        path = os.path.expanduser(f'~/Applications/{name}.app') if name else None
        if path and os.path.isdir(path):
            subprocess.Popen(['open', path])
            self.send_response(204)
        else:
            self.send_response(404)
        self.send_header('Access-Control-Allow-Origin', 'https://isakekelund.github.io')
        self.send_header('Access-Control-Allow-Private-Network', 'true')
        self.end_headers()

    def do_OPTIONS(self):  # a browser's permission check before the real request: answer it, open nothing
        print(time.strftime('%H:%M:%S'), 'OPTIONS', self.path[:160], dict(self.headers), flush=True)
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', 'https://isakekelund.github.io')
        self.send_header('Access-Control-Allow-Private-Network', 'true')
        self.end_headers()

    def log_message(self, *a):
        pass


http.server.ThreadingHTTPServer(('127.0.0.1', 8799), Handler).serve_forever()
