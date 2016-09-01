#!/bin/python

import re
import logging
import jinja2
import tempfile
import shutil
import os
from subprocess import PIPE, Popen, call
import json

from cmdsignature.parser import CmdSignatureParser

def renderTemplate(searchpath, template_file, template_vars):

	templateLoader = jinja2.FileSystemLoader( searchpath=searchpath )
	templateEnv = jinja2.Environment( loader=templateLoader )
	template = templateEnv.get_template( template_file )
	content = template.render( template_vars )

	return content

def getTemplateVars(git_describe, commit):
	git_describe_regex = r"v([^-]*)(-(.*))*-([0-9]+)-(g[a-zA-Z0-9]{7})"

	m = re.search(git_describe_regex, git_describe)
	if not m:
		logging.error("Git describe not in '%s' form" % git_describe_regex)
		exit(1)

	#0.1.git%{k8s_shortcommit}%{?dist}
	#0.17.alpha6.git%{k8s_shortcommit}%{?dist}

	version = m.group(1)
	if not m.group(3):
		release = "0.1"
	else:
		release = "0.1.%s" % re.sub("[.-]", "", m.group(3))

	return {
		"version": version,
		"release": release,
		"git_describe": git_describe,
		"commit": commit
	}

def getScriptDir(file = __file__):
	return os.path.dirname(os.path.realpath(file))

def runCommand(cmd):
	process = Popen(cmd, stderr=PIPE, stdout=PIPE, shell=True)
	stdout, stderr = process.communicate()
	rt = process.returncode
	
	return stdout, stderr, rt

# 1. clone repository
# 1. get git describe
# 1. generate tarball
# 1. generate spec file
# 1. generate srpm
# 1. generate scratch build

def run(commit, target_os = "Fedora", build_target = "rawhide"):
	script_dir = getScriptDir(__file__)

	cur_dir = os.getcwd()

	dirpath = tempfile.mkdtemp()
	os.chdir(dirpath)

	scratch_build_id = -1

	while True:
		# clone repository
		if call("git clone http://github.com/kubernetes/kubernetes", shell=True):
			break

		os.chdir("kubernetes")

		# checkout commit
		if call("git checkout %s" % commit, shell=True):
			break

		# get git describe
		so, se, rc = runCommand("git describe")
		if rc > 0:
			logging.error(se)
			break

		git_describe = so.split("\n")[0]

		# get commit info
		vars = getTemplateVars(git_describe, commit)

		# make sure the target directory exists
		call("mkdir -p ~/rpmbuild/SOURCES", shell=True)
		# generate tarball
		cmd = "git archive --prefix=kubernetes-%s/ --format tar %s | gzip -9 > ~/rpmbuild/SOURCES/kubernetes-%s.tar.gz" % (vars["commit"], vars["commit"], vars["commit"][:7])
		if call(cmd, shell=True):
			break

		# generate spec file
		spec = renderTemplate(
			script_dir,
			"kubernetes.spec.j2",
			vars
		)

		with file("kubernetes.spec", "w") as f:
			f.write(spec)

		# get go-bindata tarball
		if call("wget https://github.com/jteeuwen/go-bindata/archive/a0ff2567cfb70903282db057e799fd826784d41d/go-bindata-a0ff256.tar.gz -O ~/rpmbuild/SOURCES/go-bindata-a0ff256.tar.gz", shell=True):
			break

		# get contrib tarball
		if call("wget https://github.com/kubernetes/contrib/archive/1159b3d1823538f121a07c450fc5d93057226ffa/contrib-1159b3d.tar.gz -O ~/rpmbuild/SOURCES/contrib-1159b3d.tar.gz", shell=True):
			break

		# generate srpm
		so, se, rc = runCommand("rpmbuild -bs kubernetes.spec")
		if rc > 0:
			logging.error(se)
			break

		# ('Wrote: /home/jchaloup/rpmbuild/SRPMS/kubernetes-1.4.0-0.1.alpha2.gitff42c1f.fc20.src.rpm\n', '', 0)
		srpm = so.strip().split("Wrote: ")[1]

		# generate scratch-build
		if target_os == "Fedora":
			cmd = "koji build --scratch %s %s | tee scratch-build.log" % (build_target, srpm)
		else: #if target_os == "RHEL":
			cmd = "brew build --scratch %s %s | tee scratch-build.log" % (build_target, srpm)
		
		if call(cmd, shell=True):
			break

		# get scratch build link
		so, se, rc = runCommand("cat scratch-build.log | grep \"^Created task:\" | cut -d' ' -f3")
		if rc > 0:
			logging.error(se)
			break

		scratch_build_id = so.split("\n")[0]
		break

	shutil.rmtree(dirpath)
	os.chdir(cur_dir)

	return scratch_build_id

def parse_task_info(info):
	lines = info.split("\n")
	index = 0
	line_size = len(lines)
	
	data = {}
	key = ""
	# parse build data
	while index < line_size:
		line = lines[index]
		index = index + 1
	
		if line == "":
			break
	
		parts = line.split(": ")
		key = parts[0]
		data[key] = parts[1]
	
	data["archs"] = []
	
	# parse arch builds
	while index < line_size:	
		archs = {}
		while index < line_size:
			line = lines[index][2:]
			index = index + 1
		
			if line == "":
				break
		
			parts = line.split(": ")
			if parts[0][0] != " ":
				key = parts[0].replace(":", "")
		
			if key not in archs:
				if len(parts) < 2:
					archs[key] = []
				else:
					archs[key] = parts[1]
			else:
				if type(archs[key]) == type(""):
					archs[key] = [archs[key]]
				archs[key].append(parts[0].strip())

		if archs:
			data["archs"].append(archs)
	
	return data

if __name__ == "__main__":

	cur_dir = getScriptDir(__file__)
	gen_flags = "%s/build.yml" % (cur_dir)

	parser = CmdSignatureParser([gen_flags]).generate().parse()
	if not parser.check():
		exit(1)

	options = parser.options()
	args = parser.args()

	scratch_build_id = run(options.commit, options.os, options.buildtarget)

	if scratch_build_id == -1:
		logging.error("Unable to retrieve scratch build ID")
		exit(1)

	if options.os == "Fedora":
		cmd = "koji taskinfo -r %s" % scratch_build_id
	else:
		cmd = "brew taskinfo -r %s" % scratch_build_id

	# parse task info
	so, se, rc = runCommand(cmd)
	if rc > 0:
		logging.error("Unable to get task info for scratch build %s: %s" % (scratch_build_id, se))
		exit(1)

	info = parse_task_info(so)

	with open("build.json", "w") as f:
		json.dump({
				"os": options.os,
				"commit": options.commit,
				"repository": "github.com/kubernetes/kubernetes",
				"scratch_build_id": scratch_build_id,
				"taskinfo": info
			},
			f
		)
