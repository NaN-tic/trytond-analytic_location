# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval


__all__ = ['Location', 'Account']
__metaclass__ = PoolMeta


class Location:
    __name__ = 'stock.location'
    analytic_accounts = fields.Many2One('analytic_account.account.selection',
        'Analytic Accounts',
        states={
            'invisible': Eval('type') != 'warehouse',
            },
        depends=['type'])

    @classmethod
    def _view_look_dom_arch(cls, tree, type, field_children=None):
        AnalyticAccount = Pool().get('analytic_account.account')
        AnalyticAccount.convert_view(tree)
        arch, fields, = super(Location, cls)._view_look_dom_arch(tree, type,
            field_children=field_children)
        return arch, fields

    @classmethod
    def fields_get(cls, fields_names=None):
        AnalyticAccount = Pool().get('analytic_account.account')

        res = super(Location, cls).fields_get(fields_names)

        analytic_accounts_field = super(Location, cls).fields_get(
                ['analytic_accounts'])['analytic_accounts']

        res.update(AnalyticAccount.analytic_accounts_fields_get(
                analytic_accounts_field, fields_names,
                states=cls.analytic_accounts.states,
                required_states=Eval('type') == 'warehouse'))
        return res

    @classmethod
    def default_get(cls, fields, with_rec_name=True):
        fields = [x for x in fields if not x.startswith('analytic_account_')]
        return super(Location, cls).default_get(fields,
            with_rec_name=with_rec_name)

    @classmethod
    def read(cls, ids, fields_names=None):
        if fields_names:
            fields_names2 = [x for x in fields_names
                    if not x.startswith('analytic_account_')]
        else:
            fields_names2 = fields_names

        res = super(Location, cls).read(ids, fields_names=fields_names2)

        if not fields_names:
            fields_names = cls._fields.keys()

        root_ids = []
        for field in fields_names:
            if field.startswith('analytic_account_') and '.' not in field:
                root_ids.append(int(field[len('analytic_account_'):]))
        if root_ids:
            id2record = {}
            for record in res:
                id2record[record['id']] = record
            locations = cls.browse(ids)
            for location in locations:
                for root_id in root_ids:
                    id2record[location.id]['analytic_account_'
                        + str(root_id)] = None
                if location.type != 'warehouse':
                    continue
                if not location.analytic_accounts:
                    continue
                for account in location.analytic_accounts.accounts:
                    if account.root.id in root_ids:
                        id2record[location.id]['analytic_account_'
                            + str(account.root.id)] = account.id
                        for field in fields_names:
                            if field.startswith('analytic_account_'
                                    + str(account.root.id) + '.'):
                                _, field2 = field.split('.', 1)
                                id2record[location.id][field] = account[field2]
        return res

    @classmethod
    def create(cls, vlist):
        Selection = Pool().get('analytic_account.account.selection')
        vlist = [x.copy() for x in vlist]
        for vals in vlist:
            selection_vals = {}
            for field in vals.keys():
                if field.startswith('analytic_account_'):
                    if vals[field]:
                        selection_vals.setdefault('accounts', [])
                        selection_vals['accounts'].append(('add',
                                [vals[field]]))
                    del vals[field]
            if vals.get('analytic_accounts'):
                Selection.write([Selection(vals['analytic_accounts'])],
                    selection_vals)
            elif vals.get('type', 'internal') == 'warehouse':
                selection, = Selection.create([selection_vals])
                vals['analytic_accounts'] = selection.id
        return super(Location, cls).create(vlist)

    @classmethod
    def write(cls, *args):
        Selection = Pool().get('analytic_account.account.selection')

        actions = iter(args)
        args = []
        for locations, values in zip(actions, actions):
            values = values.copy()
            selection_vals = {}
            for field, value in values.items():
                if field.startswith('analytic_account_'):
                    root_id = int(field[len('analytic_account_'):])
                    selection_vals[root_id] = value
                    del values[field]
            if selection_vals:
                for location in locations:
                    if location.type != 'warehouse':
                        continue
                    accounts = []
                    if not location.analytic_accounts:
                        # Create missing selection
                        selection, = Selection.create([{}])
                        cls.write([location], {
                            'analytic_accounts': selection.id,
                            })
                    for account in location.analytic_accounts.accounts:
                        if account.root.id in selection_vals:
                            value = selection_vals[account.root.id]
                            if value:
                                accounts.append(value)
                        else:
                            accounts.append(account.id)
                    for account_id in selection_vals.values():
                        if account_id \
                                and account_id not in accounts:
                            accounts.append(account_id)
                    to_remove = list(set((a.id
                                for a in location.analytic_accounts.accounts))
                        - set(accounts))
                    Selection.write([location.analytic_accounts], {
                            'accounts': [
                                ('remove', to_remove),
                                ('add', accounts),
                                ],
                            })
            args.extend((locations, values))
        return super(Location, cls).write(*args)

    @classmethod
    def delete(cls, locations):
        Selection = Pool().get('analytic_account.account.selection')

        selections = []
        for location in locations:
            if location.analytic_accounts:
                selections.append(location.analytic_accounts)

        super(Location, cls).delete(locations)
        Selection.delete(selections)

    @classmethod
    def copy(cls, locations, default=None):
        Selection = Pool().get('analytic_account.account.selection')

        new_locations = super(Location, cls).copy(locations, default=default)

        for location in new_locations:
            if location.analytic_accounts:
                selection, = Selection.copy([location.analytic_accounts])
                cls.write([location], {
                    'analytic_accounts': selection.id,
                    })
        return new_locations


class Account:
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
