FROM giusedroid/ffmpeg-lgpl:ubuntu

WORKDIR /tmp/workdir

COPY task/utils.py /tmp/workdir
COPY task/task.py /tmp/workdir

ENTRYPOINT python3 task.py
