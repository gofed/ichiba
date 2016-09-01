#!/bin/python

import logging
import optparse
import os

from cmdsignature.parser import CmdSignatureParser
from jenkins_client.provisioncluster import ProvisionCluster

def getScriptDir(file = __file__):
	return os.path.dirname(os.path.realpath(file))

if __name__ == "__main__":

	cur_dir = getScriptDir(__file__)
	gen_flags = "%s/provision.yml" % (cur_dir)

	parser = CmdSignatureParser([gen_flags]).generate().parse()
	if not parser.check():
		exit(1)

	options = parser.options()
	args = parser.args()

	# fixed options: masterurl, artefact_dest
	# job specific: job name, remaining options
	params = {}
	for key in vars(options):
		if key in ["masterurl", "artefactdest"]:
			continue

		params[key] = vars(options)[key]

	ProvisionCluster(master=options.masterurl, params=params).run(options.artefactdest)
