#!/usr/bin/env python3
"""posts.json을 읽어 index.html(목록 페이지)과 sitemap.xml, rss.xml을 생성한다.

이 블로그는 GitHub Project Pages(서브패스 /devblog/)로 서비스되므로
모든 절대경로에 BASE 접두사가 붙는다.

새 글 발행 절차:
  1) posts/YYYY-MM-DD-slug.html 파일 작성
  2) posts.json의 "posts" 배열 맨 앞에 메타데이터 추가
  3) python3 build.py
  4) git add -A && git commit && git push
"""

import html
import json
import pathlib
from datetime import datetime, timezone, timedelta

ROOT = pathlib.Path(__file__).parent
KST = timezone(timedelta(hours=9))

data = json.loads((ROOT / "posts.json").read_text(encoding="utf-8"))
site = data["site"]
BASE = site.get("base", "/devblog").rstrip("/")
posts = sorted(data["posts"], key=lambda p: (p["date"], p["slug"]), reverse=True)

E = lambda s: html.escape(str(s), quote=True)

# 카테고리 칩 — posts.json 의 site.categories 순서를 따른다
CATEGORIES = site.get("categories", [])

HEAD = """<!DOCTYPE html>
<html lang="ko" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary">
<link rel="alternate" type="application/rss+xml" title="{title}" href="{base}/rss.xml">
<link rel="stylesheet" href="{base}/assets/style.css">
<script>
(function(){{var t=localStorage.getItem('theme');
if(!t)t=matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light';
document.documentElement.setAttribute('data-theme',t);}})();
</script>
</head>
<body>
<header class="site-header"><div class="wrap">
  <a class="brand" href="{base}/"><span class="brand-mark">&lt;/&gt;</span>{brand}</a>
  <nav class="nav">
    <a href="{base}/">홈</a>
    <a href="/">투자노트</a>
    <a href="{base}/rss.xml">RSS</a>
    <button class="theme-btn" id="themeBtn" aria-label="테마 전환">◐</button>
  </nav>
</div></header>
"""

FOOT = """<footer class="site-footer"><div class="wrap">
  <span>© {year} {author}</span>
  <span>코드와 설명은 개인 학습 기록이며, 실제 적용 전 공식 문서를 확인하세요.</span>
</div></footer>
<script>
var btn=document.getElementById('themeBtn');
btn&&btn.addEventListener('click',function(){{
  var r=document.documentElement,n=r.getAttribute('data-theme')==='dark'?'light':'dark';
  r.setAttribute('data-theme',n);localStorage.setItem('theme',n);
}});
</script>
</body>
</html>
"""


def build_index() -> str:
    cards = []
    for p in posts:
        tag_html = "".join(f'<span class="tag">{E(t)}</span>' for t in p.get("tags", []))
        cards.append(
            f'''  <a class="card" href="{BASE}/posts/{E(p["slug"])}.html"
     data-tags="{E("|".join(p.get("tags", [])))}"
     data-search="{E((p["title"] + " " + p.get("summary", "") + " " + " ".join(p.get("tags", []))).lower())}">
    <div class="card-meta">{tag_html}<span>{E(p["date"])}</span></div>
    <h2>{E(p["title"])}</h2>
    <p>{E(p.get("summary", ""))}</p>
  </a>'''
        )

    chips = ['<button class="chip on" data-cat="">전체</button>']
    for c in CATEGORIES:
        chips.append(f'<button class="chip" data-cat="{E(c)}">{E(c)}</button>')

    body = f"""<section class="hero"><div class="wrap">
  <h1>{E(site["title"])}</h1>
  <p>{E(site["tagline"])}</p>
</div></section>

<div class="wrap">
  <div class="chips" id="chips">
{chr(10).join("    " + c for c in chips)}
  </div>
  <div class="toolbar">
    <input class="search" id="q" type="search" placeholder="제목·태그·요약 검색 (예: Kotlin, 코딩테스트, LLM)" autocomplete="off">
    <span class="count" id="count">{len(posts)}편</span>
  </div>
  <div class="posts" id="list">
{chr(10).join(cards)}
  </div>
  <div class="empty" id="empty" style="display:none">검색 결과가 없습니다.</div>
</div>

<script>
(function(){{
  var cards=[].slice.call(document.querySelectorAll('.card')),
      q=document.getElementById('q'),
      empty=document.getElementById('empty'),
      count=document.getElementById('count'),
      chips=[].slice.call(document.querySelectorAll('.chip')),
      total=cards.length, cat='';
  function apply(){{
    var kw=(q.value||'').trim().toLowerCase(),
        terms=kw?kw.split(/\\s+/):[],
        shown=0;
    cards.forEach(function(c){{
      var hay=c.dataset.search||'',
          tags=(c.dataset.tags||'').split('|'),
          okCat=!cat||tags.indexOf(cat)>-1,
          okKw=terms.every(function(t){{return hay.indexOf(t)>-1}});
      var ok=okCat&&okKw;
      c.style.display=ok?'':'none'; if(ok)shown++;
    }});
    empty.style.display=shown?'none':'';
    count.textContent=(terms.length||cat)?shown+' / '+total+'편':total+'편';
  }}
  chips.forEach(function(b){{
    b.addEventListener('click',function(){{
      chips.forEach(function(x){{x.classList.remove('on')}});
      b.classList.add('on'); cat=b.dataset.cat||''; apply();
    }});
  }});
  q.addEventListener('input',apply);
}})();
</script>
"""

    return (
        HEAD.format(
            title=E(site["title"]),
            desc=E(site["tagline"]),
            url=E(site["url"]),
            brand=E(site["title"]),
            base=BASE,
        )
        + body
        + FOOT.format(year=datetime.now(KST).year, author=E(site["author"]))
    )


def build_sitemap() -> str:
    urls = [f"  <url><loc>{site['url']}/</loc></url>"]
    for p in posts:
        urls.append(
            f"  <url><loc>{site['url']}/posts/{p['slug']}.html</loc>"
            f"<lastmod>{p['date']}</lastmod></url>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )


def build_rss() -> str:
    items = []
    for p in posts[:30]:
        pub = datetime.strptime(p["date"], "%Y-%m-%d").replace(tzinfo=KST)
        items.append(
            f"""    <item>
      <title>{E(p['title'])}</title>
      <link>{site['url']}/posts/{p['slug']}.html</link>
      <guid isPermaLink="true">{site['url']}/posts/{p['slug']}.html</guid>
      <description>{E(p.get('summary',''))}</description>
      <pubDate>{pub.strftime('%a, %d %b %Y %H:%M:%S %z')}</pubDate>
    </item>"""
        )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>{E(site['title'])}</title>
  <link>{site['url']}</link>
  <description>{E(site['tagline'])}</description>
  <language>ko</language>
{chr(10).join(items)}
</channel></rss>
"""


if __name__ == "__main__":
    (ROOT / "index.html").write_text(build_index(), encoding="utf-8")
    (ROOT / "sitemap.xml").write_text(build_sitemap(), encoding="utf-8")
    (ROOT / "rss.xml").write_text(build_rss(), encoding="utf-8")
    print(f"✓ index.html / sitemap.xml / rss.xml 생성 완료 — 글 {len(posts)}편")
