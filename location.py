# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval

from trytond.modules.analytic_account import AnalyticMixin


__all__ = ['Location', 'Account']


class Location(AnalyticMixin):
    __metaclass__ = PoolMeta
    __name__ = 'stock.location'


class Account:
    __metaclass__ = PoolMeta
    __name__ = 'analytic_account.account'

    @classmethod
    def delete(cls, accounts):
        Location = Pool().get('stock.location')
        super(Account, cls).delete(accounts)
        # Restart the cache on the fields_view_get method of stock.location
        Location._fields_view_get_cache.clear()

    @classmethod
    def create(cls, vlist):
        Location = Pool().get('stock.location')
        accounts = super(Account, cls).create(vlist)
        # Restart the cache on the fields_view_get method of stock.location
        Location._fields_view_get_cache.clear()
        return accounts

    @classmethod
    def write(cls, accounts, values, *args):
        Location = Pool().get('stock.location')
        super(Account, cls).write(accounts, values, *args)
        # Restart the cache on the fields_view_get method of stock.location
        Location._fields_view_get_cache.clear()
