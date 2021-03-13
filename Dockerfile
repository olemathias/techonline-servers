FROM python:3
ENV PYTHONUNBUFFERED=1
WORKDIR /opt/techonline-servers
COPY . /opt/techonline-servers
# TODO Check what we need here
RUN apt-get update && apt-get install -y python-dev libsasl2-dev gcc libldap2-dev
RUN pip install -r requirements.txt
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
