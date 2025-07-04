# LoggerOpenWRT
External logger for openWRT

## The setup is done for the machine

- OS: Ubuntu 24.04.2 LTS
- Platform: x86_64
- Processor: Intel(R) Core(TM) i5-6500 CPU @ 3.20GHz (4 cores)
- RAM: 32GB DDR4 2133 MHz
- Storage: SSD 120GB

## Ports used (external):
- 8088 - dozzle (for docker monitoring)
- 2020 UDP - receive logs (syslog openWRT)
- 2221 HTTP - metrics for Prometheus
- 2222 - HTTP - PhpMyAdmin
- 2223 - TCP - MySQL
- 2224 - HTTP - Prometheus
- 2225 - HTTP - Grafana

## Install Docker
```
apt update
apt install docker.io
docker --version
systemctl start docker
systemctl enable docker
systemctl status docker
```

## Install Docker-compose
```
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
docker-compose --version
```

## Install Dozzle
This is a lightweight open-source an application with a web interface designed to monitor Docker container logs in real time. It allows you to track events in logs without having to access the file system.

[Dozzle](https://github.com/)

## Remove

```
sudo docker-compose down --volumes --remove-orphans
sudo docker image prune -a
sudo docker-compose build --no-cache
sudo docker-compose up -d
```
