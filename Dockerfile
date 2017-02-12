FROM alpine

ARG PYTHON_COMMONS_HOST
ARG PYTHON_COMMONS_SCHEME
ARG PYTHON_COMMONS_PORT

RUN apk --quiet update && \
    apk --quiet add \
        --no-cache \
        py-virtualenv \
        python3 && \
    pyvenv /venv

COPY ./requirements.txt /
COPY ./server.py /

RUN source /venv/bin/activate && \
    pip --quiet install \
        --no-cache-dir \
        --trusted-host ${PYTHON_COMMONS_HOST} \
        --extra-index-url ${PYTHON_COMMONS_SCHEME}${PYTHON_COMMONS_HOST}:${PYTHON_COMMONS_PORT} \
        --requirement /requirements.txt

CMD ["/venv/bin/python", "-m", "server"]
