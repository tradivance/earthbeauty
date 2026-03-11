"""
SEO記事 品質チェックスクリプト（汎用）

Markdown記事ファイルを検証し、品質基準をチェックする。
不合格項目を一覧で報告する。

Usage:
    python tools/note-api/quality_check.py <markdown_file>
    python tools/note-api/quality_check.py <markdown_file> --min-chars 2000 --max-chars 3000
"""

import re
import sys
import os
import io

# Windows cp932 対策: stdout を UTF-8 に強制
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


# 絵文字パターン
EMOJI_PATTERN = re.compile(
    r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF'
    r'\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U0001F900-\U0001F9FF'
    r'\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002600-\U000026FF]'
)


def count_pure_text(text):
    """純テキスト文字数をカウント（Markdown記法・空白を除外）"""
    clean = re.sub(r'[#*|>`\-\n\r\t ]', '', text)
    # リンクURL部分を除去
    clean = re.sub(r'https?://[^\s)]+', '', clean)
    # 残った記号を除去
    clean = re.sub(r'[\[\]()]', '', clean)
    return len(clean)


def split_sections(text):
    """## 見出しでセクションに分割"""
    sections = []
    current_title = None
    current_lines = []

    for line in text.split('\n'):
        if line.strip().startswith('## ') and not line.strip().startswith('### '):
            if current_title is not None:
                sections.append((current_title, '\n'.join(current_lines)))
            current_title = line.strip()[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_title is not None:
        sections.append((current_title, '\n'.join(current_lines)))

    return sections


def get_paragraphs(section_body):
    """セクション本文から段落を抽出（空行区切り）"""
    paragraphs = []
    current = []

    for line in section_body.split('\n'):
        stripped = line.strip()
        if not stripped:
            if current:
                text = ' '.join(current)
                if not text.startswith('###') and not text.startswith('- ') and text != '---' and not text.startswith('>'):
                    paragraphs.append(text)
                current = []
        else:
            if stripped.startswith('- ') or stripped.startswith('### ') or stripped == '---' or stripped.startswith('> '):
                if current:
                    text = ' '.join(current)
                    paragraphs.append(text)
                    current = []
            else:
                current.append(stripped)

    if current:
        text = ' '.join(current)
        paragraphs.append(text)

    return paragraphs


def count_sentences(paragraph):
    """段落内の文数をカウント（。で区切り）"""
    clean = re.sub(r'\*\*', '', paragraph)
    clean = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean)
    count = clean.count('。')
    return max(count, 0)


