# ガイダンス調査AI (Guidance Survey AI)

## 1. プロジェクト概要

ユーザーからアップロードされたレポート（例: TNFDレポート）を、Vertex AI Searchに構築されたナレッジベースと照合し、評価・改善点を構造化された形式で出力するAIエージェントです。

### 参考アーキテクチャ

- [google/adk-samples](https://github.com/google/adk-samples)
- [kkrishnan90/vertex-ai-search-agent-builder-demo](https://github.com/kkrishnan90/vertex-ai-search-agent-builder-demo)

## 2. 主要技術スタック

- **言語**: Python 3.10+
- **エージェントフレームワーク**: Google ADK (Agent Development Kit) の思想に準拠
- **Webフレームワーク**: FastAPI
- **ナレッジベース**: Vertex AI Search (Enterprise Search)
- **デプロイ先**: Cloud Run
- **フロントエンド連携**: Vertex AI Agent Builder のカスタムツールとして連携

## 3. セットアップと実行

### 3.1. 前提条件

- Google Cloud SDK (`gcloud`) がインストール・設定済みであること
- Python 3.10以上がインストール済みであること

### 3.2. インストール

```bash
pip install -r requirements.txt
```

### 3.3. 認証

Vertex AI Search APIを呼び出すために、認証トークンを取得します。

```bash
gcloud auth application-default login
gcloud auth print-access-token
```

取得したトークンを環境変数に設定するか、コード内で直接利用します。（**注意: 本番環境ではより安全な認証方法を検討してください**）

### 3.4. ローカルでの実行

```bash
uvicorn app.main:app --reload
```

サーバーは `http://127.0.0.1:8000` で起動します。

## 4. APIエンドポイント

### `/audit`

- **メソッド**: `POST`
- **説明**: 監査対象のレポート内容を受け取り、評価プロセスを実行し、最終的な評価結果を返します。
- **リクエストボディ**:
  ```json
  {
    "report_text": "監査対象のレポート全文..."
  }
  ```
- **レスポンス**:
  ```json
  {
    "evaluation_results": [
      {
        "item": "評価項目1",
        "evaluation": "評価結果",
        "suggestion": "改善提案",
        "reference": "参照箇所"
      }
    ]
  }
  ```

## 5. 開発者向け情報

### 5.1. プロジェクト構造

```
/guidance-survey-agent
|
├── app/
│   ├── __init__.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── supervisor_agent.py
│   │   └── sub_agents.py
│   ├── tools/
│   │   ├── __init__.py
│   │   └── search_tool.py
│   └── main.py
|
├── Dockerfile
├── requirements.txt
└── README.md
```

### 5.2. TODO

- `app/tools/search_tool.py`:
  - `PROJECT_ID` などの変数をハードコーディングから環境変数などに変更する。
- `app/agents/`:
  - 各サブエージェントの具体的なロジックを実装する。
  - エラーハンドリングを強化する。
- `app/main.py`:
  - リクエストのバリデーションを実装する。
