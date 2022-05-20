FROM python:3.7.3

COPY /app /etc/usr/src/app

WORKDIR /etc/usr/src/app

RUN pip install paho-mqtt
RUN pip install requests

ENTRYPOINT ["python"]
CMD ["message_router.py"]