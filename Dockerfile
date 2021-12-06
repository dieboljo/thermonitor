# syntax=docker/dockerfile:1

FROM nikolaik/python-nodejs:latest
ENV NODE_ENV=production

WORKDIR /app

COPY py/requirements.txt py/requirements.txt
COPY js/aviader/package.json js/package.json

RUN pip3 install -r py/requirements.txt
RUN yarn --cwd js install

COPY js/aviader js
COPY py/src/thermonitor py
COPY thermonitor.sh thermonitor.sh

CMD ./thermonitor.sh
