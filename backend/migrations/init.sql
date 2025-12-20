-- Initial migration: create a simple table to record analyses
CREATE TABLE IF NOT EXISTS analyses (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  birth_date DATE NOT NULL,
  birth_hour INT NOT NULL,
  result_birth JSONB NOT NULL,
  result_name JSONB NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Insert a sample seed entry
INSERT INTO analyses (name, birth_date, birth_hour, result_birth, result_name)
VALUES ('テスト 太郎', '1990-01-01', 12, '{"wood": 26,"fire": 15,"earth": 11,"metal": 22,"water": 37,"summary": "「柔軟性・流れ」を意識するとさらに良い"}','{"tenkaku": 26,"jinkaku": 15,"chikaku": 11,"gaikaku": 22,"soukaku": 37,"summary": "努力家で晩年安定"}');
