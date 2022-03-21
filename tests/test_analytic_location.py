# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import unittest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import ModuleTestCase
from trytond.modules.company.tests import CompanyTestMixin

class TestCase(CompanyTestMixin, ModuleTestCase):
    'Test AnalyticLocation module'
    module = 'analytic_location'


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestCase))
    return suite
