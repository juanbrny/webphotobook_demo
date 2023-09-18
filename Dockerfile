FROM registry.opensuse.org/opensuse/bci/python:latest
WORKDIR /home/
USER root
RUN mkdir static templates images
COPY content/flaskwebapp.py .
COPY content/static/ static/
COPY content/templates/ templates/
COPY content/database.db .
COPY content/myconf.yml .
COPY content/images/ images/
RUN zypper install -y python python3-Flask python3-Flask-RESTful python3-Flask-Login python3-Flask-Testing python3-Flask-Admin python3-pyaml python3-Werkzeug python3-Flask-HTTPAuth python3-pycryptodomex python3-pip python311-pipx busybox-adduser 
RUN pip install --break-system-packages Flask-BasicAuth
RUN chmod 1777 images/ ; chown nobody:nobody database.db myconf.yml 
# This app needs real power!
#USER nobody
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=flaskwebapp
# From my laptop to production, storage is not a problem
ENV FLASK_DEBUG=true
EXPOSE 5000
ENTRYPOINT [ "python3", "flaskwebapp.py" ]
