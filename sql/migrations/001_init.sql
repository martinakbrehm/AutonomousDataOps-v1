-- Inicial migration: cria tabelas de logs e issues
-- Compatível com Postgres

CREATE TABLE IF NOT EXISTS logs (
    id SERIAL PRIMARY KEY,
    agent TEXT,
    action TEXT,
    detail TEXT,
    ts TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS issues (
    id SERIAL PRIMARY KEY,
    source TEXT,
    detail TEXT,
    severity TEXT,
    ts TIMESTAMP WITH TIME ZONE DEFAULT now()
);
