# Copyright (c) SUSE Linux GmbH.  All rights reserved.
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
usage:
    azurectl -h | --help
    azurectl -v | --version
    azurectl [--config=<file>] [--account=<name>]
              <command> [<args>...]

commands:
    help       show detailed help page for given command
    storage    list information about storage accounts
    container  list information about containers for configured storage account
    disk       list, upload, delete disk images to/from a storage container
    image      list, register, deregister os images

global options:
    -h, --help
    -v, --version
    --config=<file>          config file, default is: ~/.azurectl/config
    --account=<name>         account name in config file, default is: default
"""
import importlib
from docopt import docopt

# project
from exceptions import *
from version import __VERSION__


class Cli:
    """Commandline interface"""

    def __init__(self):
        self.all_args = docopt(
            __doc__,
            version='azurectl version ' + __VERSION__,
            options_first=True
        )
        self.loaded = False
        self.command_args = self.all_args['<args>']

    def get_command(self):
        return self.all_args['<command>']

    def get_command_args(self):
        if not self.loaded:
            raise AzureCommandNotLoaded(
                '%s command not loaded' % self.get_command()
            )
        return self.__load_command_args()

    def get_global_args(self):
        result = {}
        for arg, value in self.all_args.iteritems():
            if not arg == '<command>' and not arg == '<args>':
                result[arg] = value
        return result

    def load_command(self):
        if self.loaded:
            return self.loaded
        command = self.get_command()
        if not command:
            raise AzureLoadCommandUndefined(command)
        try:
            loaded = importlib.import_module('azure_cli.' + command + '_task')
        except Exception as e:
            raise AzureUnknownCommand(command)
        self.loaded = loaded
        return self.loaded

    def __load_command_args(self):
        argv = [self.get_command()] + self.command_args
        return docopt(self.loaded.__doc__, argv=argv)
