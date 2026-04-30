"""
fix_faq_schema.py
-----------------
Batch-fix 64 Japan Encyclopedia articles that have FAQ content
but are missing <details>/<summary> structure and FAQPage JSON-LD.

Supported FAQ formats detected in the corpus:
  A  <p>Q1：question</p> <p>A1：answer</p>  (separate p tags)
  B  "Q1：...n A1：..."  (literal 'n' as newline separator)
  C  <p>1. question?</p> <p>answer</p>  (numbered list)
  D  <p>**question?**</p> <p>answer</p>  (bold markdown)
  E  <h3>Q1：question</h3> <p>**A**：answer</p>  (h3 headings)
  F  「question？」——answer  (bracket-dash inline text)
  G  HTML-entity encoded  &lt;b&gt;Q1:...&lt;br&gt;
  H  1. question？答：answer  (same paragraph)
  I  Q1：...A1：... inline (no line breaks)
  J  \\n\\nQ1：...\\nA1：  (JSON-escaped newlines)
  K  **FAQ 區塊** + <p>question</p><p>answer</p>
  L  &lt;br&gt;&lt;br&gt;Q1：  (entity-encoded br)
"""

import os
import re
import json
import glob
import html
from pathlib import Path

ARTICLES_DIR = Path("/Users/ki/Documents/japan-encyclopedia/articles")


# ---------------------------------------------------------------------------
# Helper: clean text
# ---------------------------------------------------------------------------

def clean_text(s: str) -> str:
    """Strip surrounding whitespace, common markdown, and trailing punctuation."""
    s = s.strip()
    # Remove **bold** markers
    s = re.sub(r'\*\*', '', s)
    # Remove leading "A：" / "A1：" / "**A**：" answer prefixes
    s = re.sub(r'^[Aa]\d*[：:]\s*', '', s)
    # Decode HTML entities that survived into text
    s = html.unescape(s)
    return s.strip()


def truncate(s: str, max_len: int = 500) -> str:
    return s[:max_len] if len(s) > max_len else s


# ---------------------------------------------------------------------------
# Format extractors  (each returns list of (question, answer) tuples or [])
# ---------------------------------------------------------------------------

def extract_format_a(content: str):
    """<p>Q1：question</p> followed by <p>A1：answer</p>"""
    pairs = []
    matches = re.finditer(
        r'<p>\s*Q\d+[：:]\s*([^<]{10,300})</p>\s*<p>\s*(?:A\d+[：:]\s*)?([^<]{20,500})</p>',
        content
    )
    for m in matches:
        q = clean_text(m.group(1))
        a = clean_text(m.group(2))
        if q.endswith('？') or q.endswith('?'):
            pairs.append((q, a))
    return pairs


def extract_format_b(content: str):
    """Literal 'n' as newline: 'Q1：...n A1：...'"""
    # Un-escape the 'n' separators to real newlines first
    unescaped = re.sub(r'(?<!\w)n\s+(?=[QA]\d+[：:])', '\n', content)
    pairs = []
    matches = re.finditer(
        r'Q\d+[：:]\s*([^\n]{10,300})\nA\d+[：:]\s*([^\n]{20,500})',
        unescaped
    )
    for m in matches:
        q = clean_text(m.group(1))
        a = clean_text(m.group(2))
        if q.endswith('？') or q.endswith('?'):
            pairs.append((q, a))
    return pairs


def extract_format_c(content: str):
    """<p>1. question?</p> <p>[答：]answer</p>"""
    pairs = []
    matches = re.finditer(
        r'<p>\s*\d+[\.\、]\s*([^<]{5,200}[？?])[^<]*</p>\s*<p>\s*(?:答[：:]\s*)?([^<]{20,500})</p>',
        content
    )
    for m in matches:
        q = clean_text(m.group(1))
        a = clean_text(m.group(2))
        pairs.append((q, a))
    return pairs


