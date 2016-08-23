# Kubernetes automation of common scenarios

# Available scenarios

* deploy ``Kubernetes`` cluster with ``Ansible`` playbooks

## Kubernetes deployment with Ansible

Once can configure to install kubernetes from various sources.

### Distribution based installation

```
$ ichiba kubernetes deploy [OPTIONS] --extra-vars "kube_source_type=package-manager"
```

### Github release installation

```
$ ichiba kubernetes deploy [OPTIONS] --extra-vars "kube_source_type=github-release kube_version=1.3.5"
```

### Rpm based installation

```
$ ichiba kubernetes deploy [OPTIONS] \
  --extra-vars "\
  kube_source_type=distribution-rpm \
  kube_rpm_url_base=https://kojipkgs.fedoraproject.org//packages/kubernetes/1.3.0/0.2.git507d3a7.fc26/x86_64 \
  kube_rpm_url_sufix=1.3.0-0.2.git507d3a7.fc26.x86_64.rpm \
  "
```

## TODO

* add ``--koji-build=1.3.0-0.2.git507d3a7.fc26`` to generate ``kube_source_type=distribution-rpm kube_rpm_url_base=https://kojipkgs.fedoraproject.org//packages/kubernetes/1.3.0/0.2.git507d3a7.fc26/x86_64 kube_rpm_url_sufix=1.3.0-0.2.git507d3a7.fc26.x86_64.rpm`` instead
* add ``--kube-version=1.3.5`` to generate ``kube_source_type=github-release kube_version=1.3.5`` instead
