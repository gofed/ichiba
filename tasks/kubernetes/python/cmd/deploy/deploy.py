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

from cmdsignatureparser import CmdSignatureParser

def getScriptDir(file = __file__):
	return os.path.dirname(os.path.realpath(file))

DYNAMIC_INVENTORY_FILE = "%s/../../dynamic_inventory.py" % getScriptDir()

def installAnsible(source_type, pr = 0):
	if source_type == "upstream" or source_type == "PR":
		rc = call("git clone http://github.com/kubernetes/contrib", shell=True)
		if rc != 0:
			exit(rc)
	
		os.chdir("contrib")
		if source_type == "PR":
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

	elif source_type == "distribution-rpm":
		raise NotImplementedError
		# run yum/dnf install kubernetes-ansible -y
	else:
		logging.error("source type '%s' not recognized" % source_type)
		exit(1)

def runAnsible(inventory_type, resource_file = ""):

	if inventory_type == "localhost":
		cmd = "INVENTORY=%s ./deploy-cluster.sh" % os.path.abspath("ansible/inventory/localhost.ini")
	elif inventory_type in ["from-file", "from-string"]:
		# copy dynamic inventory script into inventory directory (so it is at the same directory as group_vars)
		# TODO(jchaloup): remove the copy once the dynamic inventory gets merged
		shutil.copy(DYNAMIC_INVENTORY_FILE, "ansible/inventory/dynamic_inventory.py")
		dynamic_inventory_file_abs = os.path.abspath("ansible/inventory/dynamic_inventory.py")

		cmd = "RESOURCE_FILE=%s INVENTORY=%s ./deploy-cluster.sh" % (resource_file, dynamic_inventory_file_abs)
	else:
		logging.error("inventory type '%s' not supported" % inventory_type)
		exit(1)

	os.chdir("ansible/scripts")
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

	# from rpm of via git clone
	# TODO(jchaloup): install ansible should return ansible location
	#                 to which is cd'ed here, not in the function itself
	installAnsible(source_type, pr)

	# run the playbook
	rc = runAnsible(inventory_type, resource_file)

	if inventory_type == "from-string":
		os.unlink(temp.name)

	exit(rc)
