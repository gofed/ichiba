#!/bin/python

from subprocess import call
import os
import json
import yaml

def getScriptDir(file = __file__):
	return os.path.dirname(os.path.realpath(file))

class AtomicTask(object):

	def __init__(self, command, dry=False):
		self._command = yaml.load(command)
		self._ichiba_client = "%s/../client/client.py" % getScriptDir(__file__)
		self._dry = dry

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

		print "task | %s" % self._command["name"]
		if self._dry:
			print cmd
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

with open("build.json", "r") as f:
	print json.load(f)

