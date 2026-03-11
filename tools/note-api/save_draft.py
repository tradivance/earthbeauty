"""
note.com 下書き保存スクリプト（汎用）

Markdown記事をnote.comの下書きとして保存する。
- ログイン → 記事作成 → 本文保存（draft_save）の3ステップ
- 設定は tools/note-api/config.json から読み込み

Usage:
    python tools/note-api/save_draft.py <markdown_file> [--hashtags "tag1,tag2,..."]
    python tools/note-api/save_draft.py <markdown_file> --title "カスタムタイトル"
"""

import urllib.request
import http.cookiejar
import json
import re
import sys
import os


def load_config():
    """config.json から認証情報を読み込む"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    if not os.path.exists(config_path):
        print('ERROR: config.json が見つかりません。')
        print('  cp tools/note-api/config.example.json tools/note-api/config.json')
        print('  してからメールアドレス・パスワードを設定してください。')
        sys.exit(1)
    with open(config_path, encoding='utf-8') as f:
        return json.load(f)


def login(opener, email, password):
    """note.com にログインしてセッションCookieを取得"""
    data = json.dumps({'login': email, 'password': password}).encode('utf-8')
    req = urllib.request.Request(
        'https://note.com/api/v1/sessions/sign_in',
        data=data,
        method='POST'
    )
    req.add_header('Content-Type', 'application/json')
    req.add_header('User-Agent', 'Mozilla/5.0')
    resp = opener.open(req, timeout=30)
    if resp.status != 201:
        raise Exception(f'Login failed: {resp.status}')
    return json.loads(resp.read().decode('utf-8'))


def create_note(opener):
    """空の下書きノートを作成し、IDを返す"""
    data = json.dumps({
        'note_type': 'TextNote',
        'status': 'draft'
    }).encode('utf-8')
    req = urllib.request.Request(
        'https://note.com/api/v1/text_notes',
        data=data,
        method='POST'
    )
    req.add_header('Content-Type', 'application/json')
    req.add_header('User-Agent', 'Mozilla/5.0')
    resp = opener.open(req, timeout=30)
    result = json.loads(resp.read().decode('utf-8'))
    note_id = result['data']['id']
    note_key = result['data']['key']
    return note_id, note_key


def save_draft(opener, note_id, title, body_html, hashtags=None):
    """下書きの本文とタイトルを保存"""
    payload = {
        'name': title,
        'body': body_html
    }
    if hashtags:
        payload['hashtag_notes'] = [{'hashtag': {'name': tag}} for tag in hashtags]

    data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(
        f'https://note.com/api/v1/text_notes/draft_save?id={note_id}',
        data=data,
        method='POST'
    )
    req.add_header('Content-Type', 'application/json')
    req.add_header('User-Agent', 'Mozilla/5.0')
    resp = opener.open(req, timeout=30)
    result = json.loads(resp.read().decode('utf-8'))
    return result.get('data', {}).get('result', False)


def md_to_note_html(markdown_text):
    """Markdown を note.com 用 HTML に変換する

    Returns:
        (title, body_html) のタプル
        title: 最初の # 見出しから抽出
        body_html: 残りをHTMLに変換
    """
    lines = markdown_text.strip().split('\n')

    title = ''
    body_lines = lines

    # 最初の見出し行をタイトルとして抽出（# と ## の両方に対応）
    if lines and lines[0].startswith('# '):
        if lines[0].startswith('## '):
            title = lines[0][3:].strip()
        else:
            title = lines[0][2:].strip()
        body_lines = lines[1:]

    html_parts = []
    i = 0
    in_list = False
    in_code_block = False
    code_lines = []

    while i < len(body_lines):
        line = body_lines[i]
        stripped = line.strip()

        # コードブロック開始/終了
        if stripped.startswith('```'):
            if in_code_block:
                code_content = '\n'.join(code_lines)
                import html as html_mod
                code_content = html_mod.escape(code_content)
                html_parts.append(f'<pre><code>{code_content}</code></pre>')
                code_lines = []
                in_code_block = False
                i += 1
                continue
            else:
                if in_list:
                    html_parts.append('</ul>')
                    in_list = False
                in_code_block = True
                i += 1
                continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # 空行
        if not stripped:
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            i += 1
            continue

        # 水平線 ---
        if stripped == '---':
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            i += 1
            continue

        # h2 見出し
        if stripped.startswith('## ') and not stripped.startswith('### '):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            heading = inline_format(stripped[3:].strip())
            html_parts.append(f'<h2 style="text-align:center">{heading}</h2>')
            i += 1
            continue

        # h3 見出し
        if stripped.startswith('### '):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            heading = inline_format(stripped[4:].strip())
            html_parts.append(f'<h3 style="text-align:center">{heading}</h3>')
            i += 1
            continue

        # 引用ブロック（> で始まる行の連続）
        if stripped.startswith('> '):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            quote_lines = []
            while i < len(body_lines):
                s = body_lines[i].strip()
                if not s:
                    i += 1
                    continue
                if s.startswith('> '):
                    quote_lines.append(inline_format(s[2:].strip()))
                    i += 1
                else:
                    break
            if quote_lines:
                inner = ''.join(f'<p>{line}</p>' for line in quote_lines)
                html_parts.append(f'<blockquote>{inner}</blockquote>')
            continue

        # リスト項目
        if stripped.startswith('- '):
            if not in_list:
                html_parts.append('<ul>')
                in_list = True
            item = inline_format(stripped[2:].strip())
            html_parts.append(f'<li>{item}</li>')
            i += 1
            continue

        # 通常テキスト（段落）
        if in_list:
            html_parts.append('</ul>')
            in_list = False
        para = inline_format(stripped)
        html_parts.append(f'<p>{para}</p>')
        i += 1

    if in_list:
        html_parts.append('</ul>')

    body_html = '\n'.join(html_parts)
    return title, body_html


def inline_format(text):
    """インラインのMarkdown記法をHTMLに変換"""
    # **bold** → <b>bold</b>
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # [text](url) → <a href="url">text</a>
    def link_replace(m):
        label = m.group(1)
        url = m.group(2)
        if url.startswith('//'):
            url = 'https:' + url
        return f'<a href="{url}">{label}</a>'
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', link_replace, text)
    # Raw HTML の href="//..." / src="//..." も https: に変換
    text = re.sub(r'href="(//.+?)"', lambda m: f'href="https:{m.group(1)}"', text)
    text = re.sub(r'src="(//.+?)"', lambda m: f'src="https:{m.group(1)}"', text)
    return text


def extract_hashtags(md_text):
    """Markdownテキスト末尾の tags: 行からハッシュタグを抽出して除去する

    Returns:
        (本文テキスト, タグリスト) のタプル。tags行がなければタグリストはNone
    """
    lines = md_text.rstrip().split('\n')
    for i in range(len(lines) - 1, max(len(lines) - 5, -1), -1):
        stripped = lines[i].strip()
        if stripped.lower().startswith('tags:'):
            tag_str = stripped[5:].strip()
            tags = [t.strip() for t in tag_str.split(',') if t.strip()]
            remaining = '\n'.join(lines[:i] + lines[i+1:])
            return remaining, tags
    return md_text, None


def save_article(markdown_file, custom_title=None, hashtags=None):
    """記事をnote.comの下書きとして保存する"""
    config = load_config()

    with open(markdown_file, encoding='utf-8') as f:
        md_text = f.read()

    md_text, file_hashtags = extract_hashtags(md_text)
    if hashtags is None:
        hashtags = file_hashtags

    title, body_html = md_to_note_html(md_text)
    if custom_title:
        title = custom_title

    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    login(opener, config['email'], config['password'])

    note_id, note_key = create_note(opener)
    success = save_draft(opener, note_id, title, body_html, hashtags)

    return {
        'note_id': note_id,
        'note_key': note_key,
        'title': title,
        'success': success
    }


def main():
    if len(sys.argv) < 2:
        print('Usage: python save_draft.py <markdown_file> [--title "title"] [--hashtags "tag1,tag2"]')
        sys.exit(1)

    md_file = sys.argv[1]
    custom_title = None
    hashtags = None

    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '--title' and i + 1 < len(sys.argv):
            custom_title = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--hashtags' and i + 1 < len(sys.argv):
            hashtags = [t.strip() for t in sys.argv[i + 1].split(',')]
            i += 2
        else:
            i += 1

    result = save_article(md_file, custom_title, hashtags)

    if result['success']:
        print(f"OK: \"{result['title']}\"")
        print(f"  note_id: {result['note_id']}")
        print(f"  note_key: {result['note_key']}")
        print(f"  url: https://note.com/notes/{result['note_key']}/edit")
    else:
        print(f"FAILED: draft_save returned false")
        sys.exit(1)


if __name__ == '__main__':
    main()
