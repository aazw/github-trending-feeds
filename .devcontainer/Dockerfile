# debian version
# 10 (Buster)
# 11 (Bullseye)
# 12 (Bookworm)
# 13 (Trixie)
# 14 (Forky)

# for main image
ARG DOCKER_DEBIAN_VERSION=12.11

# for builder images
ARG DOCKER_GO_VERSION=1.24.4-bookworm
ARG DOCKER_NODE_VERSION=22.17.0-bookworm
ARG DOCKER_PYTHON_VERSION=3.13.5-bookworm

# for go install
ARG GO_DOCKERFMT_VERSION=v0.3.7
ARG GO_SHFMT_VERSION=v3.11.0
ARG GO_GO_TASK_VERSION=v3.44.0

# for npm tools
ARG NPM_NPM_VERSION=11.4.2
ARG NPM_PRETTIER_VERSION=3.6.2
ARG NPM_RENOVATE_VERSION=41.15.0
ARG NPM_CLAUDE_CODE_VERSION=1.0.35
ARG NPM_CCUSAGE_VERSION=15.2.0

# for pip tools
ARG PIP_PIP_VERSION=25.1.1
ARG PIP_PIPX_VERSION=1.7.1
ARG PIP_UV_VERSION=0.7.16
ARG PIP_RUFF_VERSION=0.12.1

# for other tools (github-tags)
ARG OTHER_JQ_VERSION=1.8.0
ARG OTHER_YQ_VERSION=4.45.4
ARG OTHER_XQ_VERSION=1.3.0
ARG OTHER_TAPLO_VERSION=0.10.0
ARG OTHER_SHELLCHECK_VERSION=v0.10.0
ARG OTHER_RIPGREP_VERSION=14.1.1

# ##########################################################################################
# builder images
# ##########################################################################################

# golang
# https://hub.docker.com/_/golang
FROM golang:${DOCKER_GO_VERSION} AS golang-builder

# dockerfmt
# https://github.com/reteps/dockerfmt
ARG GO_DOCKERFMT_VERSION
RUN go install github.com/reteps/dockerfmt@${GO_DOCKERFMT_VERSION}

# shfmt
# https://github.com/mvdan/sh
ARG GO_SHFMT_VERSION
RUN go install mvdan.cc/sh/v3/cmd/shfmt@${GO_SHFMT_VERSION}

# go-task
# https://github.com/go-task/task
# https://taskfile.dev/
ARG GO_GO_TASK_VERSION
RUN go install github.com/go-task/task/v3/cmd/task@${GO_GO_TASK_VERSION}

# node
# https://hub.docker.com/_/node
# https://note.milldea.com/posts/two-ways-to-install-nodejs-with-fixed-version-in-dockerfile
FROM node:${DOCKER_NODE_VERSION} AS node-builder

# python
# https://hub.docker.com/_/python
FROM python:${DOCKER_PYTHON_VERSION} AS python-builder
RUN mkdir -p /python-install \
    && cp -r /usr/local/bin /python-install/ \
    && cp -r /usr/local/lib /python-install/ \
    && cp -r /usr/local/include /python-install/ \
    && rm -rf /python-install/lib/pkgconfig

# ##########################################################################################
# main image
# ##########################################################################################

# debian
# https://hub.docker.com/_/debian/
FROM debian:${DOCKER_DEBIAN_VERSION}
ENV DEBIAN_FRONTEND=noninteractive
ENV DEBCONF_NOWARNINGS=yes

# add distribution packages
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    wget \
    git \
    nano \
    less \
    gzip \
    tar \
    unzip \
    xz-utils \
    locales-all

# dockerfmt
# refs above
COPY --from=golang-builder /go/bin/dockerfmt /usr/local/bin/

# shfmt
# refs above
COPY --from=golang-builder /go/bin/shfmt /usr/local/bin/

# go-task
# refs above
COPY --from=golang-builder /go/bin/task /usr/local/bin/

# node
# refs above
COPY --from=node-builder /usr/local/bin/node /usr/local/bin/node
COPY --from=node-builder /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s /usr/local/bin/node /usr/local/bin/nodejs \
    && ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npx

# python
# refs above
RUN apt-get update -y && apt-get install -y expat
COPY --from=python-builder /python-install/bin/ /usr/local/bin/
COPY --from=python-builder /python-install/lib/ /usr/local/lib/
COPY --from=python-builder /python-install/include/ /usr/local/include/
ENV PIP_ROOT_USER_ACTION=ignore

# npm
# https://github.com/npm/cli
# https://www.npmjs.com/package/npm
ARG NPM_NPM_VERSION
RUN npm install -g npm@${NPM_NPM_VERSION}

# prettier
# https://prettier.io/docs/install
ARG NPM_PRETTIER_VERSION
RUN npm install -g prettier@${NPM_PRETTIER_VERSION}

# renovate
# https://github.com/renovatebot/renovate
# https://www.npmjs.com/package/renovate
ARG NPM_RENOVATE_VERSION
RUN npm install -g renovate@${NPM_RENOVATE_VERSION}

# claude-code
# https://github.com/anthropics/claude-code
# https://github.com/anthropics/claude-code/blob/main/.devcontainer/devcontainer.json
# https://github.com/anthropics/claude-code/blob/main/.devcontainer/Dockerfile
# https://github.com/anthropics/claude-code/blob/main/.devcontainer/init-firewall.sh
RUN apt-get update -y && apt-get install -y \
    less \
    git \
    procps \
    sudo \
    fzf \
    zsh \
    man-db \
    unzip \
    gnupg2 \
    gh \
    iptables \
    ipset \
    iproute2 \
    dnsutils \
    aggregate
