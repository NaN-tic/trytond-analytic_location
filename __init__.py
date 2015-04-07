# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from .location import *


def register():
    Pool.register(
        Location,
        Account,
        module='analytic_account_warehouse', type_='model')
