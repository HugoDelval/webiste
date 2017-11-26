# My website

Why not being opensource about it ?

## Flask

Built with the microframework [Flask](https://github.com/pallets/flask)

## Run it ?

```bash
docker build -t website .
docker run -e google_passwd=<YOUR_GMAIL_PASSWD_HERE> -p 80:8080 -dt --restart unless-stopped website
```