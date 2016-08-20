FROM	fedora:23
MAINTAINER Jan Chaloupka <jchaloup@redhat.com>

LABEL Name="jenkins-client" \
      Version="v0.0.1"

# install deps
RUN dnf install -y python-pip PyYAML python-requests && dnf clean all

# create workplace
RUN useradd jenkins-client && mkdir -p /home/jenkins-client

# copy worker implementation into the image
COPY python/ /home/jenkins-client/

ENV PYTHONPATH /home/jenkins-client

# set entrypoint
CMD ["/home/jenkins-client/jenkins-client.py"]

