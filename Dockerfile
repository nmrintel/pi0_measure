# Use NVIDIA CUDA base image for GPU support
FROM nvidia/cuda:12.1.1-devel-ubuntu22.04

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    cmake \
    build-essential \
    python3.10 \
    python3-pip \
    python3-dev \
    pkg-config \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavutil-dev \
    libswscale-dev \
    libswresample-dev \
    libavfilter-dev \
    wget \
    curl \
    ca-certificates \
    openssh-client \
    nvtop \
    && rm -rf /var/lib/apt/lists/*

# Set python3.10 as the default python
RUN ln -s /usr/bin/python3.10 /usr/bin/python

# Install ffmpeg 7.x
# Since Ubuntu 22.04 might not have 7.x in default repos, we can use a PPA or build from source.
# For simplicity and reliability in a Dockerfile, we'll use a known static build or a reliable PPA.
# Here we use the conda-forge approach mentioned in the docs if possible,
# but in a pure Dockerfile (non-conda), we might want to use a static build.
RUN wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz \
    && tar -xvf ffmpeg-release-amd64-static.tar.xz \
    && mv ffmpeg-*-amd64-static/ffmpeg /usr/local/bin/ \
    && mv ffmpeg-*-amd64-static/ffprobe /usr/local/bin/ \
    && rm -rf ffmpeg-*-amd64-static*

# Upgrade pip
RUN python3 -m pip install --no-cache-dir --upgrade pip

# Clone lerobot repository into /opt for caching
WORKDIR /opt
RUN git clone https://github.com/huggingface/lerobot.git

# Install lerobot with all extras, including pi0, and debugpy in the cached location
WORKDIR /opt/lerobot
RUN pip install --no-cache-dir -e ".[all,pi]"

# Switch back to workspace
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entrypoint script
COPY entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["/bin/bash"]
