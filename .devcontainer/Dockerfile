FROM python:3.13.2-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libssl-dev \
    libjpeg-dev \
    zlib1g-dev \
    libpcap-dev \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Clone and install Home Assistant core
WORKDIR /opt
RUN git clone --depth=1 -b dev https://github.com/home-assistant/core.git hass \
    && cd hass \
    && python3 -m pip install --upgrade pip \
    && python3 -m pip install -e . \
    && ./script/setup

# Install project dependencies
WORKDIR /workspaces/hacs_smartcocoon
COPY requirements*.txt ./
RUN python3 -m pip install -r requirements_test.txt

# Create symlink script
RUN echo '#!/bin/bash\n\
ln -sf /workspaces/hacs_smartcocoon/custom_components/smartcocoon /opt/hass/homeassistant/components/smartcocoon\n\
echo "Created symlink for smartcocoon component"' > /usr/local/bin/setup-component.sh \
    && chmod +x /usr/local/bin/setup-component.sh
