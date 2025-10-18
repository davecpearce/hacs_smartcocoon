FROM python:3.13.2-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Source .env file if it exists (mounted from host)
RUN echo 'if [ -f /workspaces/hacs_smartcocoon/.devcontainer/.env ]; then set -a && source /workspaces/hacs_smartcocoon/.devcontainer/.env && set +a; fi' >> /etc/bash.bashrc

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libssl-dev \
    libjpeg-dev \
    zlib1g-dev \
    libpcap-dev \
    git \
    curl \
    ca-certificates \
    gnupg \
    lsb-release \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Docker CLI
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update \
    && apt-get install -y docker-ce-cli \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install GitHub CLI
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update \
    && apt-get install -y gh \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install act (GitHub Actions locally)
RUN curl -fsSL https://raw.githubusercontent.com/nektos/act/master/install.sh | bash \
    && mv ./bin/act /usr/local/bin/act \
    && chmod +x /usr/local/bin/act

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
