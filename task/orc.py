import requests
import json

from django.conf import settings

class Orc:
    def __init__(self):
        self.base_url = settings.ORC_BASE_URL
        self.username = settings.ORC_USERNAME
        self.password = settings.ORC_PASSWORD

        self.auth_form = {
            "username": self.username,
            "password": self.password
        }

    def jwt_token(self):
        # Add error check and cache (renew)
        return requests.post('{}api-token-auth/'.format(self.base_url), json = self.auth_form).json()['access']

    def _query(self, uri, method, kwargs = {}):
        headers = {
            'Authorization': "JWT " + self.jwt_token(),
            'Accept': 'application/json'
        }

        if method == "GET":
            request = requests.get(self.base_url+uri, headers=headers)
        elif method == "POST":
            request = requests.post(self.base_url+uri, headers=headers, json=kwargs)
        elif method == "PUT":
            request = requests.put(self.base_url+uri, headers=headers, json=kwargs)
        elif method == "PATCH":
            request = requests.patch(self.base_url+uri, headers=headers, json=kwargs)
        elif method == "DELETE":
            request = requests.delete(self.base_url+uri, headers=headers)

        if request.headers.get('content-type') == 'application/json':
            return request.json()
        return None

    def get_vm(self, id):
        return self._query("vm/%s" % id, "GET")

    def create_vm(self, vm_name, username, password, ssh_port=22, vlan_id=None, userdata = []):
        vm = {
            "name":vm_name,
            "platform": 2,
            "network": 2,
            "vm_template": 2,
            "memory": 2,
            "cpu_cores": 1,
            "os_disk": 16
        }

        userdata = [
            "useradd -s /usr/bin/bash -m -p $(openssl passwd -1 {}) {}".format(password, username),
            "usermod -aG sudo {}".format(username),
            "sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config",
            "sed -i 's/#Port 22/Port {}/' /etc/ssh/sshd_config".format(ssh_port),
            "echo '{} ALL=(ALL) NOPASSWD: ALL' | EDITOR='tee -a' visudo".format(username),
            "systemctl restart sshd"
        ] + userdata

        if vlan_id is not None:
            vm.update({"additional_net": {
                "firewall": 0,
                "vmbridge": "vmbr1",
                "vlan_id": vlan_id
            }})

            # This is bad
            ip = "10.{}.{}.1/24".format(str(vlan_id)[:2], str(vlan_id)[-2:])
            userdata.append("touch /etc/network/interfaces.d/60-techonline")
            userdata.append("echo 'auto ens19' >> /etc/network/interfaces.d/60-techonline")
            userdata.append("echo 'iface ens19 inet static' >> /etc/network/interfaces.d/60-techonline")
            userdata.append("echo 'address {}' >> /etc/network/interfaces.d/60-techonline".format(ip))

        vm.update({"userdata": userdata})

        vm_id = self._query("vm/", "POST", vm)['id']
        vm = self.get_vm(vm_id)

        return vm

    def delete_vm(self, id):
        return self._query("vm/%s" % id, "DELETE")
