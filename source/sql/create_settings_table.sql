CREATE TABLE IF NOT EXISTS settings
(
    user_id INTEGER NOT NULL PRIMARY KEY
        CONSTRAINT setting_user_pkey REFERENCES telegram_user,
    allow_ru BOOLEAN NOT NULL,
    allow_be BOOLEAN NOT NULL,
    allow_uk BOOLEAN NOT NULL,
    beta_testing BOOLEAN NOT NULL DEFAULT FALSE
);
ALTER TABLE settings OWNER TO {};