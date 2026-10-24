import os
from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# Render'da Environment Variable olarak ekleyeceğin Neon bağlantın
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db():
    # Neon bağlantısı için sslmode=require şart [citation:3]
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    return conn

@app.route("/")
def home():
    return jsonify({
        "status": "ok",
        "api": "TC/GSM Sorgu API",
        "kullanim": [
            "/api.php?tc=60055517694",
            "/api.php?gsm=5366081891",
            "/api.php?tc=X&gsm=Y"
        ]
    })

@app.route("/api.php")
def api_php():
    tc = request.args.get("tc", "").strip()
    gsm = request.args.get("gsm", "").strip()

    if not tc and not gsm:
        return jsonify({"status": "error", "message": "tc veya gsm gerekli"}), 400

    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # TC'den GSM bul
        if tc and not gsm:
            cur.execute("SELECT gsm FROM tc_gsm WHERE tc = %s LIMIT 50", (tc,))
            rows = cur.fetchall()
            result = [r['gsm'] for r in rows]
            return jsonify({"status": "ok", "tc": tc, "count": len(result), "gsm_list": result})

        # GSM'den TC bul
        if gsm and not tc:
            cur.execute("SELECT tc FROM tc_gsm WHERE gsm = %s LIMIT 50", (gsm,))
            rows = cur.fetchall()
            result = [r['tc'] for r in rows]
            return jsonify({"status": "ok", "gsm": gsm, "count": len(result), "tc_list": result})

        # İkisi de varsa eşleşme kontrolü
        cur.execute("SELECT tc, gsm FROM tc_gsm WHERE tc = %s AND gsm = %s LIMIT 1", (tc, gsm))
        row = cur.fetchone()
        if not row:
            return jsonify({"status": "not_found", "eslesme": False}), 404
        return jsonify({"status": "ok", "eslesme": True, "data": row})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
