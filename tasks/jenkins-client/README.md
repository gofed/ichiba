# Jenkins CLI API

Trigger pre-deployed parametrized Jenkins Jobs from CLI.

## Requirements

* pre-deployed Jenkins Jobs
* running instance of Jenkins Master

## Examples

```sh
$ jenkins-cli provision --os Fedora --artefact-dest /tmp/workspace
```

Or a general case

```sh
$ jenkins-cli --job provision --os RHEL --cluster-size 2 --topology "{'image': 'RHEL-7.2-15102016'}"
```
