FROM python:3.6
LABEL maintainer Tito
ENV PYTHONUNBUFFERED 1
RUN apt-get update \
  && apt-get install -y python3-dev \
                        mysql-client \
                        libsasl2-dev \
                        libldap2-dev \
                        default-libmysqlclient-dev \
                        postgresql-client \
                        vim \
  && rm -rf /var/lib/apt/lists/*
WORKDIR /home/vlabsServer
COPY ./requirements.txt .
RUN pip3 install -r requirements.txt
COPY . .
RUN mkdir -p static

