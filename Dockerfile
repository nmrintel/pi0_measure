# Use Official PyTorch 2.7.1 image with CUDA 12.6 and cuDNN 9
FROM pytorch/pytorch:2.7.1-cuda12.8-cudnn9-devel

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
# Note: The base image already has python, but we need other build tools and libraries.
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    cmake \
    build-essential \
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

# The base image has python 3.11 installed as default, so we don't need to install or symlink python3.10.


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
# Install only the necessary dependencies for PI0 benchmark
# (Avoids conflicts in [all] that break build)
RUN pip install --no-cache-dir -e ".[pi]"

# Copy entrypoint script (TODO: remove this)
COPY entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["/bin/bash"]
