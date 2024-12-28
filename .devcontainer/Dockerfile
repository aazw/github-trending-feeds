# https://hub.docker.com/r/microsoft/devcontainers-python
FROM mcr.microsoft.com/devcontainers/python:3

RUN apt-get -y update
RUN apt-get -y install \
    ca-certificates \
    curl \
    git 

# Install Docker
# https://matsuand.github.io/docs.docker.jp.onthefly/engine/install/debian/
RUN for pkg in docker.io docker-doc docker-compose podman-docker containerd runc; do sudo apt-get remove $pkg; done
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
RUN echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
RUN apt-get -y update
RUN apt-get -y install docker-ce docker-ce-cli containerd.io docker-compose-plugin docker-compose
