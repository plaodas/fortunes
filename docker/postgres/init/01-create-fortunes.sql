-- Create fortunes DB with UTF8 and Japanese UTF-8 locale
-- This script runs only when the DB cluster is initialized (empty PGDATA).
CREATE DATABASE fortunes
  WITH ENCODING='UTF8'
       LC_COLLATE='ja_JP.UTF-8'
       LC_CTYPE='ja_JP.UTF-8'
       TEMPLATE=template0;
