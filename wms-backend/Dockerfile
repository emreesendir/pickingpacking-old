FROM ubuntu:latest

RUN apt update && apt upgrade -y

RUN apt install -y -q python3-pip python3-dev

RUN apt install default-libmysqlclient-dev -y

RUN mkdir -p /home/app

WORKDIR /home/app

COPY ./app/requirements.txt .

RUN pip3 install -r requirements.txt

COPY ./app .

EXPOSE 8000
CMD ["gunicorn", "wmsBackend.wsgi:application", "--bind", "0.0.0.0:8000", "--access-logfile", "/home/app/accessLog/access.log"]