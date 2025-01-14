FROM docker.io/python:3.10.15-slim-bookworm

WORKDIR /workdir

COPY . .

EXPOSE 8000

RUN apt update

RUN apt install wget curl libpq-dev libgl1 libglib2.0-0 -y > /dev/null

RUN pip install -q -r requirements.txt

ENTRYPOINT ["fastapi","run","main.py"]
