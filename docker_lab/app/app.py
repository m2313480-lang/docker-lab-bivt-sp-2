import os
from datetime import datetime, timezone

from flask import Flask, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)


def get_conn():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "postgres"),
        port=int(os.environ.get("DB_PORT", "5432")),
        dbname=os.environ.get("DB_NAME", "default"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD", "postgres"),
    )


def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS request_log (
                    id SERIAL PRIMARY KEY,
                    path TEXT NOT NULL,
                    method TEXT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL
                );
                """
            )


@app.route("/api/v1/get", methods=["GET"])
def get_requests():
    init_db()
    now = datetime.now(timezone.utc)
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "INSERT INTO request_log(path, method, created_at) VALUES (%s, %s, %s)",
                (request.path, request.method, now),
            )
            cur.execute("SELECT id, path, method, created_at FROM request_log ORDER BY id")
            rows = cur.fetchall()
    return jsonify({"message": "Request logged successfully", "requests": rows})


@app.route("/", methods=["GET"])
def index():
    return jsonify({"status": "ok", "try": "/api/v1/get"})


if __name__ == "__main__":
    port = int(os.environ.get("SERVER_PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
