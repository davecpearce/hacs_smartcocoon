FROM mcr.microsoft.com/vscode/devcontainers/python:0-3.12

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt update \
    && sudo apt install -y libpcap-dev vim curl jq \
    && mkdir -p /opt

WORKDIR /opt

RUN git clone --depth=1 -b dev https://github.com/home-assistant/core.git hass \
    && python3 -m pip --disable-pip-version-check install --upgrade ./hass \
    && ln -s /workspaces/hacs_smartcocoon/custom_components/smartcocoon /opt/hass/homeassistant/components/smartcocoon

WORKDIR /workspaces/hacs_mysmartcocoon
COPY requirements.txt ./
COPY requirements_test.txt ./
RUN python3 -m pip install -r requirements_test.txt

# Setup the Home Assistant enviropnment
WORKDIR /opt/hass
RUN ./script/setup

ENV SHELL /bin/bash
