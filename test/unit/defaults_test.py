from nose.tools import *
from mock import patch

import nose_helper
import mock

from azurectl.azurectl_exceptions import *
from azurectl.defaults import Defaults


class TestDefaults:
    def __set_account_type_docopts(self):
        self.account_type_docopts = {
            '--locally-redundant': False,
            '--zone-redundant': False,
            '--geo-redundant': False,
            '--read-access-geo-redundant': False
        }

    def test_get_azure_domain(self):
        assert Defaults.get_azure_domain('West US') == 'cloudapp.net'

    @raises(AzureDomainLookupError)
    def test_get_azure_domain_raises(self):
        Defaults.get_azure_domain('region-does-not-exist')

    def test_set_attribute(self):
        class X:
            def __init__(self):
                self.name = 'value'
        instance = X()
        Defaults.set_attribute(instance, 'name', 'foo')
        assert instance.name == 'foo'

    def test_get_attribute(self):
        class X:
            def __init__(self):
                self.name = 'value'
        instance = X()
        Defaults.get_attribute(instance, 'name')
        assert instance.name == 'value'

    def test_account_type_for_docopts(self):
        self.__set_account_type_docopts()
        self.account_type_docopts['--locally-redundant'] = True
        result = Defaults.account_type_for_docopts(self.account_type_docopts)
        assert result == 'Standard_LRS'

        self.__set_account_type_docopts()
        self.account_type_docopts['--zone-redundant'] = True
        result = Defaults.account_type_for_docopts(self.account_type_docopts)
        assert result == 'Standard_ZRS'

        self.__set_account_type_docopts()
        self.account_type_docopts['--geo-redundant'] = True
        result = Defaults.account_type_for_docopts(self.account_type_docopts)
        assert result == 'Standard_GRS'

        self.__set_account_type_docopts()
        self.account_type_docopts['--read-access-geo-redundant'] = True
        result = Defaults.account_type_for_docopts(self.account_type_docopts)
        assert result == 'Standard_RAGRS'

    def test_default_account_type_for_docopts(self):
        self.__set_account_type_docopts()
        result = Defaults.account_type_for_docopts(self.account_type_docopts)
        assert result == 'Standard_GRS'

    def test_docopt_for_account_type(self):
        result = Defaults.docopt_for_account_type('Standard_LRS')
        assert result == '--locally-redundant'

        result = Defaults.docopt_for_account_type('Standard_ZRS')
        assert result == '--zone-redundant'

        result = Defaults.docopt_for_account_type('Standard_GRS')
        assert result == '--geo-redundant'

        result = Defaults.docopt_for_account_type('Standard_RAGRS')
        assert result == '--read-access-geo-redundant'
