
ARG PYTHON_VERSION

FROM python:${PYTHON_VERSION}
WORKDIR /opt/app
COPY ./ ./
RUN pip install . && \
    make mark-sagemaker-sdk-as-typed