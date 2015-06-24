import datetime
import sys
import mock
from mock import patch
from nose.tools import *
from urlparse import urlparse

import nose_helper

from azurectl.azurectl_exceptions import *
from azurectl.fileshare import FileShare

import azurectl

from collections import namedtuple

MOCK_STORAGE_NAME = 'mock-storage'


class TestFileShare:
    def setup(self):
        name = namedtuple("name", "name")
        self.name_list = [name(name="a"), name(name="b")]
        account = mock.Mock()
        credentials = namedtuple(
            'credentials',
            ['private_key', 'certificate', 'subscription_id']
        )
        account.storage_name = mock.Mock(return_value=MOCK_STORAGE_NAME)
        account.storage_key = mock.Mock(
            return_value='fI8bhf6QAvgwCgR9qJyoNLHQ9F73fQ97e3/e8jMCFSiFioaB' +
            'iAU0oSGcFACtniSY6pS3L5GKNzPCK0FF6M+O4A=='
        )
        account.publishsettings = mock.Mock(
            return_value=credentials(
                private_key='abc',
                certificate='abc',
                subscription_id='4711'
            )
        )
        self.files = FileShare(account)

    @patch('azurectl.fileshare.FilesService.list_shares')
    def test_list(self, mock_list_shares):
        mock_list_shares.return_value = self.name_list
        assert self.files.list() == ['a', 'b']

    @patch('azurectl.fileshare.FilesService.create_share')
    def test_create(self, mock_create_shares):
        self.files.create('foo')
        mock_create_shares.assert_called_once_with('foo')

    @patch('azurectl.fileshare.FilesService.delete_share')
    def test_delete(self, mock_delete_shares):
        self.files.delete('foo')
        mock_delete_shares.assert_called_once_with('foo')

    @raises(AzureFileShareCreateError)
    def test_raise_create_failed(self):
        self.files.create('foo')

    @raises(AzureFileShareListError)
    def test_raise_list_failed(self):
        self.files.list()

    @raises(AzureFileShareDeleteError)
    def test_raise_delete_failed(self):
        self.files.delete('foo')
