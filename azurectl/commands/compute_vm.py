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
"""
Virtual machines are created in a private IP address space, and attached to a
'cloud service' that acts as firewall, reverse proxy, and load balancer.

usage: azurectl compute vm -h | --help
       azurectl compute vm create --cloud-service-name=<name> --image-name=<image>
           [--custom-data=<string-or-file>]
           [--instance-name=<name>]
           [--instance-type=<type>]
           [--label=<label>]
           [--reserved-ip-name=<reserved-ip-name>]
           [--password=<password>]
           [--ssh-private-key-file=<file> | --fingerprint=<thumbprint>]
           [--ssh-port=<port>]
           [--user=<user>]
           [--wait]
       azurectl compute vm reboot --cloud-service-name=<name>
           [--instance-name=<name>]
           [--wait]
       azurectl compute vm regions
       azurectl compute vm show --cloud-service-name=<name>
       azurectl compute vm types
       azurectl compute vm delete --cloud-service-name=<name>
           [--instance-name=<name>]
           [--wait]
       azurectl compute vm help

commands:
    create
        create a virtual machine instance from an image
    delete
        delete a virtual machine instance. If no instance name is
        specified, the cloud service and all its associated instances
        will be deleted
    help
        show manual page for image command
    reboot
        reboot virtual machine instance
    regions
        list regions where a virtual machine can be created with the current
        subscription
    show
        Retrieves system properties for the specified cloud service
        and the virtual machine instances it contains
    types
        list available virtual machine types

options:
    --cloud-service-name=<name>
        name of the cloud service to put the virtual machine in.
        if the cloud service does not exist it will be created
    --custom-data=<string-or-file>
        a string of data or path to a file that will be injected into the new
        virtual machine
    --fingerprint=<thumbprint>
        thumbprint of an already existing certificate in the
        cloud service used for ssh public key authentication
    --image-name=<image>
        name of the VHD disk image to create the virtual machine
        instance from
    --instance-name=<name>
        name of the virtual machine instance. if no name is
        given the instance name is the same as the cloud service
        name.
    --instance-type=<type>
        virtual machine type, by default set to: Small
    --label=<label>
        custom label name for the virtual machine instance
    --password=<password>
        plain text password for the user to login. If no password is specified
        SSH password based login will be disabled
    --reserved-ip-name=<reserved-ip-name>
        name of a reserved IP address to apply as a public IP of this cloud
        service and the public IP of this instance.
    --ssh-port=<port>
        external SSH port
    --ssh-private-key-file=<file>
        path to ssh private key, from which a new PEM certificate
        will be created and added to the cloud service in order to
        allow ssh public key authentication
    --user=<user>
        user name for login, by default set to: azureuser
    --wait
        wait for the request to succeed
"""
import os
# project
from base import CliTask
from ..account.service import AzureAccount
from ..utils.collector import DataCollector
from ..utils.output import DataOutput
from ..instance.virtual_machine import VirtualMachine
from ..instance.cloud_service import CloudService
from ..help import Help


