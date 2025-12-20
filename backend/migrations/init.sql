-- Initial migration: create a simple table to record analyses
CREATE TABLE IF NOT EXISTS analyses (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  birth_date DATE NOT NULL,
  birth_hour INT NOT NULL,
  result_birth JSONB NOT NULL,
  result_name JSONB NOT NULL,
  summary TEXT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Insert a sample seed entry
INSERT INTO analyses (name, birth_date, birth_hour, result_birth, result_name, summary)
VALUES (
  'テスト 太郎',
  '1990-01-01',
  12,
  '{"meisiki": {"year": "乙卯","month": "戊寅","day": "辛巳","hour": "乙卯","summary": "辛（金）は「宝石のような金属」で、繊細で美意識が高く、こだわりを持つタイプ。巳（火）は金を鍛える火で、試練や努力を通じて磨かれる運勢を示します"}, "gogyo":{"wood": 26,"fire": 15,"earth": 11,"metal": 22,"water": 37,"summary": "「木（金を切る）と火（金を溶かす）が多いため、日主の辛（金）は試練を受けやすいが、努力で輝きを増すタイプ。人間関係や環境から刺激を受けて成長する人生。"}, "summary": "美意識やこだわりを持ち、周囲から「個性的」「センスがある」と見られやすい。人との縁が強く、交流や人脈が人生のテーマ。試練を通じて磨かれる運勢で、困難を乗り越えるほど輝きが増す。晩年は人間関係に恵まれ、後進を育てる立場に向く。柔軟性・流れ」を意識するとさらに良い"}',
  '{"tenkaku": 26,"jinkaku": 15,"chikaku": 11,"gaikaku": 22,"soukaku": 37,"summary": "努力家で晩年安定"}',
  '全体的にバランスが良く、特に水の要素が強いです。柔軟性と流れを意識するとさらに良いでしょう。名前の五格も努力家で晩年安定しています。'
);
