
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    description TEXT,
    embedding VECTOR(3) -- Adjust the dimension as needed
);