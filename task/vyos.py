import requests
import json

from django.conf import settings

class Vyos:
    def __init__(self):
        self.base_url = settings.VYOS_BASE_URL
        self.token = settings.VYOS_TOKEN
        self.data = []

    def _query(self, uri, method, kwargs = {}):
        kwargs.update({"key": self.token})
        if method == "GET":
            request = requests.get(self.base_url+uri, verify=False)
        elif method == "POST":
            request = requests.post(self.base_url+uri, data=kwargs, verify=False)
        elif method == "PUT":
            request = requests.put(self.base_url+uri, data=kwargs, verify=False)
        elif method == "PATCH":
            request = requests.patch(self.base_url+uri, data=kwargs, verify=False)
        elif method == "DELETE":
            request = requests.delete(self.base_url+uri, verify=False)

        print(request.text)

        if request.headers.get('content-type') == 'application/json':
            return request.json()
        return None

    def set(self, path, value):
        data = {"op": "set", "path": path, "value": str(value)}
        self.data.append(data)

    def commit(self):
        print(self.data)
        self._query("configure", "POST", {"data": json.dumps(self.data)})
        # Add error check
        self.data = []

    def delete(self, path):
        data = {"op": "delete", "path": path}
        self.data.append(data)

    def get_nat_rules(self):
        data = {"op": "showConfig", "path": ["nat", "destination"]}
        return self._query("retrieve", "POST", data)

    def get_nat_rule(self, id):
        data = {"op": "showConfig", "path": ["nat", "destination", "rule", str(id)]}
        return self._query("retrieve", "POST", data)

    def create_nat_rule(self, id, destination, translation, description, interface = "eth0", protocol = "tcp"):
        value = {
            "description": description,
            "destination": destination,
            "inbound-interface": interface,
            "protocol": protocol,
            "translation": translation
        }

        self.set(["nat", "destination", "rule", str(id), "inbound-interface"], interface)
        self.set(["nat", "destination", "rule", str(id), "description"], description)
        self.set(["nat", "destination", "rule", str(id), "protocol"], protocol)

        self.set(["nat", "destination", "rule", str(id), "destination", "address"], destination['address'])
        self.set(["nat", "destination", "rule", str(id), "destination", "port"], destination['port'])

        self.set(["nat", "destination", "rule", str(id), "translation", "address"], translation['address'])
        self.set(["nat", "destination", "rule", str(id), "translation", "port"], translation['port'])

        self.commit()

    def delete_nat_rule(self, id):
        self.delete(["nat", "destination", "rule", str(id)])
        print(self.data)
        self.commit()
        return True
