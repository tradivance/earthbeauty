# earthbeauty

Claude Codeで動くSEO記事作成システム（Earth Beauty / シェアサロン向け）。キーワードグルーピングCSVから、構成→執筆→品質チェック→note.com入稿まで一気通貫で実行します。

## セットアップ

### 1. リポジトリをフォーク＆クローン

```bash
git clone https://github.com/YOUR_USERNAME/earthbeauty.git
cd earthbeauty
```

### 2. note.com認証情報を設定

```bash
cp tools/note-api/config.example.json tools/note-api/config.json
```

`config.json` を編集して、note.comのログイン情報を入力してください。

```json
{
  "email": "your-email@example.com",
  "password": "your-password",
  "account_url": "https://note.com/earth_beauty22"
}
```

### 3. Python環境

Python 3.8以上が必要です。追加パッケージのインストールは不要（標準ライブラリのみ使用）。

## 使い方

### Claude Codeで記事を作成

```
claude
> /note-start
```

記事番号を指定するか、キーワードを直接入力して記事作成を開始します。

### 個別ステップの実行

| コマンド | 説明 |
|---------|------|
| `/note-start` | 一気通貫（構成→執筆→チェック→入稿） |
| `/note-1-plan` | 構成作成のみ |
| `/note-2-write` | 執筆のみ（構成作成済みが前提） |
| `/note-3-check` | 品質チェックのみ |
| `/note-4-publish` | note.com入稿のみ |

### 文字数の選択肢

| 文字数 | 用途 |
|--------|------|
| 2,000〜3,000字 | ベース（通常の記事） |
| 3,000〜5,000字 | 中〜長め（詳しく解説する記事） |
| 5,000字以上 | 長文（網羅的なガイド記事） |

## カスタマイズ

| ファイル | 変更内容 |
|---------|---------|
| `data/keyword-groups.csv` | KWグルーピングの追加・更新 |
| `config/site.md` | サイト名・アカウント情報 |
| `config/target.md` | ターゲット読者像・ペルソナ |
| `config/tone.md` | 文章のトーン＆マナー |
| `config/writing-rules.md` | ライティングルール |
| `config/article-goal.md` | 記事のゴール・CTA設計 |
| `knowledge-base/` | 参考記事・トーンサンプル |

## フォルダ構成

```
earthbeauty/
├── CLAUDE.md              # Claude Code用システム設定
├── README.md              # このファイル
├── .claude/commands/      # Claude Codeスキル定義
├── config/                # サイト設定・ライティングルール
├── data/                  # KWグルーピングCSV
├── articles/              # 記事成果物
├── knowledge-base/        # 参考記事・ペルソナ
└── tools/note-api/        # note.com入稿ツール
```

## ライセンス

MIT License
