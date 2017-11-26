FROM python

COPY requirements.txt .
RUN pip3 install -r requirements.txt && rm requirements.txt
RUN apt-get update && apt-get install -y nginx

RUN mkdir -p /srv/app
WORKDIR /srv/app/

COPY website/ .
RUN mv nginx.site.conf /etc/nginx/sites-enabled/website && \
    useradd website && \
    chmod o-r . ./* && \
    chmod +r static -R && \
    chown website:website . -R

CMD service nginx start && \
    su website -c "python website.py"
