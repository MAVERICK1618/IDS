FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

# Fix possible time validation issues
RUN apt-get -o Acquire::Check-Valid-Until=false update && \
    apt-get install -y \
    samba \
    smbclient

# Create public share directory
RUN mkdir -p /srv/samba/public && \
    chmod -R 777 /srv/samba/public

# Create Samba user properly
RUN useradd -m smbuser && \
    (echo "password"; echo "password") | smbpasswd -a -s smbuser

# Configure Samba
RUN printf '%s\n' \
"[global]" \
"workgroup = WORKGROUP" \
"server string = Vulnerable Samba Server" \
"security = user" \
"map to guest = Bad User" \
"" \
"[public]" \
"path = /srv/samba/public" \
"browseable = yes" \
"writable = yes" \
"guest ok = yes" \
"read only = no" \
> /etc/samba/smb.conf

EXPOSE 139 445

CMD ["/usr/sbin/smbd", "--foreground", "--no-process-group"]
