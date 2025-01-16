FROM mcr.microsoft.com/devcontainers/python:1-3.12-bullseye
ENV TMPPROVDIR=/tmp/provisioning
COPY provisioning $TMPPROVDIR
RUN \
$TMPPROVDIR/10-install_packages.sh && \
$TMPPROVDIR/12-configure_freeradius.sh