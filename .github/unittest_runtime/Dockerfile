FROM ubuntu

RUN \
    apt-get update && \
    apt-get install -y xvfb libgtk-3-0 git curl python3 --no-install-recommends && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/*

COPY *.sh /

ENTRYPOINT ["/entrypoint.sh"]
