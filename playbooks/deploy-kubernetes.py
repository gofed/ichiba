#!/bin/python

from subprocess import call
import os
import json
import yaml

def getScriptDir(file = __file__):
	return os.path.dirname(os.path.realpath(file))

RED = '\033[91m'
GREEN = '\033[92m'
BLUE = '\033[94m'
CYAN = '\033[96m'
WHITE = '\033[97m'
YELLOW = '\033[93m'
MAGENTA = '\033[95m'
GREY = '\033[90m'
BLACK = '\033[90m'
DEFAULT = '\033[99m'
ENDC = '\033[0m'

class AtomicTask(object):

	def __init__(self, command):
		self._command = yaml.load(command)
		self._ichiba_client = "%s/../client/client.py" % getScriptDir(__file__)
		self._dry = False

	def run(self):
		if "provider" not in self._command:
			provider = "docker"
		else:
			provider = self._command["provider"]

		cmd = "%s --provider %s %s %s %s" % (
			self._ichiba_client,
			provider,
			self._command["task"],
			self._command["command"],
			" ".join(self._command["args"])
		)

		print "%stask | %s%s" % (GREEN, self._command["name"], ENDC)
		if self._dry:
			print "%s%s%s" % (WHITE, cmd, ENDC)
		else:
			rc = call(cmd, shell=True)
			if rc > 0:
				exit(rc)

# build kubernetes, artefacts in build.json
AtomicTask("""
  name: Build kubernetes
  provider: host
  task: kubernetes
  command: build
  args:
    - "--os Fedora"
    - "--commit 72fbb5193b839af17d732631e932de8889850a16"
    - "--build-target rawhide"
""").run()

# Assumming kubernetes is built on x86_64 only
with open("build.json", "r") as f:
	data = json.load(f)

rpms = filter(lambda l: not l.endswith(".src.rpm"), data["taskinfo"]["archs"][0]["Output"])
url_base = "https://kojipkgs.fedoraproject.org/%s" % "/".join(rpms[0].split("/")[3:-1])
url_sufix = "-".join(rpms[0].split("/")[-1].split("-")[-2:])

# provision cluster
AtomicTask("""
  name: Provision cluster
  task: jenkins-client
  command: provision
  args:
    - "--os Fedora"
    - "--flavor m1.small"
    - "--size 3"
""").run()

# deploy kubernetes on the cluster
AtomicTask("""
  name: Deploy Kubernetes with ansible
  task: kubernetes
  command: deploy
  args:
    - "--source-type-upstream"
    - "--resource-from-file resources.json"
    - "--extra-vars 'flannel_subnet=10.253.0.0 flannel_prefix=16 kube_master_api_port=6443 kube_cert_ip=_use_aws_external_ip_ open_cadvisor_port=true kube_source_type=distribution-rpm kube_rpm_url_base=%s kube_rpm_url_sufix=%s'"
""" % (url_base, url_sufix)).run()
