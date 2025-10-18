FROM mcr.microsoft.com/devcontainers/python:3.13.2

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt update \
    && sudo apt install -y libpcap-dev vim curl jq \
    && mkdir -p /opt

WORKDIR /opt

RUN git clone --depth=1 -b dev https://github.com/home-assistant/core.git hass \
    && python3 -m pip --disable-pip-version-check install --upgrade ./hass

WORKDIR /workspaces/hacs_smartcocoon
COPY requirements.txt ./
COPY requirements_test.txt ./
RUN python3 -m pip install -r requirements_test.txt

# Setup the Home Assistant environment
WORKDIR /opt/hass
RUN ./script/setup

# Create symlink for the custom component (this will be done after container starts)
WORKDIR /workspaces/hacs_smartcocoon

# Add a post-create script to set up the symlink
RUN echo '#!/bin/bash\n\
if [ ! -L "/opt/hass/homeassistant/components/smartcocoon" ]; then\n\
    ln -s /workspaces/hacs_smartcocoon/custom_components/smartcocoon /opt/hass/homeassistant/components/smartcocoon\n\
    echo "Created symlink for smartcocoon component"\n\
fi' > /usr/local/bin/setup-component.sh && chmod +x /usr/local/bin/setup-component.sh

ENV SHELL /bin/bash