class ComputeVmTask(CliTask):
    """
        Process vm commands
    """
    SSH_DEFAULT_PORT = 22

    def process(self):
        self.manual = Help()
        if self.__help():
            return

        self.result = DataCollector()
        self.out = DataOutput(
            self.result,
            self.global_args['--output-format'],
            self.global_args['--output-style']
        )

        self.load_config()

        self.account = AzureAccount(self.config)

        if self.command_args['types']:
            self.__list_instance_types()
        elif self.command_args['regions']:
            self.__list_locations()
        elif self.command_args['show']:
            self.cloud_service = CloudService(self.account)
            self.__show_cloud_service_properties()
        else:
            self.vm = VirtualMachine(self.account)
            self.cloud_service = CloudService(self.account)
            if self.command_args['create']:
                self.__create_cloud_service()
                self.__create_instance()
            elif self.command_args['delete']:
                if self.command_args['--instance-name']:
                    self.__delete_instance()
                else:
                    self.__delete_cloud_service()
            elif self.command_args['reboot']:
                self.__reboot_instance()

    def __help(self):
        if self.command_args['help']:
            self.manual.show('azurectl::compute::vm')
        else:
            return False
        return self.manual

    def __list_instance_types(self):
        self.result.add('instance-types', self.account.instance_types())
        self.out.display()

    def __list_locations(self):
        self.result.add('regions', self.account.locations('PersistentVMRole'))
        self.out.display()

    def __show_cloud_service_properties(self):
        properties = self.cloud_service.get_properties(
            self.command_args['--cloud-service-name']
        )
        self.result.add(
            'cloud_service:' + self.command_args['--cloud-service-name'],
            properties
        )
        self.out.display()

    def __create_instance(self):
        instance_type = self.command_args['--instance-type']
        if not instance_type:
            instance_type = 'Small'
        fingerprint = u''
        if self.command_args['--ssh-private-key-file']:
            fingerprint = self.cloud_service.add_certificate(
                self.command_args['--cloud-service-name'],
                self.command_args['--ssh-private-key-file']
            )
        elif self.command_args['--fingerprint']:
            fingerprint = self.command_args['--fingerprint']
        linux_configuration = self.__prepare_linux_configuration(fingerprint)
        network_configuration = self.__prepare_network()
        request_id = self.vm.create_instance(
            self.command_args['--cloud-service-name'],
            self.command_args['--image-name'],
            linux_configuration,
            network_config=network_configuration,
            label=self.command_args['--label'],
            machine_size=instance_type,
            reserved_ip_name=self.command_args['--reserved-ip-name']
        )
        if self.command_args['--wait']:
            # we might want to change this to wait until the VM becomes
            # accessible to the user
            self.request_wait(request_id)
        self.result.add(
            'instance',
            request_id
        )
        self.out.display()

    def __create_cloud_service(self):
        cloud_service_request_id = self.cloud_service.create(
            self.command_args['--cloud-service-name'],
            self.config.get_region_name()
        )
        if cloud_service_request_id > 0:
            # a new cloud service was created for this instance, waiting
            # for the cloud service to become created. Basically we try
            # to prevent blocking, thus this is an exception to other
            # requests
            self.request_wait(cloud_service_request_id)

    def __delete_cloud_service(self):
        cloud_service = self.command_args['--cloud-service-name']
        complete_deletion = True
        request_id = self.cloud_service.delete(
            cloud_service, complete_deletion
        )
        if self.command_args['--wait']:
            self.request_wait(request_id)
        self.result.add(
            'cloud_service:' + cloud_service,
            request_id
        )
        self.out.display()

    def __delete_instance(self):
        instance_name = self.command_args['--instance-name']
        request_id = self.vm.delete_instance(
            self.command_args['--cloud-service-name'],
            instance_name
        )
        if self.command_args['--wait']:
            self.request_wait(request_id)
        self.result.add(
            'instance:' + instance_name,
            request_id
        )
        self.out.display()

    def __reboot_instance(self):
        instance_name = self.command_args['--instance-name']
        if not instance_name:
            instance_name = self.command_args['--cloud-service-name']
        request_id = self.vm.reboot_instance(
            self.command_args['--cloud-service-name'],
            instance_name
        )
        if self.command_args['--wait']:
            self.request_wait(request_id)
        self.result.add(
            'reboot:' + instance_name,
            request_id
        )
        self.out.display()

    def __prepare_linux_configuration(self, fingerprint=u''):
        user = self.command_args['--user']
        instance_name = self.command_args['--instance-name']
        password = self.command_args['--password']

        custom_data = self.command_args['--custom-data']
        if (custom_data and os.path.isfile(custom_data)):
            with open(custom_data, 'r') as file:
                custom_data = file.read()

        disable_ssh_password_authentication = False
        if not user:
            # no user specified, use the default Azure user name
            user = 'azureuser'
        if not instance_name:
            # no instance name specified, use the cloud service name
            instance_name = self.command_args['--cloud-service-name']
        if not password:
            # no password set, disable ssh user authentication
            disable_ssh_password_authentication = True
        return self.vm.create_linux_configuration(
            user,
            instance_name,
            disable_ssh_password_authentication,
            password,
            custom_data,
            fingerprint
        )

    def __prepare_network(self):
        ssh_endpoint = self.__prepare_ssh()
        return self.vm.create_network_configuration(
            [ssh_endpoint]
        )

    def __prepare_ssh(self, ssh_local_port=SSH_DEFAULT_PORT):
        ssh_public_port = self.command_args['--ssh-port']
        if not ssh_public_port:
            # no ssh public port specified, use local port as default
            ssh_public_port = ssh_local_port
        return self.vm.create_network_endpoint(
            'SSH', ssh_public_port, ssh_local_port, 'TCP'
        )
