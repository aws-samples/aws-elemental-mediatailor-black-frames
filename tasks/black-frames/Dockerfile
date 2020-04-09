FROM jrottenberg/ffmpeg
LABEL maintainer="Giuseppe Battista <gbatt@amazon.co.uk>"

RUN apt-get update -yq && \
    apt-get install python3-dev python3-pip -yq && \
    apt-get autoremove -yq && \
    apt-get clean -yq

RUN pip3 install -U pip && python3 -m pip install awscli boto3

WORKDIR /tmp/workdir

COPY task/utils.py /tmp/workdir
COPY task/task.py /tmp/workdir

ENTRYPOINT python3 task.py
