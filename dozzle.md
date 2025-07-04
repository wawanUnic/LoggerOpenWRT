# Dozzle monitoring service

### Web panel - port 2026

Does not work as root

Let's create a folder for work
```
mkdir dozzle
cd dozzle
```

Run the container for generating the configuration file
```
sudo docker run --name dozzle amir20/dozzle:latest generate admin --password password --email test@email.net --name "John Doe" >> users.yml
```

The created credentials are as follows
```
admin - admin
password - password
email - test@email.net
name - John Doe
```

Delete this container (it should have stopped itself)
```
sudo docker ps -a
sudo docker stop dozzle
sudo docker rm dozzle
```

Run the container (permanently work)
```
sudo docker run -d --restart unless-stopped --name dozzle -v /var/run/docker.sock:/var/run/docker.sock -v ~/dozzle:/data -p 2026:8080 amir20/dozzle:latest --auth-provider simple --auth-ttl 48h --enable-actions --no-analytics
```
