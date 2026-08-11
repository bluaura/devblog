# 블루오라 개발노트

앱 개발·AI 도구·알고리즘 학습 기록. → https://bluaura.github.io/devblog/

## 구조

| 파일 | 역할 |
|---|---|
| `publish.py` | 글 1편 발행 (템플릿 적용 → 목록 갱신 → commit → push) |
| `build.py` | `posts.json` → `index.html` / `sitemap.xml` / `rss.xml` 생성 |
| `tools/template.html` | 글 페이지 템플릿 (highlight.js·복사버튼·다크모드 포함) |
| `assets/style.css` | 전체 스타일 (라이트/다크 자동, 코드블록 토큰 색 포함) |
| `posts.json` | 사이트 메타 + 글 목록 |

## 발행

```bash
export GITHUB_TOKEN=github_pat_...
python3 publish.py \
  --title "제목" \
  --tags "Android,Kotlin,튜토리얼" \
  --summary "한 줄 요약" \
  --slug "2026-08-11-my-slug" \
  --body body.html
```

`--body` 에는 본문 조각만 넣는다 (`<html>`/`<body>`/인라인 `style=` 금지).

## 코드블록 작성

```html
<div class="code">
  <div class="code-head"><span class="fname">MainActivity.kt</span><button class="copy-btn">복사</button></div>
  <pre><code class="language-kotlin">fun main() { println("hi") }</code></pre>
</div>
```

`<` `>` `&` 는 각각 `&lt;` `&gt;` `&amp;` 로 이스케이프한다.
