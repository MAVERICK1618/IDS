FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    apache2

# Fake vulnerable banner
RUN echo "ServerTokens Full" >> /etc/apache2/conf-enabled/security.conf \
    && echo "ServerSignature On" >> /etc/apache2/conf-enabled/security.conf

# Change displayed version to 2.2.8
RUN sed -i 's/Apache\\/2.4.41 (Ubuntu)/Apache\\/2.2.8/g' /etc/apache2/conf-enabled/security.conf || true

# Vulnerable test page
RUN echo '<html><body><h1>Apache HTTPD 2.2.8 Vulnerable Lab</h1></body></html>' > /var/www/html/index.html

EXPOSE 80

CMD ["/usr/sbin/apache2ctl", "-D", "FOREGROUND"]
