FROM python:3.7.3

COPY /app /etc/usr/src/app

WORKDIR /etc/usr/src/app

RUN pip install paho-mqtt requests Flask Flask-Cors

ENTRYPOINT ["python"]
CMD ["message_router.py"]