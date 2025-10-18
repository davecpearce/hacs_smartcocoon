FROM mcr.microsoft.com/devcontainers/python:3.13.2

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt update \
    && apt install -y libpcap-dev vim curl jq git \
    && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt update \
    && apt install -y gh \
    && mkdir -p /opt

WORKDIR /opt

RUN git clone --depth=1 -b dev https://github.com/home-assistant/core.git hass \
    && python3 -m pip --disable-pip-version-check install --upgrade ./hass \
    && ln -s /workspaces/hacs_smartcocoon/custom_components/smartcocoon /opt/hass/homeassistant/components/smartcocoon

WORKDIR /workspaces/hacs_smartcocoon
COPY requirements.txt ./
COPY requirements_test.txt ./
RUN python3 -m pip install -r requirements_test.txt

# Setup the Home Assistant enviropnment
WORKDIR /opt/hass
RUN ./script/setup

# Copy Git setup script
WORKDIR /workspaces/hacs_smartcocoon
COPY .devcontainer/setup-git.sh /usr/local/bin/setup-git.sh
RUN chmod +x /usr/local/bin/setup-git.sh

ENV SHELL /bin/bash
