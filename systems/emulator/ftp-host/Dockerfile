FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    libpam0g-dev \
    wget

# Clone the backdoored vsftpd source
RUN git clone https://github.com/DoctorKisow/vsftpd-2.3.4.git /opt/vsftpd-2.3.4

WORKDIR /opt/vsftpd-2.3.4

# Fix permissions
RUN chmod +x vsf_findlibs.sh

# Add PAM library support
RUN sed -i 's/^LIBS.*/& -lpam/' Makefile

# Create required directories and users
RUN mkdir -p /var/ftp/empty \
    && mkdir -p /usr/share/empty \
    && mkdir -p /home/ftp \
    && groupadd -g 47 vsftpd \
    && groupadd -g 48 ftp \
    && useradd -c "vsftpd User" -d /dev/null -g vsftpd -s /usr/sbin/nologin -u 47 vsftpd \
    && useradd -c anonymous_user -d /home/ftp -g ftp -s /usr/sbin/nologin -u 48 ftp

# Build and install
RUN make \
    && install -v -m 755 vsftpd /usr/sbin/vsftpd \
    && install -v -m 644 vsftpd.conf /etc/vsftpd.conf

# Configure vsftpd
RUN echo "listen=YES" >> /etc/vsftpd.conf \
    && echo "anonymous_enable=YES" >> /etc/vsftpd.conf \
    && echo "local_enable=YES" >> /etc/vsftpd.conf \
    && echo "write_enable=YES" >> /etc/vsftpd.conf

EXPOSE 21
EXPOSE 6200

CMD ["/usr/sbin/vsftpd", "/etc/vsftpd.conf"]
