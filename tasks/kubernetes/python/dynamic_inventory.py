#!/bin/python

import json
import os

try:
	RESOURCE_FILE = os.environ["RESOURCE_FILE"]
except KeyError:
	print "RESOURCE_FILE env not set"
	exit(1)

with open(RESOURCE_FILE, "r") as f:
	resources = json.load(f)

inventory = {}

for host in resources["resources"]:
	# host ips
	if "ip" not in host:
		print "Host '%s' is missing 'ip' field" % json.dumps(host)
		exit(1)

	inventory[host["name"]] = {"hosts": [host["ip"]], "vars": {}}

	# ansible fields
	if "metadata" not in host:
		print "Missing ansible 'metadata' field"
		exit(1)

	for key, val in host["metadata"].iteritems():
		if "ansible-group" not in key:
			continue

		for group in val:
			if group not in inventory:
				inventory[group] = {"hosts": [host["ip"]], "vars": {}}
			else:
				inventory[group]["hosts"].append(host["ip"])

			for key, val in host["metadata"].iteritems():
				inventory[group]["vars"][key] = val

print json.dumps(inventory)