def check_quality(md_text, min_chars=2000, max_chars=3000):
    """品質チェックを実行し、結果を返す

    Args:
        md_text: Markdownテキスト
        min_chars: 最小文字数（デフォルト: 2000）
        max_chars: 最大文字数（デフォルト: 3000）

    Returns:
        list of dict: [{item: int, name: str, passed: bool, detail: str}, ...]
    """
    results = []
    sections = split_sections(md_text)

    # 1. 合計文字数
    char_count = count_pure_text(md_text)
    results.append({
        'item': 1,
        'name': f'合計文字数（{min_chars:,}〜{max_chars:,}字）',
        'passed': min_chars <= char_count <= max_chars,
        'detail': f'{char_count:,}文字'
    })

    # 2. ## 見出し数（最低3個）
    h2_count = len(re.findall(r'^## ', md_text, re.MULTILINE))
    results.append({
        'item': 2,
        'name': '## 見出し数（3個以上）',
        'passed': h2_count >= 3,
        'detail': f'{h2_count}個'
    })

    # 3. 記事構造（# タイトル行 + リード文の存在）
    lines_list = md_text.strip().split('\n')
    has_title = bool(lines_list) and lines_list[0].startswith('# ') and not lines_list[0].startswith('## ')
    lead_text = ''
    for ln in lines_list[1:]:
        if ln.strip().startswith('## '):
            break
        lead_text += ln
    has_lead = len(lead_text.strip()) > 0
    structure_detail = []
    if not has_title:
        structure_detail.append('# タイトル行なし')
    if not has_lead:
        structure_detail.append('リード文なし（# タイトルと最初の ## の間にテキストが必要）')
    results.append({
        'item': 3,
        'name': '記事構造（# タイトル + リード文）',
        'passed': has_title and has_lead,
        'detail': ', '.join(structure_detail) if structure_detail else 'OK'
    })

    # 4. 絵文字なし
    emojis = EMOJI_PATTERN.findall(md_text)
    results.append({
        'item': 4,
        'name': '絵文字なし',
        'passed': len(emojis) == 0,
        'detail': f'{len(emojis)}個検出' if emojis else 'OK'
    })

    # 5. note非対応記法なし
    has_table = bool(re.search(r'^\|.*\|.*\|', md_text, re.MULTILINE))
    results.append({
        'item': 5,
        'name': 'note非対応記法なし',
        'passed': not has_table,
        'detail': 'テーブル記法検出' if has_table else 'OK'
    })

    # 6. です・ます調
    casual_endings = []
    for line in md_text.split('\n'):
        stripped = line.strip()
        if not stripped or stripped.startswith('#') or stripped.startswith('-') or stripped.startswith('>') or stripped == '---':
            continue
        sentences = re.findall(r'[^。]+。', stripped)
        for s in sentences:
            s_clean = re.sub(r'\*\*', '', s).strip()
            if s_clean.endswith('た。') or s_clean.endswith('だ。'):
                if not s_clean.endswith('でした。') and not s_clean.endswith('ました。') and not s_clean.endswith('くれた。'):
                    casual_endings.append(s_clean[-10:])
    results.append({
        'item': 6,
        'name': 'です・ます調統一',
        'passed': len(casual_endings) == 0,
        'detail': f'常体文末{len(casual_endings)}件: {casual_endings[:3]}' if casual_endings else 'OK'
    })

    # 7. 太字チェック（フレーズ太字の検出）
    bold_matches = re.findall(r'\*\*(.+?)\*\*', md_text)
    phrase_bold = []
    for b in bold_matches:
        if ':' in b and len(b) < 20:
            continue
        if not b.strip().endswith('。') and not b.strip().endswith('：') and len(b) > 5:
            phrase_bold.append(b[:30])
    results.append({
        'item': 7,
        'name': '太字が1文単位',
        'passed': len(phrase_bold) == 0,
        'detail': f'フレーズ太字{len(phrase_bold)}件' if phrase_bold else 'OK'
    })

    # 8. 段落1〜3文チェック（最重要）
    long_paragraphs = []
    for title, body in sections:
        paragraphs = get_paragraphs(body)
        for p in paragraphs:
            sentence_count = count_sentences(p)
            if sentence_count >= 4:
                long_paragraphs.append({
                    'section': title[:20],
                    'sentences': sentence_count,
                    'preview': p[:50]
                })
    results.append({
        'item': 8,
        'name': '段落1〜3文（4文以上の段落が0件）',
        'passed': len(long_paragraphs) == 0,
        'detail': f'{len(long_paragraphs)}件違反' if long_paragraphs else 'OK'
    })

    # 9. 免責・注記の存在
    has_disclaimer = bool(re.search(r'> .*時点の情報', md_text))
    results.append({
        'item': 9,
        'name': '免責・注記あり',
        'passed': has_disclaimer,
        'detail': 'あり' if has_disclaimer else 'なし（記事末尾に「> 20XX年X月時点の情報〜」を追加）'
    })

    return results, long_paragraphs


def main():
    if len(sys.argv) < 2:
        print('Usage: python quality_check.py <markdown_file> [--min-chars N --max-chars N]')
        sys.exit(1)

    md_file = sys.argv[1]
    min_chars = 2000
    max_chars = 3000

    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '--min-chars' and i + 1 < len(sys.argv):
            min_chars = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '--max-chars' and i + 1 < len(sys.argv):
            max_chars = int(sys.argv[i + 1])
            i += 2
        else:
            i += 1

    with open(md_file, encoding='utf-8') as f:
        md_text = f.read()

    results, long_paragraphs = check_quality(md_text, min_chars, max_chars)

    # 結果表示
    passed = sum(1 for r in results if r['passed'])
    total = len(results)
    all_passed = passed == total

    print(f'\n{"=" * 50}')
    print(f'  品質チェック結果: {passed}/{total} 合格')
    print(f'{"=" * 50}')

    for r in results:
        mark = 'PASS' if r['passed'] else 'FAIL'
        print(f'  [{mark}] {r["item"]:2d}. {r["name"]} — {r["detail"]}')

    if long_paragraphs:
        print(f'\n--- 段落違反の詳細 ---')
        for lp in long_paragraphs:
            print(f'  [{lp["section"]}] {lp["sentences"]}文: {lp["preview"]}...')

    print()
    if all_passed:
        print('RESULT: ALL PASSED')
    else:
        failed = [r for r in results if not r['passed']]
        print(f'RESULT: {len(failed)} FAILED')
        for f in failed:
            print(f'  - Item {f["item"]}: {f["name"]}')

    sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()
