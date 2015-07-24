# Copyright (c) 2015 SUSE Linux GmbH.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from tempfile import NamedTemporaryFile
from azure.servicemanagement import ServiceManagementService
from azure.servicemanagement import ConfigurationSetInputEndpoint
from azure.servicemanagement import ConfigurationSet
from azure.servicemanagement import PublicKey
from azure.servicemanagement import LinuxConfigurationSet
from azure.servicemanagement import OSVirtualHardDisk
from azure.storage.blob import BlobService

# project
from azurectl_exceptions import (
    AzureVmCreateError,
    AzureVmDeleteError
)


class VirtualMachine(object):
    """
        Implements creation/deletion and management of virtual
        machine instances from a given image name
    """
    def __init__(self, account):
        self.account = account
        self.container_name = account.storage_container()
        self.account_name = account.storage_name()
        self.account_key = account.storage_key()
        self.cert_file = NamedTemporaryFile()
        self.publishsettings = self.account.publishsettings()
        self.cert_file.write(self.publishsettings.private_key)
        self.cert_file.write(self.publishsettings.certificate)
        self.cert_file.flush()

        self.service = ServiceManagementService(
            self.publishsettings.subscription_id,
            self.cert_file.name
        )

        self.storage = BlobService(
            self.account_name, self.account_key
        )

    def create_linux_configuration(
        self, username='azureuser', instance_name=None,
        disable_ssh_password_authentication=True,
        password=None, custom_data=None, fingerprint=u''
    ):
        """
            create a linux configuration
        """
        # The given instance name is used as the host name in linux
        linux_config = LinuxConfigurationSet(
            instance_name, username, password,
            disable_ssh_password_authentication,
            custom_data
        )
        if fingerprint:
            ssh_key_file = '/home/' + username + '/.ssh/authorized_keys'
            ssh_pub_key = PublicKey(
                fingerprint, ssh_key_file
            )
            linux_config.ssh.public_keys = [ssh_pub_key]
        return linux_config

    def create_network_configuration(self, network_endpoints):
        """
            create a network configuration
        """
        network_config = ConfigurationSet()
        for endpoint in network_endpoints:
            network_config.input_endpoints.input_endpoints.append(endpoint)
        network_config.configuration_set_type = 'NetworkConfiguration'
        return network_config

    def create_network_endpoint(
        self, name, public_port, local_port, protocol
    ):
        """
            create a network service endpoint
        """
        return ConfigurationSetInputEndpoint(
            name, protocol, public_port, local_port
        )

    def create_instance(
        self, cloud_service_name, location, disk_name, system_config,
        network_config=None, label=None, group='production',
        machine_size='Small'
    ):
        """
            create a virtual disk image instance
        """
        media_link = self.storage.make_blob_url(
            self.container_name, disk_name + '_instance'
        )
        instance_disk = OSVirtualHardDisk(disk_name, media_link)
        instance_record = {
            'deployment_name': cloud_service_name,
            'deployment_slot': group,
            'label': cloud_service_name,
            'network_config': network_config,
            'role_name': cloud_service_name,
            'role_size': machine_size,
            'service_name': cloud_service_name,
            'system_config': system_config,
            'os_virtual_hard_disk': instance_disk,
            'provision_guest_agent': True,
            'media_location': location
        }
        if label:
            instance_record['label'] = label
        if network_config:
            instance_record['network_config'] = network_config

        try:
            result = self.service.create_virtual_machine_deployment(
                **instance_record
            )
            return {
                'request_id': format(result.request_id),
                'cloud_service_name': cloud_service_name,
                'instance_name': system_config.host_name
            }
        except Exception as e:
            raise AzureVmCreateError(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def delete_instance(
        self, cloud_service_name, instance_name
    ):
        """
            delete a virtual disk image instance
        """
        try:
            result = self.service.delete_deployment(
                cloud_service_name, instance_name
            )
            return(format(result.request_id))
        except Exception as e:
            raise AzureVmDeleteError(
                '%s: %s' % (type(e).__name__, format(e))
            )
