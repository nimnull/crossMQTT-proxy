FROM python:3.12-slim

ENV WORKDIR="/opt/srv"
ENV POETRY_HOME="/opt/poetry"
ENV POETRY_NO_INTERACTION=1
ENV POETRY_VIRTUALENVS_PATH="/opt/venvs"
ENV PATH="$POETRY_HOME/bin:/opt/bin:$PATH"

CMD ["make", "run_local"]
WORKDIR ${WORKDIR}

RUN useradd -ms /bin/bash mqtt-bridge
RUN apt-get update --fix-missing\
 && apt-get install -y --no-install-recommends\
 libffi.*\
 zlib1g\
 unzip\
 make\
 curl\
 procps\
 && curl -sSL https://install.python-poetry.org | python3 -

COPY poetry.lock pyproject.toml ./
COPY bridge/__init__.py bridge/

RUN savedAptMark="$(apt-mark showmanual)"\
 && apt-get update --fix-missing\
 && apt-get install -y --no-install-recommends\
 # install dev packages
 build-essential\
 libffi-dev\
 zlib1g-dev\
 # install python packages
 && poetry install --no-dev -v \
 # clear packages
 && apt-mark auto '.*' > /dev/null\
 && apt-mark manual $savedAptMark\
 && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false\
 && rm -rf ~/.cache/pip\
 && rm -rf /var/lib/apt/lists/*

COPY . .
RUN chown -R mqtt-bridge:mqtt-bridge /opt

USER mqtt-bridge
