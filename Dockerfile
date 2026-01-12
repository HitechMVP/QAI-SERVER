FROM python:3.10-bullseye
ENV DEBIAN_FRONTEND=noninteractive

ENV PIP_BREAK_SYSTEM_PACKAGES=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3-venv \
        python3-pip \
        libgpiod2 \
        udev \
        python3-tk \
        libatlas-base-dev \
        libprotobuf-dev \
        protobuf-compiler \
        libgl1 \
        libglib2.0-0 \
        libjpeg-dev \
        libpng-dev \
        libavcodec-dev \
        libavformat-dev \
        libswscale-dev \
        libqt5gui5 \
        libqt5core5a \
        libqt5widgets5 \
        libx11-6 \
        libxext6 \
        libxrender1 \
        libxft2 \
        ffmpeg \
        x11-apps \
        cron \
        git \
        \
        build-essential \
        libgpiod-dev \
        swig \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /app

COPY requirements.txt .

RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel && \
    pip3 install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y iw wireless-tools
    

COPY . /app

CMD python main.py

