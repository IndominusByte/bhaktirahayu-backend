FROM ubuntu:18.04

RUN apt-get update && apt-get upgrade -y &&\
    apt-get install -y wget \
    build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev \
    libsqlite3-dev python-dev

RUN wget https://www.python.org/ftp/python/3.8.3/Python-3.8.3.tgz &&\
    tar -xf Python-3.8.3.tgz &&\
    cd Python-3.8.3 &&\
    ./configure --enable-optimizations &&\
    make -j8 &&\
    make altinstall

RUN update-alternatives --install /usr/bin/python3 python3 /usr/local/bin/python3.8 3 &&\
    update-alternatives --install /usr/bin/pip3 pip3 /usr/local/bin/pip3.8 3 &&\
    pip3 install --upgrade pip

RUN apt-get install -y tesseract-ocr tesseract-ocr-ind ffmpeg libsm6 libxext6

WORKDIR /app
COPY requirements.txt .
RUN pip3 install -r requirements.txt
COPY . .

CMD ["bash","docker-entrypoint.sh"]
