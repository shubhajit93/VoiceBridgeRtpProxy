FROM python:3.10-bullseye

RUN apt-get update \
    && apt-get install -y \
        gstreamer1.0-tools \
        gstreamer1.0-plugins-base \
        gstreamer1.0-plugins-good \
        gstreamer1.0-plugins-bad \
        gstreamer1.0-plugins-ugly \
        gstreamer1.0-libav \
        python3-gi \
        python3-gst-1.0 \
        vim \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    python3-dev \
    libgirepository1.0-dev  # Install gobject-introspection-1.0 development headers

RUN pip install poetry

# Create a new non-root user
RUN useradd -ms /bin/bash hishab

ENV APP_DIR=/app

WORKDIR ${APP_DIR}

COPY pyproject.toml ./
COPY src/ ./src/

RUN poetry config virtualenvs.create false
RUN poetry install --no-dev --no-interaction --no-ansi

CMD ["poetry", "run", "server"]