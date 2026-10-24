CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY,
 username TEXT NOT NULL UNIQUE,
 name TEXT NOT NULL,
 password_hash TEXT NOT NULL,
 role TEXT NOT NULL CHECK(role IN ('MEMBER','MODERATOR','ADMIN')),
 active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
 balance INTEGER NOT NULL DEFAULT 0,
 session_version INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS skins (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 name TEXT NOT NULL,
 weapon TEXT NOT NULL,
 rarity TEXT NOT NULL,
 wear TEXT NOT NULL,
 float_value REAL NOT NULL,
 reference_price INTEGER NOT NULL DEFAULT 100,
 active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
 created_at TEXT NOT NULL,
 updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS inventory (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 skin_id INTEGER NOT NULL REFERENCES skins(id),
 owner_id INTEGER NOT NULL REFERENCES users(id),
 acquired_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS listings (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 item_id INTEGER NOT NULL REFERENCES inventory(id),
 seller_id INTEGER NOT NULL REFERENCES users(id),
 buyer_id INTEGER REFERENCES users(id),
 price INTEGER NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('ACTIVE','SOLD','CANCELLED','HIDDEN')),
 moderation_reason TEXT NOT NULL DEFAULT '',
 created_at TEXT NOT NULL,
 updated_at TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS single_active_listing ON listings(item_id) WHERE status='ACTIVE';
CREATE TABLE IF NOT EXISTS trades (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 proposer_id INTEGER NOT NULL REFERENCES users(id),
 recipient_id INTEGER NOT NULL REFERENCES users(id),
 give_item_id INTEGER NOT NULL REFERENCES inventory(id),
 want_item_id INTEGER NOT NULL REFERENCES inventory(id),
 status TEXT NOT NULL CHECK(status IN ('PENDING','ACCEPTED','REJECTED','CANCELLED')),
 created_at TEXT NOT NULL,
 updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS history (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 actor_id INTEGER NOT NULL REFERENCES users(id),
 other_id INTEGER REFERENCES users(id),
 action TEXT NOT NULL,
 entity_type TEXT NOT NULL,
 entity_id INTEGER NOT NULL,
 detail TEXT NOT NULL,
 created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS notifications (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 recipient_id INTEGER NOT NULL REFERENCES users(id),
 event_type TEXT NOT NULL,
 body TEXT NOT NULL,
 entity_type TEXT NOT NULL,
 entity_id INTEGER NOT NULL,
 is_read INTEGER NOT NULL DEFAULT 0 CHECK(is_read IN (0,1)),
 created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS idempotency (
 user_id INTEGER NOT NULL REFERENCES users(id),
 method TEXT NOT NULL,
 path TEXT NOT NULL,
 request_key TEXT NOT NULL,
 digest TEXT NOT NULL,
 body TEXT NOT NULL,
 status INTEGER NOT NULL,
 PRIMARY KEY(user_id,method,path,request_key)
);
CREATE INDEX IF NOT EXISTS inventory_owner ON inventory(owner_id,id);
CREATE INDEX IF NOT EXISTS listings_status ON listings(status,id);
CREATE INDEX IF NOT EXISTS trades_parties ON trades(proposer_id,recipient_id,status);
CREATE INDEX IF NOT EXISTS notifications_user ON notifications(recipient_id,id);
CREATE INDEX IF NOT EXISTS history_parties ON history(actor_id,other_id,id);
