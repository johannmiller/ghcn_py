import pytest
import os
import numpy as np

from ghcn_py.dly import Dly, Filter


test_dir = os.path.abspath(os.path.dirname(__file__))


@pytest.fixture
def dly():
    file = os.path.join(test_dir, 'data', 'test.dly')
    return Dly(file)

def test_parse_outside_year(dly):
    dly.parse(start_year=2000)
    data = dly.get_data()
    assert 0 == len(data)

def test_parse_invalid_years(dly):
    with pytest.raises(ValueError):
        dly.parse(start_year=2000, end_year=1999)

def test_get_data(dly):
    dly.parse()
    data = dly.get_data()
    assert type(data) == np.ndarray
    assert 273 == len(data)

def test_get_data_as_dict(dly):
    dly.parse()
    data = dly.get_data_as_dict(dly.get_data())
    assert type(data) == dict
    assert 5 == len(data)

def test_filter_eq(dly):
    dly.parse()
    filters = [
        Filter(column='year', value=1900)
    ]
    data = dly.get_data(filters)
    years = dly.get_data_as_dict(data)['year']
    assert 90 == len(years)
    assert 1881 not in years
    assert 1900 in years
    assert 1950 not in years

def test_filter_gt(dly):
    dly.parse()
    filters = [
        Filter(column='year', value=1900, operator='gt')
    ]
    data = dly.get_data(filters)
    years = dly.get_data_as_dict(data)['year']
    assert 91 == len(years)
    assert 1881 not in years
    assert 1900 not in years
    assert 1950 in years

def test_filter_gte(dly):
    dly.parse()
    filters = [
        Filter(column='year', value=1900, operator='gte')
    ]
    data = dly.get_data(filters)
    years = dly.get_data_as_dict(data)['year']
    assert 181 == len(years)
    assert 1881 not in years
    assert 1900 in years
    assert 1950 in years

def test_filter_lt(dly):
    dly.parse()
    filters = [
        Filter(column='year', value=1881, operator='lt')
    ]
    data = dly.get_data(filters)
    years = dly.get_data_as_dict(data)['year']
    assert 0 == len(years)

def test_filter_lte(dly):
    dly.parse()
    filters = [
        Filter(column='year', value=1881, operator='lte')
    ]
    data = dly.get_data(filters)
    years = dly.get_data_as_dict(data)['year']
    assert 92 == len(years)
    assert 1881 in years
    assert 1900 not in years
    assert 1950 not in years

def test_multi_filter(dly):
    """
    Since test.dly is artificial, has 3 distinct years where each year has 3 observations in 3 distinct months, expectation here is to get a single value.  A normal .dly would yield 12 values, from the second of each month.
    """
    dly.parse()
    filters = [
        Filter(column='year', value=1881, operator='lte'),
        Filter(column='day', value=2, operator='eq'),
        Filter(column='obs', value='TMAX', operator='eq'),
    ]
    data = dly.get_data(filters)
    values = dly.get_data_as_dict(data)['value']
    assert 1 == len(values)
    assert 317 == values[0]

def test_interpolation(dly):
    """
    GHCN uses -9999 for data points that don't exist, or weren't collected form some reason.  Dly.parse() automatically replaces -9999 with np.nan (not a number), although this is controllable with the kwarg <code>replace_missing_data</code>.

    Call Dly.interpolate(...) to replace nan values with interpolated. Test that this occurs.
    """
    dly.parse()
    filters = [
        Filter(column='year', value=1950),
        Filter(column='month', value=4),
        Filter(column='obs', value='TMAX', operator='eq'),
    ]
    data = dly.get_data(filters)
    assert np.isnan(data['value'][2])
    assert 56 == data['value'][0]

    data = dly.interpolate(data, 'day')
    assert not np.isnan(data['value'][2])

    # floating point precision problem
    assert 5.6 == pytest.approx(data['value'][0])




