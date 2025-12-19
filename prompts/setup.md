以下のサービスの開発準備をお願いします。

サービス名：Fortunes
タイトル：Fortunes -四柱推命と姓名判断から本当のあなたを暴きます


初めはMVPとして以下の機能を実装：
  - フロントで名前、生年月日、生まれた時間（１時間単位）の入力
  - バックエンドで命式と画数を計算して （ダミーデータ）JSON を返す
    - result = {
        "year": "乙卯",
        "month": "戊寅",
        "day": "辛巳",
        "hour": "乙卯",
        "nameAnalysis": {
          "tenkaku": 26,
          "jinkaku": 15,
          "chikaku": 11,
          "gaikaku": 22,
          "soukaku": 37,
          "summary": "努力家で晩年安定"
        }
      }
    - フロントでUIに表示、グラフで五行バランスを可視化


構成：
docker composeで以下の環境をセットアップ
  - バックエンド：Python/FastAPI
    - テーブル作成、初期データはmigrationファイルで管理
    -
  - DB: PostgreSQL
  - フロントエンド：React/Next, PWAアプリ

githubでのソース管理を前提とし、mainブランチpushの際はGithub actionsでのテストを実施します。
