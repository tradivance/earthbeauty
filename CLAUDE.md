# CLAUDE.md — earthbeauty

Claude Codeで動くSEO記事作成システム。キーワードグルーピングCSVに基づいて、構成→執筆→品質チェック→note.com入稿を一気通貫で実行する。

## 概要
- **ジャンル**: シェアサロン・レンタルサロン（女性セラピスト向け独立支援）
- **記事計画**: `data/keyword-groups.csv` にKWグルーピングを管理
- **入稿先**: note.com（下書き保存）
- **noteアカウント**: https://note.com/earth_beauty22

## ワークフロー
1. `/seo-start` — 新しい記事のプランニングから入稿まで一気通貫
2. `/seo-1-plan` — 記事構成を策定
3. `/seo-2-write` — 記事を執筆
4. `/seo-3-check` — 品質チェック
5. `/seo-4-publish` — note.comに下書き保存

## フォルダ構成
```
earthbeauty/
├── CLAUDE.md              # このファイル
├── README.md              # セットアップガイド
├── .claude/commands/      # スキル定義（seo-*）
├── config/
│   ├── site.md            # サイト情報
│   ├── target.md          # ターゲット像（ペルソナ含む）
│   ├── tone.md            # トーン＆マナー
│   ├── writing-rules.md   # ライティングルール
│   └── article-goal.md    # 記事のゴール・CTA設計
├── data/
│   └── keyword-groups.csv # KWグルーピング
├── articles/              # 記事成果物（slug/article.md, structure.md）
├── knowledge-base/        # 参考記事・トーンサンプル・ペルソナ
│   ├── README.md
│   ├── share-salon-story.md    # シェアサロンを始めた理由（原稿）
│   ├── existing-articles.md    # 投稿済み7記事のトーンサンプル
│   └── persona-mikako.md      # ペルソナストーリー
└── tools/
    └── note-api/
        ├── save_draft.py        # note.com下書き保存
        ├── quality_check.py     # 品質チェック
        └── config.example.json  # 設定テンプレート
```

## Git運用ルール
- 自動コミットは絶対にしない
- ユーザーが「コミットして」と言ったときだけ実行する
- `git add .` は使わない（ファイル名を具体的に指定）

## 記事作成の運用ルール（必読）

### CSVベースのキーワード管理
- `data/keyword-groups.csv` に記事のKWグルーピングを定義
- 記事#を指定して、対応するKW群を自動で読み込む
- CSVが空の場合はキーワードを直接入力してもOK
- CSVの列: 記事#, 記事テーマ, キーワード, 月間Vol, 検索意図, 記事内での役割, トレンド

### 文字数の選択肢
- **2,000〜3,000字**: ベース（通常の記事）
- **3,000〜5,000字**: 中〜長め（詳しく解説する記事）
- **5,000字以上**: 長文（網羅的なガイド記事）

### 品質チェック・文字数計測
- ツールで自動実行してよい。ユーザーへの確認は不要
- 計測結果はユーザーに共有する

### 最終確認（入稿前に必須）
- 品質チェック合格後、**必ず以下をユーザーに提示してOKをもらう**
  1. 記事ファイルのフルパス
  2. 狙いキーワード一覧（検索数・トレンド・配置場所）
- ユーザーのOKなしに `save_draft.py` を実行してはいけない

### キーワード表示（構成確認・本文確認のたびに）
- 構成提案時・本文確認時は必ず以下の形式でKW一覧を表示する

```
| キーワード | 月間Vol | トレンド | 主な配置 |
|-----------|---------|---------|---------|
| シェアサロン 東京 | X,XXX | 安定 | タイトル・H2 |
```

### キーワードの入れ方
- タイトルにメインKW（H1/ブログKW）を含める
- H2見出しの50%以上に狙いKWを散りばめる
- structure.mdの各H2に `（KW: ...）` メモで対応KWを明記する
- SEO狙いで不自然になるなら「の」を入れるなど変形してよい

### カスタマイズポイント
- `data/keyword-groups.csv` にKWグルーピングを追加・更新
- `config/` 配下の設定ファイルを必要に応じて調整
- `tools/note-api/config.json` にnote.comアカウント情報を設定
- `knowledge-base/` に参考記事・トーンサンプルを追加
