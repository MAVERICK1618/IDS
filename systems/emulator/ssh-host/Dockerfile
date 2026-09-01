eeFROM debian:stretch-slim
# Force use of archive mirrors since stretch is EOL
RUN sed -i 's/deb.debian.org/archive.debian.org/g' /etc/apt/sources.list \
&& sed -i 's/security.debian.org/archive.debian.org/g' /etc/apt/sources.list \
&& sed -i '/stretch-updates/d' /etc/apt/sources.list || true
RUN apt-get -o Acquire::Check-Valid-Until=false update && apt-get install -y wget build-essential zlib1g-dev libssl-dev --force-yes
RUN wget https://cdn.openbsd.org/pub/OpenBSD/OpenSSH/portable/openssh-4.7p1.tar.gz \
&& tar -xzf openssh-4.7p1.tar.gz \
&& cd openssh-4.7p1 \
&& ./configure --prefix=/usr --sysconfdir=/etc/ssh \
&& make \
&& make install
RUN useradd -m admin && echo 'admin:admin123' | chpasswd \
&& mkdir -p /var/run/sshd
EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
