import sys
import mock
from mock import patch


from test_helper import *

import azurectl
from azurectl.commands.compute_image import ComputeImageTask


class TestComputeImageTask:
    def setup(self):
        sys.argv = [
            sys.argv[0], '--config', '../data/config',
            'compute', 'image', 'list'
        ]
        self.task = ComputeImageTask()
        self.image = mock.Mock()
        azurectl.commands.compute_image.Image = mock.Mock(return_value = self.image)
        azurectl.commands.compute_image.Help = mock.Mock(
            return_value=mock.Mock()
        )

    def __init_command_args(self):
        self.task.command_args = {}
        self.task.command_args['--color'] = False
        self.task.command_args['list'] = False
        self.task.command_args['help'] = False
        self.task.command_args['create'] = False
        self.task.command_args['delete'] = False
        self.task.command_args['replicate'] = False
        self.task.command_args['replication-status'] = False
        self.task.command_args['unreplicate'] = False
        self.task.command_args['publish'] = False
        self.task.command_args['update'] = False
        self.task.command_args['show'] = False
        self.task.command_args['--offer'] = 'offer'
        self.task.command_args['--regions'] = 'a,b,c'
        self.task.command_args['--sku'] = 'sku'
        self.task.command_args['--wait'] = False
        self.task.command_args['--quiet'] = False
        self.task.command_args['--private'] = False
        self.task.command_args['--msdn'] = False
        self.task.command_args['--image-version'] = '1.0.0'
        self.task.command_args['--delete-disk'] = False
        self.task.command_args['--label'] = 'label'
        self.task.command_args['--name'] = 'some-image'
        self.task.command_args['--blob'] = 'some-blob'
        self.task.command_args['--description'] = 'description'
        self.task.command_args['--eula'] = 'eula'
        self.task.command_args['--image-family'] = 'family'
        self.task.command_args['--icon-uri'] = 'uri'
        self.task.command_args['--label'] = 'label'
        self.task.command_args['--language'] = 'en_US'
        self.task.command_args['--privacy-uri'] = 'uri'
        self.task.command_args['--published-date'] = 'date'
        self.task.command_args['--small-icon-uri'] = 'uri'

    @patch('azurectl.commands.compute_image.DataOutput')
    def test_process_compute_image_list(self, mock_out):
        self.__init_command_args()
        self.task.command_args['list'] = True
        self.task.process()
        self.task.image.list.assert_called_once_with()

    @patch('azurectl.commands.compute_image.DataOutput')
    def test_process_compute_image_show(self, mock_out):
        self.__init_command_args()
        self.task.command_args['show'] = True
        self.task.process()
        self.task.image.show.assert_called_once_with(
            self.task.command_args['--name']
        )

    @patch('azurectl.commands.compute_image.DataOutput')
    def test_process_compute_image_delete(self, mock_out):
        self.__init_command_args()
        self.task.command_args['delete'] = True
        self.task.process()
        self.task.image.delete.assert_called_once_with(
            self.task.command_args['--name'],
            self.task.command_args['--delete-disk']
        )

    @patch('azurectl.commands.compute_image.DataOutput')
    def test_process_compute_image_create(self, mock_out):
        self.__init_command_args()
        self.task.command_args['create'] = True
        self.task.process()
        self.task.image.create.assert_called_once_with(
            self.task.command_args['--name'],
            self.task.command_args['--blob'],
            self.task.command_args['--label'],
            self.task.account.storage_container()
        )

    def test_process_compute_image_help(self):
        self.__init_command_args()
        self.task.command_args['help'] = True
        self.task.process()
        self.task.manual.show.assert_called_once_with(
            'azurectl::compute::image'
        )

    @patch('azurectl.commands.compute_image.DataOutput')
    def test_process_compute_image_replicate(self, mock_out):
        self.__init_command_args()
        self.task.command_args['replicate'] = True
        self.task.process()
        self.task.image.replicate.assert_called_once_with(
            self.task.command_args['--name'],
            self.task.command_args['--regions'].split(','),
            self.task.command_args['--offer'],
            self.task.command_args['--sku'],
            self.task.command_args['--image-version']
        )

    @patch('azurectl.commands.compute_image.BackgroundScheduler')
    @patch('azurectl.commands.compute_image.DataOutput')
    def test_process_compute_image_replicate_wait(self, mock_out, mock_bg):
        # given
        self.__init_command_args()
        self.task.command_args['replicate'] = True
        self.task.command_args['--wait'] = True
        # when
        self.task.process()
        # then
        self.task.image.replicate.assert_called_once_with(
            self.task.command_args['--name'],
            self.task.command_args['--regions'].split(','),
            self.task.command_args['--offer'],
            self.task.command_args['--sku'],
            self.task.command_args['--image-version']
        )
        self.task.image.wait_for_replication_completion.assert_called_once_with(
            self.task.command_args['--name']
        )

    @patch('azurectl.commands.compute_image.BackgroundScheduler')
    @patch('azurectl.commands.compute_image.DataOutput')
    # then
    @raises(SystemExit)
    def test_process_compute_image_replicate_wait_interrupted(
            self,
            mock_out,
            mock_job
                                                              ):
        # given
        self.__init_command_args()
        self.task.command_args['replicate'] = True
        self.task.command_args['--wait'] = True
        self.image.wait_for_replication_completion.side_effect = \
            KeyboardInterrupt
        # when
        self.task.process()

    @patch('azurectl.commands.compute_image.DataOutput')
    def test_process_compute_image_replication_status(self, mock_out):
        self.__init_command_args()
        self.task.command_args['replication-status'] = True
        self.task.process()
        self.task.image.replication_status.assert_called_once_with(
            self.task.command_args['--name']
        )

    @patch('azurectl.commands.compute_image.DataOutput')
    def test_process_compute_image_unreplicate(self, mock_out):
        self.__init_command_args()
        self.task.command_args['unreplicate'] = True
        self.task.process()
        self.task.image.unreplicate.assert_called_once_with(
            self.task.command_args['--name']
        )

    @patch('azurectl.commands.compute_image.DataOutput')
    def test_process_compute_image_publish_public(self, mock_out):
        self.__init_command_args()
        self.task.command_args['publish'] = True
        self.task.process()
        self.task.image.publish.assert_called_once_with(
            self.task.command_args['--name'], 'public'
        )

    @patch('azurectl.commands.compute_image.DataOutput')
    def test_process_compute_image_publish_private(self, mock_out):
        self.__init_command_args()
        self.task.command_args['publish'] = True
        self.task.command_args['--private'] = True
        self.task.process()
        self.task.image.publish.assert_called_once_with(
            self.task.command_args['--name'], 'private'
        )

    @patch('azurectl.commands.compute_image.DataOutput')
    def test_process_compute_image_publish_msdn(self, mock_out):
        self.__init_command_args()
        self.task.command_args['publish'] = True
        self.task.command_args['--msdn'] = True
        self.task.process()
        self.task.image.publish.assert_called_once_with(
            self.task.command_args['--name'], 'msdn'
        )

    def test_process_compute_image_update(self):
        self.__init_command_args()
        self.task.command_args['update'] = True
        self.task.process()
        self.task.image.update.assert_called_once_with(
            'some-image', {
                'eula': 'eula',
                'description': 'description',
                'language': 'en_US',
                'image_family': 'family',
                'icon_uri': 'uri',
                'label': 'label',
                'small_icon_uri': 'uri',
                'published_date': 'date',
                'privacy_uri': 'uri'
            }
        )