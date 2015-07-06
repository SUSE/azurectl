import sys
import mock
from mock import patch
from nose.tools import *

import nose_helper

import azurectl
from azurectl.compute_vm_task import ComputeVmTask
from azurectl.azurectl_exceptions import *


class TestComputeVmTask:
    def setup(self):
        sys.argv = [
            sys.argv[0], '--config', '../data/config',
            'compute', 'vm', 'delete', '--cloud-service-name', 'cloudservice',
            '--instance-name', 'foo'
        ]
        self.task = ComputeVmTask()
        vm = mock.Mock()
        vm.create_network_configuration = mock.Mock(
            return_value={}
        )
        vm.create_linux_configuration = mock.Mock(
            return_value={}
        )
        azurectl.compute_vm_task.VirtualMachine = mock.Mock(
            return_value=vm
        )
        cloud_service = mock.Mock()
        cloud_service.create = mock.Mock(
            return_value=42
        )
        azurectl.compute_vm_task.CloudService = mock.Mock(
            return_value=cloud_service
        )
        azurectl.compute_vm_task.Help = mock.Mock(
            return_value=mock.Mock()
        )

    def __init_command_args(self):
        self.task.command_args = {}
        self.task.command_args['--cloud-service-name'] = 'cloudservice'
        self.task.command_args['--region'] = 'somewhere'
        self.task.command_args['--image-name'] = 'image'
        self.task.command_args['--instance-name'] = None
        self.task.command_args['--custom-data'] = None
        self.task.command_args['--instance-type'] = None
        self.task.command_args['--label'] = None
        self.task.command_args['--password'] = None
        self.task.command_args['--ssh-private-key-file'] = '../data/id_test'
        self.task.command_args['--fingerprint'] = None
        self.task.command_args['--ssh-port'] = None
        self.task.command_args['--user'] = None
        self.task.command_args['create'] = False
        self.task.command_args['delete'] = False
        self.task.command_args['help'] = False

    @patch('azurectl.compute_vm_task.DataOutput')
    def test_process_compute_vm_create(self, mock_out):
        self.__init_command_args()
        self.task.command_args['create'] = True
        self.task.process()
        self.task.cloud_service.create.assert_called_once_with(
            self.task.command_args['--cloud-service-name'],
            self.task.command_args['--region']
        )
        self.task.cloud_service.wait_for_request_completion.assert_called_once_with(42)
        self.task.vm.create_instance.assert_called_once_with(
            self.task.command_args['--cloud-service-name'],
            self.task.command_args['--region'],
            self.task.command_args['--image-name'],
            {},
            {},
            self.task.command_args['--label'],
            'production',
            'Small'
        )

    @patch('azurectl.compute_vm_task.DataOutput')
    def test_process_compute_vm_create_with_fingerprint(self, mock_out):
        self.task.command_args['--fingerprint'] = 'foo'
        self.task.command_args['create'] = True
        self.task.process()
        self.task.vm.create_linux_configuration.assert_called_once_with(
            'azureuser', 'foo', True, None, None, 'foo'
        )

    def test_process_compute_vm_delete(self):
        self.__init_command_args()
        self.task.command_args['delete'] = True
        self.task.command_args['--cloud-service-name'] = 'cloudservice'
        self.task.command_args['--instance-name'] = None
        self.task.process()
        self.task.cloud_service.delete.assert_called_once_with(
            self.task.command_args['--cloud-service-name'],
            True
        )
        self.task.command_args['--cloud-service-name'] = 'cloudservice'
        self.task.command_args['--instance-name'] = 'instance'
        self.task.process()
        self.task.vm.delete_instance.assert_called_once_with(
            self.task.command_args['--cloud-service-name'],
            self.task.command_args['--instance-name']
        )

    def test_process_compute_vm_help(self):
        self.__init_command_args()
        self.task.command_args['help'] = True
        self.task.process()
        self.task.manual.show.assert_called_once_with(
            'azurectl::compute::vm'
        )