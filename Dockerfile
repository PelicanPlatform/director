FROM almalinux:8

RUN dnf install -y wget bzip2 ca-certificates curl procps

# Download and install Miniconda
RUN wget -q https://repo.anaconda.com/miniconda/Miniconda3-py39_23.1.0-1-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh

# Set environment variables
ENV PATH="/opt/conda/bin:${PATH}"

# Initialize and activate base
RUN conda init bash
RUN echo "conda activate base" >> ~/.bashrc

# Install necessary Python packages
RUN conda install -y flask requests tldextract && \
    conda install -y -c conda-forge maxminddb python-htcondor flask-apscheduler

# Set up dirs needed by app
COPY src/osdf_cache_manager/ /app/
RUN mkdir /app/maxminddb

# Condor config stuff
RUN mkdir -p /etc/condor/config.d && \
    echo "SEC_DEFAULT_AUTHENTICATION_METHODS = SCITOKENS" > /etc/condor/config.d/00-local.conf
ENV CONDOR_CONFIG=/etc/condor/config.d/00-local.conf

EXPOSE 8443

CMD ["python3", "/app/app.py"]
