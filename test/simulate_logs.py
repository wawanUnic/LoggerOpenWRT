import socket
import time
import random
import argparse

parser = argparse.ArgumentParser(description="Лог-генератор для тестов log-receiver")
parser.add_argument("--ip", default="127.0.0.1", help="IP лог-сервера")
parser.add_argument("--port", type=int, default=9999, help="UDP порт лог-сервера")
parser.add_argument("--rate", type=int, default=50, help="Логов в секунду")
parser.add_argument("--duration", type=int, default=60, help="Длительность генерации (сек)")
parser.add_argument("--devices", type=int, default=5, help="Количество виртуальных устройств")
args = parser.parse_args()

UDP_IP = args.ip
UDP_PORT = args.port
MESSAGES_PER_SECOND = args.rate
DURATION = args.duration
DEVICE_COUNT = args.devices

# Генерация MAC + имён
def generate_devices(n):
    devs = []
    for i in range(n):
        mac = ":".join(f"{random.randint(0,255):02x}" for _ in range(6))
        name = f"device-{i+1}"
        devs.append((mac, name))
    return devs

devices = generate_devices(DEVICE_COUNT)
levels = ["INFO", "WARNING", "ERR", "NOTICE"]

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def generate_log():
    mac, name = random.choice(devices)
    level = random.choice(levels)
    ip = f"192.168.8.{random.randint(2, 254)}"
    return f"<{random.randint(10, 190)}>Jul  5 22:15:49 OpenWrt dnsmasq-dhcp[1]: [{level}] DHCPACK(br-lan) {ip} {mac} {name}"

# Основной цикл
print(f"📡 Отправка {MESSAGES_PER_SECOND} логов/сек на {UDP_IP}:{UDP_PORT} в течение {DURATION} сек...")
end_time = time.time() + DURATION
while time.time() < end_time:
    for _ in range(MESSAGES_PER_SECOND):
        msg = generate_log().encode('utf-8')
        sock.sendto(msg, (UDP_IP, UDP_PORT))
    time.sleep(1)

print("Генерация завершена.")
