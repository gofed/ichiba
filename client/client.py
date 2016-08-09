#!/bin/python3

# Parse command and generate corresponding signature for it.
# Supported signatures:
# - docker signature (constructured locally)
# - kubernetes signature (constructured remotelly)
# - Jenkins signature (??)
# - Vagrant signature (??)

# 1. get input (command) signature
# 2. generate output signature (docker or kubernetes atm)
# 3. if docker
#    - run the docker command
# 4. if kubernetes
#    - create the kubernetes job
#    - keep fetching pod jobs
#    - post link with generated resources

# Expected form of command
# ichiba [OPTIONS] command [ARGUMENTS]
# E.g.
# ichiba -v gofed repo2spec --detect github.com/golang/sys
# ichiba --provider docker gofed repo2spec --detect github.com/golang/sys
# ichiba --provider kubernetes gofed repo2spec --detect github.com/golang/sys
#
# To get a help for each tasks (or its command), use:
# ichiba gofed -h
# ichiba gofed repo2spec -h
#

import argparse
import os
import yaml
import sys
from cmdsignatureinterpreter import cmdSignatureInterpreter
import pykube
import logging
import time

def getScriptDir(file = __file__):
	return os.path.dirname(os.path.realpath(file))

# TODO(jchaloup): make the task directory configurable
tasks_dir = "%s/../tasks" % getScriptDir(__file__)
kubeconfig = "%s/kubeconfig" % getScriptDir(__file__)

def getOptionParser():

	parser = argparse.ArgumentParser()

	parser.add_argument(
		"-v",
		"--verbose",
		dest="verbose",
		action="store_true",
		default=False
	)
	parser.add_argument(
		"-p",
		"--provider",
		dest="provider",
		action="store",
		choices=["docker", "kubernetes"],
		default="docker",
		help="What provider to use: kubernetes, docker. Defaults to docker."
	)
	parser.add_argument(
		"--host",
		dest="hostname",
		action="store",
		default=""
	)
	parser.add_argument(
		"--server",
		dest="servername",
		action="store",
		default=""
	)

	parser.add_argument(
		"--async",
		dest="async",
		action="store_true",
		default=False
	)

	subparsers = parser.add_subparsers(help='commands', dest="task_name")

	for task in os.listdir(tasks_dir):
		task_parser = subparsers.add_parser(task, help="Run %s command" % task)
		main_file = "%s/%s/main.yml" % (tasks_dir, task)
		data = yaml.load(open(main_file, 'r'))
		if "commands" not in data:
			continue

		commands_parser = task_parser.add_subparsers()

		for command in data["commands"]:
			description = ""
			for file in command["flags"]:
				flags_file = "%s/%s/cmd/%s" % (tasks_dir, task, file)
				cmd_data = yaml.load(open(flags_file, 'r'))
				if "description" in cmd_data:
					description = cmd_data["description"]

			command_parser = commands_parser.add_parser(command["name"], add_help=False)
			command_parser.set_defaults(command=command["name"])

	return parser

def getSignatureInterpreter(results):

	results, unknown = parser.parse_known_args()

	main_file = "%s/%s/main.yml" % (tasks_dir, results.task_name)
	data = yaml.load(open(main_file, 'r'))
	for command in data["commands"]:
		if command["name"] == results.command:
			interpreter = cmdSignatureInterpreter(
				map(lambda l: "%s/%s/cmd/%s" % (tasks_dir, results.task_name, l), command["flags"]),
				command = results.command
			)

			return interpreter

	raise SignatureException("Command '%s' not found" % results.command)

def waitForJob(job_name, server, kube_api):

	wait_for_job_to_appear = 0
	start_time = time.time()
	while True:
		jobs = pykube.Job.objects(kube_api).filter(namespace="default", selector={"job-name": job_name})

		print("\rWaiting... %ss" % (int(time.time() - start_time)), end="")
		time.sleep(3)

		# As there are no two jobs with the same name, len(jobs) \in {0,1}
		if len(jobs) < 1:
			wait_for_job_to_appear = wait_for_job_to_appear + 1
			if wait_for_job_to_appear > 5:
				logging.error("Job '%s' not found" % job_name)
				exit(1)
			continue

		job_obj = None
		for job in jobs:
			job_obj = job
			break

		if "status" not in job_obj.obj:
			continue

		if "succeeded" not in job_obj.obj["status"]:
			continue

		if job_obj.obj["status"]["succeeded"] == 1:
			break


	print("\nJob at http://%s/pub/ichiba/%s" % (server, job_name))

if __name__ == "__main__":

	parser = getOptionParser()
	results, unknown = parser.parse_known_args()
	interpreter = getSignatureInterpreter(results)
	if "-h" in unknown or "--help" in unknown:
		interpreter.printHelp()
		exit(0)

	# original args would be [results.task_name, results.command] + unknown
	interpreter.interpret(unknown)
	if results.provider == "docker":
		print(interpreter.dockerSignature())
	elif results.provider == "kubernetes":
		config = {}
		if results.hostname != "":
			config["hostname"] = results.hostname
		if results.servername != "":
			config["servername"] = results.servername
		config["target"] = "/var/www/html/pub/ichiba"

		job_spec = interpreter.kubeSignature(config)

		kube_api = pykube.HTTPClient(pykube.KubeConfig.from_file(kubeconfig))
		try:
			pykube.Job(kube_api, job_spec).create()
			print("Job %s created" % job_spec["metadata"]["name"])
		except Exception as e:
			logging.error("Job not created: %s" % s)

		# Wait for the job to finish
		if not results.async:
			waitForJob(job_spec["metadata"]["name"], results.servername, kube_api)
