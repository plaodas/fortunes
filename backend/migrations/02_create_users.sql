-- Create users table for authentication
CREATE TABLE IF NOT EXISTS "users" (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT UNIQUE,
    password_hash TEXT NOT NULL,
    display_name TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Helpful indexes (unique constraints already create indexes for username/email)
CREATE INDEX IF NOT EXISTS idx_users_username ON "users"(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON "users"(email);

-- Consider adding a trigger to update `updated_at` on row modification if desired.