def extract_format_d(content: str):
    """<p>**question?**</p> <p>answer</p>"""
    pairs = []
    matches = re.finditer(
        r'<p>[^<]*\*\*([^*]{5,200}[？?])\*\*[^<]*</p>\s*<p>\s*([^<]{20,500})</p>',
        content
    )
    for m in matches:
        q = clean_text(m.group(1))
        a = clean_text(m.group(2))
        # Skip if answer looks like another question
        if not a.endswith('？'):
            pairs.append((q, a))
    return pairs


def extract_format_e(content: str):
    """<h3>Q1：question</h3> <p>**A**：answer</p>"""
    pairs = []
    matches = re.finditer(
        r'<h3>\s*Q\d+[：:]\s*([^<]{10,300})</h3>\s*<p>\s*(?:\*\*A(?:\d+)?\*\*[：:]\s*|A\d*[：:]\s*)?([^<]{20,500})</p>',
        content
    )
    for m in matches:
        q = clean_text(m.group(1))
        a = clean_text(m.group(2))
        pairs.append((q, a))
    return pairs


def extract_format_f(content: str):
    """「question？」——answer  (inline bracket-dash, but in actual html)"""
    pairs = []
    matches = re.finditer(
        r'「([^」]{5,150}？)」[——\-–—]{1,3}([^「\n<]{20,300})',
        content
    )
    for m in matches:
        q = clean_text(m.group(1))
        a = clean_text(m.group(2))
        # Skip if it's inside a meta/description tag
        start = m.start()
        preceding = content[max(0, start-50):start]
        if 'content="' in preceding or '"description"' in preceding:
            continue
        pairs.append((q, a))
    return pairs


def extract_format_g(content: str):
    """HTML-entity encoded FAQ: &lt;b&gt;Q1:...&lt;br&gt;"""
    # Decode entities and extract
    decoded = html.unescape(content)
    pairs = []
    # Match <b>Q1: question</b><br>A1: answer
    matches = re.finditer(
        r'<b>Q\d+[：:]\s*([^<]{10,300})</b><br>\s*A\d+[：:]\s*([^<\n]{20,500})',
        decoded
    )
    for m in matches:
        q = clean_text(m.group(1))
        a = clean_text(m.group(2))
        pairs.append((q, a))
    return pairs


def extract_format_h(content: str):
    """Inline in same <p>: '1. question？答：answer'"""
    pairs = []
    matches = re.finditer(
        r'<p>\s*\d+[\.\、]\s*([^<]{5,200}[？?])答[：:]\s*([^<]{20,500})</p>',
        content
    )
    for m in matches:
        q = clean_text(m.group(1))
        a = clean_text(m.group(2))
        pairs.append((q, a))
    return pairs


def extract_format_i(content: str):
    """Inline Q1:...A1:...Q2:... without newlines in HTML paragraph"""
    pairs = []
    # Only look in paragraphs that contain Q/A patterns
    para_matches = re.finditer(r'<p>([^<]{50,}Q\d+[：:][^<]{30,}A\d+[：:][^<]{30,})</p>', content)
    for pm in para_matches:
        text = pm.group(1)
        # Extract all Q/A pairs from this paragraph
        sub_matches = re.finditer(
            r'Q\d+[：:]\s*([^QA]{10,200}[？?])[^QA]*?A\d+[：:]\s*([^QA]{20,300})(?=Q\d+[：:]|$)',
            text
        )
        for m in sub_matches:
            q = clean_text(m.group(1))
            a = clean_text(m.group(2))
            pairs.append((q, a))
    return pairs


def extract_format_j(content: str):
    """JSON-escaped: \\n\\nQ1：...\\nA1："""
    # Unescape \\n to actual newline
    unescaped = content.replace('\\n', '\n')
    pairs = []
    matches = re.finditer(
        r'Q\d+[：:]\s*([^\n]{10,300})\nA\d+[：:]\s*([^\n]{20,500})',
        unescaped
    )
    for m in matches:
        q = clean_text(m.group(1))
        a = clean_text(m.group(2))
        pairs.append((q, a))
    return pairs


