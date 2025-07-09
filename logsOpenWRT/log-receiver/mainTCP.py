import socket
import mysql.connector
import time
import re
from datetime import datetime
from collections import defaultdict
from flask import Flask, Response
from threading import Thread
from queue import Queue

# Константы
TCP_IP = "0.0.0.0"
TCP_PORT = 9999
WORKER_COUNT = 4
MESSAGE_QUEUE = Queue()

FACILITY_LABELS = {
    0: "KERNEL", 1: "USER", 2: "MAIL", 3: "DAEMON", 4: "AUTH",
    5: "SYSLOG", 6: "LPR", 7: "NEWS", 8: "UUCP", 9: "CRON",
    10: "AUTHPRIV", 11: "FTP", 16: "LOCAL0", 17: "LOCAL1", 18: "LOCAL2",
    19: "LOCAL3", 20: "LOCAL4", 21: "LOCAL5", 22: "LOCAL6", 23: "LOCAL7"
}

SEVERITY_LABELS = ['EMERG', 'ALERT', 'CRIT', 'ERR', 'WARNING', 'NOTICE', 'INFO', 'DEBUG']

DB_CONFIG = {
    'host': 'mysql',
    'user': 'loguser',
    'password': 'logpass',
    'database': 'logs'
}

log_count = 0
severity_counter = defaultdict(int)
facility_counter = defaultdict(int)
source_ip_counter = defaultdict(int)

app = Flask(__name__)

# Подключение к БД
for attempt in range(10):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        break
    except mysql.connector.errors.DatabaseError:
        print(f"⏳ [{attempt+1}/10] Ожидание MySQL...")
        time.sleep(3)
else:
    raise RuntimeError("Невозможно подключиться к MySQL")

cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        received_at DATETIME,
        facility_code INT,
        facility_label VARCHAR(20),
        severity_code INT,
        severity_label VARCHAR(10),
        content TEXT,
        source_ip VARCHAR(45),
        source_port INT
    )
""")
conn.commit()

# Парсинг syslog
def parse_syslog_header(text):
    match = re.match(r"<(\d+)>", text)
    if match:
        priority = int(match.group(1))
        facility = priority // 8
        severity = priority % 8
        facility_label = FACILITY_LABELS.get(facility, "UNKNOWN")
        severity_label = SEVERITY_LABELS[severity]
        return facility, facility_label, severity, severity_label
    return None, "UNKNOWN", None, "UNKNOWN"

# TCP Listener
def run_tcp_listener():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((TCP_IP, TCP_PORT))
    server_socket.listen()
    print(f"[TCP] Слушаем порт {TCP_PORT}...")

    while True:
        conn, addr = server_socket.accept()
        Thread(target=handle_tcp_client, args=(conn, addr), daemon=True).start()

def handle_tcp_client(conn, addr):
    source_ip, source_port = addr
    with conn:
        while True:
            data = conn.recv(4096)
            if not data:
                break
            MESSAGE_QUEUE.put((data.decode('utf-8', errors='replace'), addr, datetime.now()))

# Воркер БД
def db_worker():
    db = mysql.connector.connect(**DB_CONFIG)
    cur = db.cursor()

    global log_count
    while True:
        log_text, addr, received_at = MESSAGE_QUEUE.get()
        source_ip, source_port = addr

        facility_code, facility_label, severity_code, severity_label = parse_syslog_header(log_text)

        cur.execute("""
            INSERT INTO logs (
                received_at, facility_code, facility_label,
                severity_code, severity_label, content,
                source_ip, source_port
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            received_at, facility_code, facility_label,
            severity_code, severity_label, log_text,
            source_ip, source_port
        ))
        db.commit()

        log_count += 1
        severity_counter[severity_label] += 1
        facility_counter[facility_label] += 1
        source_ip_counter[source_ip] += 1

        print(f"[{received_at}] {source_ip}:{source_port} → {severity_label} [{facility_label}] — {log_text}")

# Метрики
@app.route('/metrics')
def metrics():
    response = "# HELP log_receiver_log_count_total Total logs received\n"
    response += f"log_receiver_log_count_total {log_count}\n"
    for key, val in severity_counter.items():
        response += f"log_receiver_severity_total{{level=\"{key}\"}} {val}\n"
    for key, val in facility_counter.items():
        response += f"log_receiver_facility_total{{facility=\"{key}\"}} {val}\n"
    for ip, val in source_ip_counter.items():
        response += f"log_receiver_source_ip_total{{ip=\"{ip}\"}} {val}\n"
    return Response(response, mimetype='text/plain')

# Запуск
if __name__ == "__main__":
    Thread(target=run_tcp_listener, daemon=True).start()
    for _ in range(WORKER_COUNT):
        Thread(target=db_worker, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
