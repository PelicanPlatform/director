FROM almalinux:8

RUN dnf update -y && dnf install python39 -y

RUN yes | pip3 install flask flask_apscheduler requests tldextract maxminddb htcondor

COPY src/* /app/

EXPOSE 12000

#CMD ["python3", "/app/app.py"]





