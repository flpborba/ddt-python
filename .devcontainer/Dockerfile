FROM sagemath/sagemath:10.9

USER root

RUN apt update -y
RUN apt install -y git

RUN sage -python -m pip install --no-cache-dir black==26.5.1
RUN sage -python -m pip install --no-cache-dir isort==8.0.1
