#!/usr/bin/env python3
"""개발 블로그 글 1편을 발행한다 (템플릿 적용 → 목록 갱신 → commit → push).

push 인증은 실행 환경의 GitHub 연결을 그대로 사용한다. 토큰을 넘기지 않는다.

사용법:
    python3 publish.py \
        --title "Kotlin Flow 디바운스 처리" \
        --tags "Android,Kotlin,튜토리얼" \
        --summary "검색어 입력에 debounce 300ms 적용해 API 호출을 1/8로 줄인 과정" \
        --slug 2026-08-11-kotlin-flow-debounce \
        --body body.html

--body 에는 <article class="article-body"> 안에 들어갈 **본문 조각만** 넣는다.
(<html>, <head>, <header>, <footer> 등은 템플릿이 자동으로 붙인다)

옵션:
    --date YYYY-MM-DD   기본값: 오늘(KST)
    --slug my-slug      기본값: 날짜 + 제목 슬러그
    --no-push           로컬 파일만 생성하고 commit·push 하지 않음
"""

import argparse
import hashlib
import html
import json
import pathlib
import re
import subprocess
import sys
from datetime import datetime, timezone, timedelta

ROOT = pathlib.Path(__file__).parent
KST = timezone(timedelta(hours=9))
SITE = "https://bluaura.github.io/devblog"


def sh(*cmd, check=True):
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip()
    if check and r.returncode != 0:
        print(f"$ {' '.join(cmd)}\n{out}", file=sys.stderr)
        sys.exit(f"명령 실패 (exit {r.returncode})")
    return out


def slugify(title: str) -> str:
    """URL-safe ASCII 슬러그. 한글 제목이면 해시로 대체해 인코딩 문제를 피한다."""
    s = re.sub(r"[^A-Za-z0-9\s-]", " ", title).strip().lower()
    s = re.sub(r"[\s_]+", "-", s).strip("-")
    if len(s) < 4:
        s = "post-" + hashlib.md5(title.encode("utf-8")).hexdigest()[:8]
    return s[:60]


def push():
    """origin/main 을 rebase 한 뒤 push 한다. 실패하면 우회하지 않고 중단한다."""
    r = subprocess.run(["git", "pull", "--rebase", "-q", "origin", "main"],
                       cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        subprocess.run(["git", "rebase", "--abort"], cwd=ROOT, capture_output=True)
        print((r.stdout + r.stderr).strip(), file=sys.stderr)
        sys.exit("rebase 실패 — 커밋은 로컬에 남아 있습니다. 원격 변경을 확인한 뒤 다시 push 하세요.")

    r = subprocess.run(["git", "push", "-q", "origin", "main"],
                       cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        print((r.stdout + r.stderr).strip(), file=sys.stderr)
        sys.exit("push 실패 — 커밋은 로컬에 남아 있습니다. 저장소의 GitHub 권한 연결을 확인하세요.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True)
    ap.add_argument("--summary", required=True)
    ap.add_argument("--body", required=True, help="본문 조각 HTML 파일 경로")
    ap.add_argument("--tags", default="", help="쉼표로 구분")
    ap.add_argument("--date", default=datetime.now(KST).strftime("%Y-%m-%d"))
    ap.add_argument("--slug", default=None)
    ap.add_argument("--no-push", action="store_true")
    a = ap.parse_args()

    tags = [t.strip() for t in a.tags.split(",") if t.strip()]
    slug = a.slug or f"{a.date}-{slugify(a.title)}"
    body = pathlib.Path(a.body).read_text(encoding="utf-8")

    if "<html" in body.lower() or "<body" in body.lower():
        sys.exit("--body 에는 본문 조각만 넣으세요 (<html>/<body> 태그 금지).")
    if re.search(r"<style[\s>]|\sstyle=", body, re.I):
        sys.exit("인라인 style / <style> 태그는 금지입니다. 정의된 CSS 클래스만 쓰세요.")

    tag_html = "".join(f'<span class="tag">{html.escape(t)}</span>' for t in tags)
    page = (ROOT / "tools" / "template.html").read_text(encoding="utf-8")
    for k, v in {
        "{{TITLE}}": html.escape(a.title),
        "{{SUMMARY}}": html.escape(a.summary),
        "{{DATE}}": a.date,
        "{{SLUG}}": slug,
        "{{TAGHTML}}": tag_html,
        "{{BODY}}": body,
    }.items():
        page = page.replace(k, v)

    (ROOT / "posts" / f"{slug}.html").write_text(page, encoding="utf-8")

    meta_path = ROOT / "posts.json"
    data = json.loads(meta_path.read_text(encoding="utf-8"))
    data["posts"] = [p for p in data["posts"] if p["slug"] != slug]
    data["posts"].insert(0, {
        "slug": slug,
        "title": a.title,
        "date": a.date,
        "tags": tags,
        "summary": a.summary,
    })
    meta_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8")

    print(sh(sys.executable, "build.py"))

    if a.no_push:
        print(f"✓ 로컬 생성 완료: posts/{slug}.html (push 생략)")
        return

    sh("git", "add", "-A")
    if not sh("git", "status", "--porcelain"):
        print("변경사항 없음 — commit 생략")
        return
    sh("git", "commit", "-q", "-m", f"post: {a.title}")
    push()
    print(f"✓ 발행 완료 → {SITE}/posts/{slug}.html")
    print("  (GitHub Pages 반영까지 30초~1분)")


if __name__ == "__main__":
    main()
