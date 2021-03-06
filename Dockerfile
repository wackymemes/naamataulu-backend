FROM debian:stretch

RUN apt-get update -y
RUN apt-get install -y python3-pip \
    python3-dev \
    build-essential \
    cmake \
    libsm6 \
    libxext6 \
    libxrender1

COPY requirements.txt .

# Install dlib first
RUN pip3 install --no-cache-dir dlib==19.16.0

RUN pip3 install --no-cache-dir -r requirements.txt

ADD src ./src/
COPY ./docker-entrypoint.sh /

CMD ["sh", "./docker-entrypoint.sh"]