def extract_format_k(content: str):
    """**FAQ 區塊** or similar header, then <p>question</p><p>answer</p>"""
    pairs = []
    # Find FAQ block marker
    block_m = re.search(r'\*\*FAQ[^*]*\*\*.*?(?=<p>)', content, re.DOTALL)
    if not block_m:
        return pairs
    # Extract from marker to end of article
    block = content[block_m.end():]
    # Find pairs: <p>question?</p><p>answer</p>
    matches = re.finditer(
        r'<p>\s*([^<]{5,150}[？?])\s*</p>\s*<p>\s*([^<]{20,400})</p>',
        block
    )
    for m in matches:
        q = clean_text(m.group(1))
        a = clean_text(m.group(2))
        # Stop if answer looks like a structural section
        if '<' in a or a.startswith('©'):
            break
        pairs.append((q, a))
    return pairs


def extract_format_l(content: str):
    """Entity-encoded br: &lt;br&gt;&lt;br&gt;Q1：...&lt;br&gt;&lt;br&gt;A1：
    Also handles Q1：question<br><br>answer (no A1: prefix, answer before next Q)
    """
    decoded = html.unescape(content)
    pairs = []

    # Pattern 1: Q1：question <br> A1：answer
    matches = re.finditer(
        r'Q\d+[：:]\s*([^\n]{10,300}?)<br>\s*(?:<br>\s*)?A\d+[：:]\s*([^\n]{20,500}?)(?=<br>|Q\d+[：:]|</p>|$)',
        decoded
    )
    for m in matches:
        q = clean_text(re.sub(r'<[^>]+>', '', m.group(1)))
        a = clean_text(re.sub(r'<[^>]+>', '', m.group(2)))
        if q and a:
            pairs.append((q, a))

    # Pattern 2: Q1：question <br><br> answer (no A: prefix)
    if not pairs:
        matches2 = re.finditer(
            r'Q\d+[：:]\s*([^\n<]{10,300})<br>(?:<br>)?\s*(.*?)(?=<br>\s*Q\d+[：:]|</p>|$)',
            decoded, re.DOTALL
        )
        for m in matches2:
            q = clean_text(m.group(1))
            a = clean_text(re.sub(r'<[^>]+>', '', m.group(2)))
            if q and a and len(a) >= 20:
                pairs.append((q, a))

    return pairs


def extract_format_m(content: str):
    """<h3>【Q1】</h3> <p>question</p> <p>A1：answer</p>"""
    pairs = []
    matches = re.finditer(
        r'<h3>\s*【Q\d+】\s*</h3>\s*<p>\s*([^<]{5,200})</p>\s*<p>\s*A\d+[：:]\s*([^<]{20,500})</p>',
        content
    )
    for m in matches:
        q = clean_text(m.group(1))
        a = clean_text(m.group(2))
        pairs.append((q, a))
    return pairs


def extract_format_n(content: str):
    """HTML entity encoded <strong>Q1：question</strong><br>answer"""
    decoded = html.unescape(content)
    pairs = []
    matches = re.finditer(
        r'<strong>\s*Q\d+[：:]\s*([^<]{5,200})</strong><br>\s*([^<\n]{20,500})',
        decoded
    )
    for m in matches:
        q = clean_text(m.group(1))
        a = clean_text(m.group(2))
        pairs.append((q, a))
    return pairs


