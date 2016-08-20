from .jenkinsmasterclient import JenkinsMasterClient

class ProvisionCluster(object):

	def __init__(self, master, params):
		self._client = JenkinsMasterClient(master, "provision-cluster-1-provision", params)

	def run(self, artefact_dest):
		self._client.run(artefact_dest, resources=["resources.json", "RESOURCES.txt"])

