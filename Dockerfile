FROM python:3.7.8-slim-stretch

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt && rm -f /tmp/requirements.txt

COPY . /fv3config
RUN cd /fv3config && pip3 install --no-deps --no-cache-dir . && rm -rf /fv3config
