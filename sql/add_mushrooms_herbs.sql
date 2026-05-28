-- Таблицы каталога: грибы и травы (структура как у насекомых)

CREATE TABLE IF NOT EXISTS mushrooms (
    id SERIAL PRIMARY KEY,
    name_ru VARCHAR(255) NOT NULL,
    name_lat VARCHAR(255),
    size_min NUMERIC(10, 2),
    size_max NUMERIC(10, 2),
    color TEXT,
    habitat TEXT,
    season TEXT,
    description TEXT,
    image_url TEXT
);

CREATE TABLE IF NOT EXISTS herbs (
    id SERIAL PRIMARY KEY,
    name_ru VARCHAR(255) NOT NULL,
    name_lat VARCHAR(255),
    size_min NUMERIC(10, 2),
    size_max NUMERIC(10, 2),
    color TEXT,
    habitat TEXT,
    season TEXT,
    description TEXT,
    image_url TEXT
);

CREATE INDEX IF NOT EXISTS idx_mushrooms_habitat ON mushrooms(habitat);
CREATE INDEX IF NOT EXISTS idx_mushrooms_season ON mushrooms(season);
CREATE INDEX IF NOT EXISTS idx_herbs_habitat ON herbs(habitat);
CREATE INDEX IF NOT EXISTS idx_herbs_season ON herbs(season);
CREATE INDEX IF NOT EXISTS idx_herbs_color ON herbs(color);
