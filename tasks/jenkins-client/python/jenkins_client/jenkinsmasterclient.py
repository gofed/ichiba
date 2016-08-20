import requests
import logging
import uuid
import time
import urllib2

class JenkinsMasterClient(object):

	def __init__(self, master, job, params={}):
		self._job = job
		self._jenkins_master = master
		self._params = params

	def run(self, artefact_dest, resources):
		# 1. start a Jenkins Job (with a unique hash)
		print "Triggering Jenkins Job"
		ok, uuid = self._triggerJenkinsJob()
		
		# 2. get a list of all jobs and find the currently triggered job
		print "Waiting for job to start"
		counter = 0
		while counter < 10:
			try:
				build = self._getJenkinsJobID(uuid)
				break
			except KeyError:
				pass
		
			counter = counter + 1
			time.sleep(1)
		
		if counter >= 10:
			logging.error("Timeout waiting for build to start")
			return False

		# 3. ask the server each second (or two) if a job is done
		print "Waiting for job to finish"
		self._waitForBuild(build)

		# 4. get a resource file with a cluster
		print "Retrieving artifacts"
		self._getArtifacts(build, artefact_dest, resources)

	def _triggerJenkinsJob(self):
		job_uuid = str(uuid.uuid4())

		url = "%s/job/%s/buildWithParameters" % (self._jenkins_master, self._job)
		url = url + "?uuid=" + job_uuid
		if self._params != []:
			url = url + "&" + "&".join(map(lambda l: "%s=%s" % (l, self._params[l]), self._params))

		r = requests.post(url)

		if r.status_code != requests.codes.created:
			logging.error("Failed to create pull request comment [HTTP %d]" % r.status_code)
			logging.error(r.headers)
			logging.error(r.json())
			return False, -1

		return True, job_uuid
	
	def _getJenkinsJobID(self, uuid):
		url = "%s/job/%s/api/json" % (self._jenkins_master, self._job)
		r = requests.get(url)
		if r.status_code != requests.codes.ok:
			logging.error("Failed to create pull request comment [HTTP %d]" % r.status_code)
			logging.error(r.headers)
			logging.error(r.json())
			raise KeyError("Job with '%s' uuid not found" % uuid)

		for build in r.json()["builds"]:
			url = "%s/api/json" % build["url"]
			#print build
			sr = requests.get(url)
			if sr.status_code != requests.codes.ok:
				continue

			parameters = []
			for action in sr.json()["actions"]:
				if "parameters" in action:
					parameters = action["parameters"]
					break

			if parameters == []:
				continue

			for param in parameters:
				if param["name"] == "uuid" and param["value"] == uuid:
					return build

		raise KeyError("Job with '%s' uuid not found" % uuid)

	def _waitForBuild(self, build):
		building = True
		while building:
			url = "%s/api/json" % build["url"]
			r = requests.get(url)
			if r.status_code != requests.codes.ok:
				logging.error("Failed to create pull request comment [HTTP %d]" % r.status_code)
				logging.error(r.headers)
				logging.error(r.json())
				raise KeyError("Build %s not found" % build["url"])

			building = r.json()["building"]
			time.sleep(1)

	def _getResource(self, resource_url, target):
		response = urllib2.urlopen(resource_url)
		with open(target, "w") as f:
			f.write(response.read())
			f.flush()

	def _getArtifacts(self, build, artefact_dest, resources):
		dest = "./"
		if artefact_dest != "":
			dest = "%s/" % artefact_dest

		for resource in resources:
			self._getResource("%s/artifact/%s" % (build["url"], resource), "%s/%s" % (dest, resource))

