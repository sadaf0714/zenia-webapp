FROM ubuntu:22.04

ENV HOST=0.0.0.0
ENV PORT=3001

#Args
ARG GIT_USERNAME
ARG GIT_PASSWORD

#Builder Process

# Set the working directory in the container
WORKDIR /zenia_app/vector-embedding

# Install Python Git and other dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    git \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Clone private repo
RUN /bin/bash -c "git clone --depth 1 --branch feature/dockerized https://${GIT_USERNAME}:${GIT_PASSWORD}@github.com/ZeniaGraph/vector-embedding.git" 

ADD requirements.txt /zenia_app/vector-embedding/requirements.txt

RUN pip install -r ./requirements.txt

ADD . .

CMD ["python3", "./src/main.py"]


 