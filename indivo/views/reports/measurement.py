"""
Indivo Views -- Measurements
"""

from django.http import HttpResponseBadRequest, HttpResponse
from indivo.lib.view_decorators import marsloader, DEFAULT_ORDERBY
from indivo.lib.query import FactQuery, DATE, STRING, NUMBER
from indivo.models import Measurement
import copy

MEASUREMENT_FILTERS = {
  'lab_code' : ('type', STRING),
  'value' : ('value', NUMBER),
  'date_measured' : ('datetime', DATE),
  DEFAULT_ORDERBY : ('created_at', DATE)
}

MEASUREMENT_TEMPLATE = 'reports/measurement.xml'

def measurement_list(*args, **kwargs):
  """ For 1:1 mapping of URLs to views: calls _measurement_list """
  return _measurement_list(*args, **kwargs)

def carenet_measurement_list(*args, **kwargs):
  """ For 1:1 mapping of URLs to views: calls _measurement_list """
  return _measurement_list(*args, **kwargs)

@marsloader(query_api_support=True)
def _measurement_list(request, group_by, date_group, aggregate_by,
                      limit, offset, order_by,
                      status, date_range, filters,
                      lab_code, record=None, carenet=None):
  query_filters = copy.copy(filters)
  if lab_code:
    query_filters['lab_code'] = lab_code

  q = FactQuery(Measurement, MEASUREMENT_FILTERS,
                group_by, date_group, aggregate_by,
                limit, offset, order_by,
                status, date_range, query_filters,
                record, carenet)
  try:
    # hack, so we don't display lab_code in the output if it wasn't in the query string.
    q.execute()
    if q.query_filters.has_key('lab_code') and not filters.has_key('lab_code'):
      del q.query_filters['lab_code']

    return q.render(MEASUREMENT_TEMPLATE)
  except ValueError as e:
    return HttpResponseBadRequest(str(e))
