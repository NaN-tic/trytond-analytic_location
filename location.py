# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from sql.aggregate import Min
from sql.conditionals import Coalesce

from trytond import backend
from trytond.model import ModelSQL, ModelView, Unique, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval, If
from trytond.transaction import Transaction

from trytond.modules.analytic_account import AnalyticMixin

__all__ = ['Location', 'LocationCompany', 'AnalyticAccountEntry']


class Location(metaclass=PoolMeta):
    __name__ = 'stock.location'
    companies = fields.One2Many('stock.location.company', 'location',
        'Configuration by company')

    @classmethod
    def __setup__(cls):
        super(Location, cls).__setup__()
        cls.companies.states['invisible'] = (
            ~Eval('type', '').in_(cls.enabled_location_types()))
        cls.companies.depends.append('type')

    @staticmethod
    def enabled_location_types():
        # Extend it to show configuration by company in certain location types
        return []


class LocationCompany(AnalyticMixin, ModelSQL, ModelView):
    '''Stock Location by Company'''
    __name__ = 'stock.location.company'
    location = fields.Many2One('stock.location', 'Location', required=True,
        readonly=True, ondelete='CASCADE')
    company = fields.Many2One('company.company', 'Company', required=True,
        ondelete='CASCADE')

    @classmethod
    def __setup__(cls):
        super(LocationCompany, cls).__setup__()
        cls.analytic_accounts.domain = [
            ('company', '=', If(~Eval('company'),
                    Eval('context', {}).get('company', -1),
                    Eval('company', -1))),
            ]
        cls.analytic_accounts.depends.append('company')
        t = cls.__table__()
        cls._sql_constraints = [
            ('company_uniq', Unique(t, t.location, t.company),
                'The Company must to be unique per Location.')
            ]

    @classmethod
    def __register__(cls, module_name):
        pool = Pool()
        Account = pool.get('analytic_account.account')
        AccountEntry = pool.get('analytic.account.entry')
        Company = pool.get('company.company')
        Location = pool.get('stock.location')
        TableHandler = backend.get('TableHandler')
        cursor = Transaction().connection.cursor()

        super(LocationCompany, cls).__register__(module_name)

        location_handler = TableHandler(Location, module_name)
        # Migration from 3.4 from analytic_account_warehouse and analytic_stock
        # modules: analytic accounting in stock.location changed to reference
        # field to new stock.location.company model
        if location_handler.column_exist('analytic_accounts'):
            account = Account.__table__()
            company = Company.__table__()
            entry = AccountEntry.__table__()
            location = Location.__table__()
            table = cls.__table__()

            cursor.execute(*company.select(company.id,
                    order_by=company.id,
                    limit=1))
            default_company_id, = cursor.fetchone()

            cursor.execute(*table.insert([
                        table.create_uid,
                        table.create_date,
                        table.location,
                        table.company,
                        ],
                    location.join(entry,
                        condition=(
                            location.analytic_accounts == entry.selection)
                        ).join(account, condition=(entry.account == account.id)
                            ).select(
                                Min(entry.create_uid),
                                Min(entry.create_date),
                                location.id,
                                Coalesce(account.company, default_company_id),
                                group_by=(location.id, account.company))))
            cursor.execute(*location.join(entry,
                    condition=(location.analytic_accounts == entry.selection)
                    ).join(account, condition=(entry.account == account.id)
                        ).join(table,
                            condition=((table.location == location.id)
                                & (table.company == account.company)
                                )
                            ).select(
                                table.id, table.company,
                                location.analytic_accounts,
                                group_by=(table.id,
                                    location.analytic_accounts)))
            for loc_company_id, company_id, selection_id in cursor.fetchall():
                cursor.execute(*entry.update(
                        columns=[entry.origin],
                        values=['%s,%s' % (
                                LocationCompany.__name__, loc_company_id)],
                        from_=[account],
                        where=((entry.account == account.id)
                            & (account.company == company_id)
                            & (entry.selection == selection_id))))
            location_handler.drop_column('analytic_accounts')

    @staticmethod
    def default_company():
        return Transaction().context.get('company')


class AnalyticAccountEntry(metaclass=PoolMeta):
    __name__ = 'analytic.account.entry'

    @classmethod
    def _get_origin(cls):
        origins = super(AnalyticAccountEntry, cls)._get_origin()
        return origins + ['stock.location.company']

    @fields.depends('origin')
    def on_change_with_company(self, name=None):
        pool = Pool()
        LocationCompany = pool.get('stock.location.company')
        company = super(AnalyticAccountEntry, self).on_change_with_company(
            name)
        if isinstance(self.origin, LocationCompany) and self.origin.company:
            company = self.origin.company.id
        return company

    @classmethod
    def search_company(cls, name, clause):
        domain = super(AnalyticAccountEntry, cls).search_company(name, clause),
        return ['OR',
            domain,
            (('origin.company',) + tuple(clause[1:]) +
                ('stock.location.company',)),
            ]