def extract_format_o(content: str):
    """Prose 「question」——answer inside <p> tags (each pair in a separate <p>)"""
    pairs = []
    # Find <p> tags that contain 「...」——... pattern
    p_matches = re.finditer(r'<p>\s*(「[^」]{5,100}」[——\-–—]{1,3}[^<]{20,400})\s*</p>', content)
    for pm in p_matches:
        text = pm.group(1)
        # Extract multiple pairs from this <p>
        for m in re.finditer(r'「([^」]{5,100})」[——\-–—]{1,3}([^「]{20,300}?)(?=「|$)', text):
            q = clean_text(m.group(1))
            a = clean_text(m.group(2))
            if q.endswith('？') or q.endswith('?') or True:  # Accept even without ?
                pairs.append((q, a))
    return pairs


def extract_prose_faq(content: str):
    """
    Prose FAQ inside a 'FAQ：' or '【FAQ】' labelled paragraph.
    Looks for 'Q1：question A1：answer' style in continuous prose.
    Also handles '「question」——answer' style when clearly in an FAQ context.
    """
    pairs = []

    # Find text containing FAQ label
    faq_section_m = re.search(
        r'(?:【FAQ】|FAQ[：:区塊]|常見問題[^<]{0,50})\s*</[^>]+>\s*(.*?)(?=</div>|<section|<footer)',
        content, re.DOTALL
    )
    if not faq_section_m:
        return pairs

    section = faq_section_m.group(1)

    # Try 「question？」——answer pattern inside FAQ section
    for m in re.finditer(r'「([^」]{5,150}[？?])」[——\-–—]{1,3}([^「\n<]{20,300})', section):
        q = clean_text(m.group(1))
        a = clean_text(m.group(2))
        pairs.append((q, a))

    # Try Q1：question A1：answer  (inline continuous text)
    for m in re.finditer(
        r'Q\d+[：:]\s*([^QA]{10,200}[？?])[^QA]*?A\d+[：:]\s*([^QA]{20,300})(?=Q\d+[：:]|$)',
        section
    ):
        q = clean_text(m.group(1))
        a = clean_text(m.group(2))
        if (q, a) not in pairs:
            pairs.append((q, a))

    return pairs


# ---------------------------------------------------------------------------
# Master extractor
# ---------------------------------------------------------------------------

EXTRACTORS = [
    extract_format_m,   # <h3>【Q1】</h3> format (nagoya)
    extract_format_n,   # <strong>Q1：</strong><br> (entity encoded)
    extract_format_a,
    extract_format_e,   # h3 before b because both use Q1：
    extract_format_b,
    extract_format_g,
    extract_format_l,
    extract_format_j,
    extract_format_c,
    extract_format_h,
    extract_format_d,
    extract_format_k,
    extract_format_o,   # prose <p>「...」——... </p>
    extract_format_i,
    extract_format_f,
    extract_prose_faq,
]


def extract_faq_pairs(content: str):
    """Try all extractors, return the best (most pairs) result, max 8 pairs."""
    best = []
    for extractor in EXTRACTORS:
        try:
            pairs = extractor(content)
        except Exception:
            continue
        # De-duplicate by question text
        seen = set()
        unique = []
        for q, a in pairs:
            if q not in seen and len(q) > 5:
                seen.add(q)
                unique.append((q, a))
        if len(unique) > len(best):
            best = unique
        if len(best) >= 5:
            break  # Good enough
    return best[:8]


# ---------------------------------------------------------------------------
# HTML builders
# ---------------------------------------------------------------------------

def build_details_html(pairs):
    parts = []
    for q, a in pairs:
        a_clean = a.rstrip('。').strip()
        parts.append(
            f'<details><summary>{q}</summary><p>{a_clean}</p></details>'
        )
    return '\n'.join(parts)


