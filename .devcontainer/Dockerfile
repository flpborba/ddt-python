FROM mcr.microsoft.com/devcontainers/miniconda:1-3

RUN conda config --add channels conda-forge
RUN conda config --set channel_priority strict
RUN conda install -c conda-forge mamba

COPY environment.yml /tmp/conda-tmp/

RUN mamba env create -n sage -f /tmp/conda-tmp/environment.yml -y
RUN mamba clean -a -y
