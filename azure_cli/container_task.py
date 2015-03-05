"""
usage: azure-cli container list

commands:
    list     list available containers
"""

# project
from cli_task import CliTask
from storage_account import StorageAccount
from data_collector import DataCollector
from logger import Logger
from exceptions import *
from container import Container

class ContainerTask(CliTask):
    def process(self):
        self.account = StorageAccount(self.account_name, self.config_file)
        self.container = Container(self.account)
        if self.command_args['list']:
            self.__list()
        elif self.command_args['content']:
            self.__content()
        else:
            raise AzureUnknownContainerCommand(self.command_args)

    def __list(self):
        result = DataCollector()
        result.add(
            'containers:' + self.account.get_name(),
            self.container.list()
        )
        Logger.info(result.get())