ARG NPM_CLAUDE_CODE_VERSION
RUN npm install -g @anthropic-ai/claude-code@${NPM_CLAUDE_CODE_VERSION}
ENV DEVCONTAINER=true

## ccusage
# https://github.com/ryoppippi/ccusage
# https://www.npmjs.com/package/ccusage
ARG NPM_CCUSAGE_VERSION
RUN npm install -g ccusage@${NPM_CCUSAGE_VERSION}

# pip
# https://pypi.org/project/pip/
ARG PIP_PIP_VERSION
RUN pip install --upgrade pip==${PIP_PIP_VERSION}

# pipx
# https://github.com/pypa/pipx
ARG PIP_PIPX_VERSION
RUN pip install pipx==${PIP_PIPX_VERSION}

# uv
# https://github.com/astral-sh/uv
# https://pypi.org/project/uv/
ARG PIP_UV_VERSION
RUN pip install uv==${PIP_UV_VERSION}

# ruff
# https://github.com/astral-sh/ruff
ARG PIP_RUFF_VERSION
RUN pip install ruff==${PIP_RUFF_VERSION}

# jq
# https://github.com/jqlang/jq
ARG OTHER_JQ_VERSION
RUN curl -fsSL -o /jq https://github.com/jqlang/jq/releases/download/jq-${OTHER_JQ_VERSION}/jq-linux-$(uname -m | sed 's/aarch64/arm64/' | sed 's/x86_64/amd64/') \
    && chmod +x /jq \
    && mv /jq /usr/local/bin/ \
    && jq --version

# yq
# https://github.com/mikefarah/yq
# https://hub.docker.com/r/mikefarah/yq
ARG OTHER_YQ_VERSION
RUN curl -fsSL -o /yq https://github.com/mikefarah/yq/releases/download/v${OTHER_YQ_VERSION}/yq_linux_$(uname -m | sed 's/aarch64/arm64/' | sed 's/x86_64/amd64/') \
    && chmod +x /yq \
    && mv /yq /usr/local/bin/ \
    && yq --version

# xq
# https://github.com/sibprogrammer/xq
ARG OTHER_XQ_VERSION
RUN curl -fsSL -o /xq.tar.gz https://github.com/sibprogrammer/xq/releases/download/v${OTHER_XQ_VERSION}/xq_${OTHER_XQ_VERSION}_linux_$(uname -m | sed 's/aarch64/arm64/' | sed 's/x86_64/amd64/').tar.gz \
    && mkdir -p /xq \
    && tar -xvzf /xq.tar.gz -C /xq/ \
    && chmod +x /xq/xq \
    && mv /xq/xq /usr/local/bin/ \
    && rm /xq.tar.gz \
    && rm -rf /xq \
    && xq --version

# taplo
# https://github.com/tamasfe/taplo
# https://taplo.tamasfe.dev/
# https://hub.docker.com/r/tamasfe/taplo
ARG OTHER_TAPLO_VERSION
RUN curl -fsSL -o /taplo.gz https://github.com/tamasfe/taplo/releases/download/${OTHER_TAPLO_VERSION}/taplo-linux-$(uname -m | sed 's/arm64/aarch64/' | sed 's/amd64/x86_64/').gz \
    && gzip -d /taplo.gz \
    && chmod +x /taplo \
    && mv /taplo /usr/local/bin/ \
    && taplo --version

# shellcheck
# https://github.com/koalaman/shellcheck
# https://hub.docker.com/r/koalaman/shellcheck
ARG OTHER_SHELLCHECK_VERSION
RUN curl -fsSL -o /shellcheck.tar.xz https://github.com/koalaman/shellcheck/releases/download/${OTHER_SHELLCHECK_VERSION}/shellcheck-${OTHER_SHELLCHECK_VERSION}.linux.$(uname -m | sed 's/arm64/aarch64/' | sed 's/amd64/x86_64/').tar.xz \
    && tar -xvf /shellcheck.tar.xz -C / \
    && chmod +x /shellcheck-${OTHER_SHELLCHECK_VERSION}/shellcheck \
    && mv /shellcheck-${OTHER_SHELLCHECK_VERSION}/shellcheck /usr/local/bin/ \
    && rm /shellcheck.tar.xz \
    && rm -rf /shellcheck-${OTHER_SHELLCHECK_VERSION} \
    && shellcheck --version

# ripgrep
# https://github.com/BurntSushi/ripgrep
ARG OTHER_RIPGREP_VERSION
RUN mkdir -p /ripgrep \
    && curl -fsSL -o /ripgrep/ripgrep.tar.gz -L https://github.com/BurntSushi/ripgrep/releases/download/${OTHER_RIPGREP_VERSION}/ripgrep-${OTHER_RIPGREP_VERSION}-$(uname -m)-unknown-linux-gnu.tar.gz \
    && cd /ripgrep \
    && tar -xvzf ripgrep.tar.gz \
    && mv ripgrep-${OTHER_RIPGREP_VERSION}-$(uname -m)-unknown-linux-gnu/rg /usr/local/bin/ \
    && chmod +x /usr/local/bin/rg \
    && rm -rf /ripgrep

# add vscode user
# https://code.visualstudio.com/remote/advancedcontainers/add-nonroot-user#_creating-a-nonroot-user
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL >/etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME
USER $USERNAME