def build_faqpage_schema(pairs):
    entities = []
    for q, a in pairs:
        entities.append({
            "@type": "Question",
            "name": q,
            "acceptedAnswer": {
                "@type": "Answer",
                "text": truncate(a)
            }
        })
    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": entities
    }
    return json.dumps(schema, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Article fixer
# ---------------------------------------------------------------------------

def fix_article(html_path: Path):
    content = html_path.read_text(encoding='utf-8', errors='replace')

    # Guard: already fixed
    if '<details>' in content:
        return False, "already has <details>"

    # Guard: already has FAQPage
    if 'FAQPage' in content:
        return False, "already has FAQPage schema"

    # Must have FAQ content
    has_faq_marker = any(kw in content for kw in [
        'AI搜尋最佳化', '常見問題', '【FAQ】', 'FAQ：', 'FAQ区塊',
        'Q1：', 'Q1:', 'Q2：', 'Q2:'
    ])
    if not has_faq_marker:
        return False, "no FAQ marker found"

    pairs = extract_faq_pairs(content)
    if len(pairs) < 2:
        return False, f"only {len(pairs)} Q&A pair(s) found"

    # Build schema tag
    faq_schema = build_faqpage_schema(pairs)
    schema_tag = f'<script type="application/ld+json">\n{faq_schema}\n</script>'

    # Inject schema into <head>
    if '</head>' not in content:
        return False, "no </head> tag"
    content = content.replace('</head>', f'{schema_tag}\n</head>', 1)

    # Build details section
    details_html = build_details_html(pairs)
    faq_section = (
        '<section class="faq-section">\n'
        '<h2>常見問題</h2>\n'
        f'{details_html}\n'
        '</section>'
    )

    # Insert before </article> or </main>
    if '</article>' in content:
        content = content.replace('</article>', f'{faq_section}\n</article>', 1)
    elif '</main>' in content:
        content = content.replace('</main>', f'{faq_section}\n</main>', 1)
    else:
        # Append before </body> as last resort
        if '</body>' in content:
            content = content.replace('</body>', f'{faq_section}\n</body>', 1)
        else:
            return False, "no insertion point found"

    html_path.write_text(content, encoding='utf-8')
    return True, f"fixed with {len(pairs)} Q&A pairs"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    all_htmls = list(ARTICLES_DIR.glob("*.html"))
    total = len(all_htmls)

    # Find candidates: has FAQ marker, no <details>
    candidates = []
    for f in all_htmls:
        try:
            c = f.read_text(encoding='utf-8', errors='replace')
        except Exception:
            continue
        if '<details>' in c:
            continue
        if 'FAQPage' in c:
            continue
        if any(kw in c for kw in [
            'AI搜尋最佳化', '常見問題', '【FAQ】', 'FAQ：', 'FAQ区塊',
            'Q1：', 'Q1:', 'Q2：', 'Q2:'
        ]):
            candidates.append(f)

    print(f"Total HTML files    : {total}")
    print(f"Candidates to fix   : {len(candidates)}")
    print()

    # Count existing FAQPage before
    existing_faq = sum(
        1 for f in all_htmls
        if 'FAQPage' in f.read_text(encoding='utf-8', errors='replace')
    )
    print(f"FAQPage before fix  : {existing_faq}/{total} ({existing_faq/total*100:.1f}%)")
    print()

    fixed = 0
    skipped = 0
    skip_reasons = {}

    for f in sorted(candidates):
        success, msg = fix_article(f)
        if success:
            fixed += 1
            if fixed <= 10:
                print(f"OK  {f.name[:70]} — {msg}")
        else:
            skipped += 1
            skip_reasons[msg] = skip_reasons.get(msg, 0) + 1

    print()
    if skipped:
        print("Skip reasons:")
        for reason, count in sorted(skip_reasons.items(), key=lambda x: -x[1]):
            print(f"  {count:3d}x  {reason}")
        print()

    # Count after
    after_faq = sum(
        1 for f in all_htmls
        if 'FAQPage' in f.read_text(encoding='utf-8', errors='replace')
    )

    print(f"Fixed               : {fixed} articles")
    print(f"Skipped             : {skipped} articles")
    print(f"FAQPage after fix   : {after_faq}/{total} ({after_faq/total*100:.1f}%)")
    print(f"Coverage change     : +{after_faq - existing_faq} articles")


if __name__ == "__main__":
    main()
