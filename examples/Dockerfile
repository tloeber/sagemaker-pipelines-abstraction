
ARG PYTHON_VERSION

FROM python:${PYTHON_VERSION}
# Copy library, because we will install it from local source
COPY src/ /opt/
COPY pyproject.toml /opt/

# Set up the examples-package
WORKDIR /opt/app
COPY ./ ./

RUN pip install . && \
    make mark-sagemaker-sdk-as-typed
