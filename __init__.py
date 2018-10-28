# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import location

def register():
    Pool.register(
        location.Location,
        location.LocationCompany,
        location.AnalyticAccountEntry,
        module='analytic_location', type_='model')
