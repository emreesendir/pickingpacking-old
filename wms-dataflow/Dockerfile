FROM ubuntu:latest

RUN apt update && apt upgrade -y

RUN apt install -y -q python3-pip python3-dev

ENV TZ=Europe/Zurich
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN mkdir -p /home/app

WORKDIR /home/app

COPY ./app/requirements.txt .

RUN pip3 install -r requirements.txt

COPY ./app .

CMD ["python3", "main.py"]