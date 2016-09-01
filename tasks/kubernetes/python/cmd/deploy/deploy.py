#!/bin/python

# GOAL:
# 1. choose ansible source: rpm, master HEAD, master HEAD+PR
# 1. get the ansible (yum/dnf install kubernetes-ansible, git clone github.com/kubernetes/contrib + install deps)
# 1. pick inventory: localhost, dynamic inventory
# 1. run ansible (or its subset based on settings)

# Target OS is determined by cluster
from subprocess import call
import os
import uuid
import logging
import tempfile
import json
import shutil

from cmdsignature.parser import CmdSignatureParser

def getScriptDir(file = __file__):
	return os.path.dirname(os.path.realpath(file))

DYNAMIC_INVENTORY_FILE = "%s/../../dynamic_inventory.py" % getScriptDir()

def installAnsible(source_type, pr = 0):
	if source_type == "upstream" or source_type == "PR":
		rc = call("git clone http://github.com/kubernetes/contrib", shell=True)
		if rc != 0:
			exit(rc)
	
		if source_type == "PR":
			os.chdir("contrib")
			print "\nMergin master branch with PR '%s'\n" % pr
			new_branch_name = "BRANCHNAME-%s" % uuid.uuid4()
			if call("git fetch origin pull/%s/head:%s" % (pr, new_branch_name), shell=True) != 0:
				logging.error("Unable to fetch PR number '%s'" % pr)
				exit(1)
			if call("git checkout %s" % new_branch_name, shell=True) != 0:
				logging.error("Unable to checkout PR number '%s'" % pr)
				exit(1)
			if call("git merge master --no-edit", shell=True) != 0:
				logging.error("Unable to merge PR number '%s' with master" % pr)
				exit(1)
			os.chdir("..")

		return "%s/contrib/ansible" % os.getcwd()

	if source_type == "distribution-rpm":
		# kubernetes-ansible installed?
		if call("rpm -q kubernetes-ansible", shell=True) > 0:
			logging.error("kubernetes-ansible not installed")
			exit(1)

		return "/usr/share/kubernetes-ansible/"

	logging.error("source type '%s' not recognized" % source_type)
	exit(1)

def runAnsible(inventory_type, resource_file = "", private_key = "", extravars = "", script = "deploy-cluster.sh"):

	envs = []

	if inventory_type == "localhost":
		envs.append({"name": "INVENTORY", "value": os.path.abspath("inventory/localhost.ini")})
	elif inventory_type in ["from-file", "from-string"]:
		# copy dynamic inventory script into inventory directory (so it is at the same directory as group_vars)
		# TODO(jchaloup): remove the copy once the dynamic inventory gets merged
		shutil.copy(DYNAMIC_INVENTORY_FILE, "inventory/dynamic_inventory.py")
		dynamic_inventory_file_abs = os.path.abspath("inventory/dynamic_inventory.py")

		envs.append({"name": "RESOURCE_FILE", "value": resource_file})
		envs.append({"name": "INVENTORY", "value": dynamic_inventory_file_abs})
	else:
		logging.error("inventory type '%s' not supported" % inventory_type)
		exit(1)

	if private_key != "":
		envs.append({"name": "ANSIBLE_PRIVATE_KEY_FILE", "value": os.path.abspath(private_key)})

	envs.append({"name": "ANSIBLE_HOST_KEY_CHECKING", "value": "False"})

	cmd = "%s ./%s" % (" ".join(map(lambda l: "%s=%s" % (l["name"], l["value"]), envs)), script)
	if extravars != "":
		cmd = "%s --extra-vars %s" % (cmd, repr(extravars))

	os.chdir("scripts")

	print "\nRunning ansible...\n"
	return call(cmd, shell=True)

if __name__ == "__main__":

	cur_dir = getScriptDir(__file__)
	gen_flags = "%s/deploy.yml" % (cur_dir)

	parser = CmdSignatureParser([gen_flags]).generate().parse()
	if not parser.check():
		exit(1)

	options = parser.options()
	args = parser.args()

	source_type = ""
	pr = 0
	if options.sourcetypeupstream:
		source_type = "upstream"
	elif options.sourcetypepr:
		source_type = "PR"
		pr = options.sourcetypepr
	elif options.sourcetyperpm:
		source_type = "distribution-rpm"
	else:
		logging.error("Source type not recognized")
		exit(1)

	resource_file = ""
	if options.localinventory:
		inventory_type = "localhost"
	elif options.resourcefromfile != "":
		inventory_type = "from-file"
		resource_file = os.path.abspath(options.resourcefromfile)
	elif options.resourcefromstring != "":
		inventory_type = "from-string"
		with tempfile.NamedTemporaryFile(delete=False) as temp:
			json.dump(json.loads(options.resourcefromstring), temp)
			temp.flush()
			resource_file = temp.name

	script = "deploy-cluster.sh"
	if options.deploy != "":
		script = "deploy-%s.sh" % options.deploy
	elif options.restart != "":
		script = "restart-%s.sh" % options.deploy
	elif options.update != "":
		script = "update-%s.sh" % options.deploy

	# from rpm of via git clone
	ansible_location = installAnsible(source_type, pr)
	os.chdir(ansible_location)

	# run the playbook
	rc = runAnsible(inventory_type, resource_file, options.privatekey, options.extravars, script)

	if inventory_type == "from-string":
		os.unlink(temp.name)

	exit(rc)
