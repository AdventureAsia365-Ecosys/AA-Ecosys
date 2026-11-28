#!/usr/bin/env python3
"""Post a Jira comment as the tech lead (REST v2 + his API token), so it carries no "Claude with ..." label (S297).

Usage:
  python3 tools/jira/post_comment.py --issue PR-31 --body-file draft.txt [--image a.png ...]            # dry run
  python3 tools/jira/post_comment.py --issue PR-31 --body-file draft.txt [--image a.png ...] --post     # post

The body is Jira wiki markup: mention `[~accountid:<id>]`, numbered list `# `, bold `*...*`. Each `--image` is
uploaded as an attachment and appended as `!<file name>|width=900!` in the given order. The token file (outside the
repo, ask the tech lead before each use) holds two non-empty lines: the Atlassian e-mail, then the API token. The
token is never printed. A 401 means the token expired: the tech lead creates a new one (id.atlassian.com > Security >
API tokens). Skill: aa-jira-update ("Kết nối").
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

SITE = "https://adventure-asia.atlassian.net"
TOKEN_FILE = Path("/home/nghiep/projects/secret_manager/Jira/jira-token")


def auth_header(token_file: Path) -> str:
    lines = [x.strip() for x in token_file.read_text().splitlines() if x.strip()]
    if len(lines) < 2:
        raise SystemExit("token file needs two non-empty lines: e-mail, then token")
    return "Basic " + base64.b64encode(f"{lines[0]}:{lines[1]}".encode()).decode()


def call(auth: str, method: str, path: str, data: bytes | None = None, headers: dict | None = None):
    req = urllib.request.Request(SITE + path, data=data, method=method)
    req.add_header("Authorization", auth)
    req.add_header("Accept", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read()[:300].decode(errors="replace")}


def multipart(path: Path) -> tuple[bytes, str]:
    boundary = uuid.uuid4().hex
    head = (
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
        f"Content-Type: {mimetypes.guess_type(path.name)[0] or 'application/octet-stream'}\r\n\r\n"
    ).encode()
    return head + path.read_bytes() + f"\r\n--{boundary}--\r\n".encode(), boundary


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--issue", required=True)
    ap.add_argument("--body-file", required=True, type=Path)
    ap.add_argument("--image", action="append", default=[], type=Path)
    ap.add_argument("--token-file", type=Path, default=TOKEN_FILE)
    ap.add_argument("--post", action="store_true")
    a = ap.parse_args(argv)

    auth = auth_header(a.token_file)
    status, me = call(auth, "GET", "/rest/api/2/myself")
    print("myself", status, (me or {}).get("displayName"))
    if status != 200:
        return 1
    body = a.body_file.read_text()
    if a.image:
        body = body.rstrip() + "\n\n" + "\n\n".join(f"!{p.name}|width=900!" for p in a.image)
    if not a.post:
        print(f"dry run: would attach {len(a.image)} image(s) and post {len(body)} characters on {a.issue}")
        return 0
    for p in a.image:
        data, boundary = multipart(p)
        st, res = call(auth, "POST", f"/rest/api/2/issue/{a.issue}/attachments", data,
                       {"X-Atlassian-Token": "no-check", "Content-Type": f"multipart/form-data; boundary={boundary}"})
        print("attach", p.name, st)
        if st not in (200, 201):
            print(res)
            return 1
    st, res = call(auth, "POST", f"/rest/api/2/issue/{a.issue}/comment", json.dumps({"body": body}).encode(),
                   {"Content-Type": "application/json"})
    print("comment", st, (res or {}).get("id"), ((res or {}).get("author") or {}).get("displayName"))
    return 0 if st == 201 else 1


if __name__ == "__main__":
    sys.exit(main())
