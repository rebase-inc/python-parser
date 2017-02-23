FROM python:alpine

ARG PYTHON_COMMONS_HOST
ARG PYTHON_COMMONS_SCHEME
ARG PYTHON_COMMONS_PORT

RUN apk --quiet update && \
    apk --quiet add \
        --no-cache && \
    python3.6 -m venv /venv

COPY ./requirements.txt /

RUN source /venv/bin/activate && \
    pip --quiet install \
        --no-cache-dir \
        --trusted-host ${PYTHON_COMMONS_HOST} \
        --extra-index-url ${PYTHON_COMMONS_SCHEME}${PYTHON_COMMONS_HOST}:${PYTHON_COMMONS_PORT} \
        --requirement /requirements.txt

COPY ./server.py /

CMD ["/venv/bin/python", "-m", "server"]
