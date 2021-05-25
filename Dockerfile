FROM python:3.7.8-slim-stretch

COPY requirements.txt constraints.txt /tmp
RUN pip3 install -c /tmp/constraints.txt -r /tmp/requirements.txt && rm -f /tmp/requirements.txt /tmp/constraints.txt

COPY . /fv3config
RUN cd /fv3config && pip3 install --no-deps --no-cache-dir . && rm -rf /fv3config
