FROM ubuntu:latest
LABEL authors="Aleksey"

ENTRYPOINT ["top", "-b"]