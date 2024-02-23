CREATE TABLE IF NOT EXISTS "profile" (
    "name" TEXT,
    "wallet" BIGINT DEFAULT 0,
    "bank" BIGINT DEFAULT 0,
    "user_id" BIGINT,
    "level" BIGINT DEFAULT 0,
    "xp" BIGINT DEFAULT 0,
    "job" BIGINT DEFAULT 0,
    PRIMARY KEY (user_id)
)

--CREATE TABLE IF NOT EXISTS "clans" (
    
---)



-- UID, LEVEL, XP, MULTI

-- NAME, OWNER_ID, CO_OWNER_ID, OFFICERS_ID, MEMBERS