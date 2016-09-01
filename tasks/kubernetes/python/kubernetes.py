#!/bin/python

import os
import sys
from cmdsignature.program import ProgramSignatureParser
from subprocess import call

def getScriptDir(file = __file__):
	return os.path.dirname(os.path.realpath(file))

def execCommand(command):
	return call(command, shell=True)

if __name__ == "__main__":

	script_dir = getScriptDir(__file__)

	parser = ProgramSignatureParser(
		"kubernetes",
		"%s/cmd" % script_dir
	).parse(
		["%s/main.yml" % script_dir],
		sys.argv[1:]
	)

	command = parser.signature()
	exit(execCommand(command))

