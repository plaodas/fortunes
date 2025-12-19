-- Initial migration: create a simple table to record analyses
CREATE TABLE IF NOT EXISTS analyses (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  birth_date DATE NOT NULL,
  birth_hour INT NOT NULL,
  result JSONB NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Insert a sample seed entry
INSERT INTO analyses (name, birth_date, birth_hour, result)
VALUES ('テスト 太郎', '1990-01-01', 12, '{"sample": true}');
