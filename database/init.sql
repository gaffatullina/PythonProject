CREATE TABLE IF NOT EXISTS services (
    id SERIAL PRIMARY KEY,             
    name TEXT NOT NULL,                
    master1_price TEXT,      
    master2_price TEXT     
);

ALTER TABLE services ADD CONSTRAINT unique_service_name UNIQUE (name);

CREATE TABLE cart (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    service_name TEXT NOT NULL,
    min_price NUMERIC,
    max_price NUMERIC,
    comment TEXT
);

CREATE INDEX IF NOT EXISTS idx_cart_user_id ON cart(user_id);