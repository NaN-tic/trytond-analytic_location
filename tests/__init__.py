# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
try:
    from trytond.modules.analytic_location.tests.test_analytic_location import suite
except ImportError:
    from .test_analytic_location import suite

__all__ = ['suite']
