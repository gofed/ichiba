FROM	fedora:23
MAINTAINER Jan Chaloupka <jchaloup@redhat.com>

LABEL Name="kubernetes" \
      Version="v0.0.1"

# install deps
RUN dnf install -y python-pip PyYAML python-requests git ansible python-netaddr kubernetes-ansible fedora-packager wget && dnf clean all

# configure git
RUN git config --global user.email "ichiba@gofed.com" && git config --global user.name "Gofed Ichiba"

# create workplace
RUN useradd kubernetes

# copy worker implementation into the image
COPY python/ /home/kubernetes/

ENV PYTHONPATH /home/kubernetes

# set entrypoint
CMD ["/home/kubernetes/kubernetes.py"]

