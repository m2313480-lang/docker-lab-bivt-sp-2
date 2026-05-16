import os
import json
import time
import uuid
from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
import redis

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "lab2")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
REDIS_HOST = os.getenv("REDIS_HOST", "keydb")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
CACHE_TTL = int(os.getenv("CACHE_TTL", "60"))

cache = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)


def get_conn():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        cursor_factory=RealDictCursor,
    )


def wait_for_services():
    for _ in range(40):
        try:
            with get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
            cache.ping()
            return
        except Exception:
            time.sleep(1)
    raise RuntimeError("PostgreSQL or KeyDB is not available")


def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id UUID PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL
                )
                """
            )
        conn.commit()


def user_cache_key(user_id: str) -> str:
    return f"user:v1:{user_id}"


@app.get("/")
def index():
    return jsonify({
        "status": "ok",
        "lab": "Lab 2 - KeyDB/Redis cache-aside",
        "endpoints": [
            "POST /users",
            "GET /users/<id>",
            "PUT /users/<id>",
            "DELETE /users/<id>",
            "GET /cache/<id>",
        ],
    })


@app.post("/users")
def create_user():
    body = request.get_json(force=True)
    name = body.get("name", "Ivan Ivanov")
    email = body.get("email", "student@misis.edu")
    user_id = str(uuid.uuid4())
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (id, name, email) VALUES (%s, %s, %s) RETURNING id, name, email",
                (user_id, name, email),
            )
            user = dict(cur.fetchone())
        conn.commit()
    return jsonify(user), 201


@app.get("/users/<user_id>")
def get_user(user_id):
    key = user_cache_key(user_id)
    cached = cache.get(key)
    if cached:
        app.logger.info("User cache hit")
        data = json.loads(cached)
        data["source"] = "cache"
        return jsonify(data)

    app.logger.info("User cache miss")
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, email FROM users WHERE id = %s", (user_id,))
            user = cur.fetchone()
    if user is None:
        return jsonify({"error": "not found"}), 404

    data = dict(user)
    cache.setex(key, CACHE_TTL, json.dumps(data, default=str))
    data["source"] = "database"
    return jsonify(data)


@app.put("/users/<user_id>")
def update_user(user_id):
    body = request.get_json(force=True)
    name = body.get("name")
    email = body.get("email")
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, email FROM users WHERE id = %s", (user_id,))
            current = cur.fetchone()
            if current is None:
                return jsonify({"error": "not found"}), 404
            cur.execute(
                """
                UPDATE users
                SET name = COALESCE(%s, name), email = COALESCE(%s, email)
                WHERE id = %s
                RETURNING id, name, email
                """,
                (name, email, user_id),
            )
            updated = dict(cur.fetchone())
        conn.commit()

    cache.delete(user_cache_key(user_id))
    app.logger.info("User cache evict on update")
    updated["cache"] = "evicted"
    return jsonify(updated)


@app.delete("/users/<user_id>")
def delete_user(user_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
    cache.delete(user_cache_key(user_id))
    app.logger.info("User cache evict on delete")
    return jsonify({"deleted": user_id, "cache": "evicted"})


@app.get("/cache/<user_id>")
def get_cache(user_id):
    key = user_cache_key(user_id)
    ttl = cache.ttl(key)
    value = cache.get(key)
    return jsonify({"key": key, "ttl": ttl, "value": json.loads(value) if value else None})


if __name__ == "__main__":
    wait_for_services()
    init_db()
    app.run(host="0.0.0.0", port=int(os.getenv("SERVER_PORT", "8080")))
