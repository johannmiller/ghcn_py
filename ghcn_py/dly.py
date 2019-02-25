import numpy as np
import os
import logging

log = logging.getLogger(__name__)

_COLUMNS_ORIG = ['year','month','obs']
_DTYPES_ORIG = [np.int16, np.int8, (np.str_,4)]

_COLUMNS = ['year','month', 'day', 'obs', 'value']
_DTYPES = [np.int16, np.int8, np.int8, (np.str_,4), np.float32]


class Filter(object):
    """ 
    This class allows filtering on a single column. 

    Methods
    -------
    filter(data)
        Returns filtered data of shape (NUM_ROWS, 5)
    """

    _OPERATORS = ('eq', 'lt', 'lte', 'gt', 'gte')

    def __init__(self, column=None, value=None, operator='eq'):
        """
        Parameters
        ----------
        column : str, optional
            One of 'year','month', 'day', 'obs', 'value'
        value : str | int | float, optional
            The value to filter
        operator : str, optional
            One of 'eq', 'lt', 'lte', 'gt', 'gte' (default is 'eq')
        """
        if column not in (_COLUMNS):
            raise ValueError('column must be one of {}'.format(_COLUMNS))
        if operator not in self._OPERATORS:
            raise ValueError('operator must be one of {}'.format(self._OPERATORS))
        self._column = column
        self._value = value
        self._operator = operator


    def filter(self, data):
        """Filters numpy array.

        Parameters
        ----------
        data : numpy.ndarray
            Array of shape (N,5)

        Returns
        -------
        numpy.ndarray
            The filtered data, of same shape as the param.
        """
        if self._operator == 'lt':
            return data[data[self._column] < self._value]
        if self._operator == 'lte':
            return data[data[self._column] <= self._value]
        if self._operator == 'eq':
            return data[data[self._column] == self._value]
        if self._operator == 'gte':
            return data[data[self._column] >= self._value]
        if self._operator == 'gt':
            return data[data[self._column] > self._value]


class Dly(object):
    """ 
    This class provides a parser for .dly files.

    To understand the contents of GHCN daily files, please view the official doc https://www1.ncdc.noaa.gov/pub/data/ghcn/daily/readme.txt.  

    Methods
    -------
    parse(start_year=None, end_year=None, replace_missing_data=True)
        Parses the file, optionally slicing the data by year and replacing missing data

    get_data(filters=None)
        Return the parsed data, optionally filtered by filters

    get_data_as_dict(data)
        Return pythonic view of data, ie, dict of lists

    interpolate(data, fp_column, adjust_temp_values=True)
        Return data where missing values have been interpolated and temp units are expressed as degrees Celcius
    """

    def __init__(self, file):
        """
        Parameters
        ----------
        file : str
            Path to .dly file
        """
        if not os.path.exists(file):
            raise FileNotFoundError(file)
        self._file = file
        self._data = None
        log.debug('file {}'.format(file))


    def parse(self, start_year=None, end_year=None, replace_missing_data=True):
        """
        Parse the .dly file and store the resulting numpy array internally.

        Parameters
        ----------
        start_year : int, optional
            Slice the initial data so only rows after start_year are stored

        end_year : int, optional
            Slice the initial data so only rows before end_year are stored

        replace_missing_data: bool, optional
            Convert -9999 to numpy.nan
        """
        if (end_year and start_year) and (end_year < start_year):
            raise ValueError('end_year {} cannot be less than start_year {}'.format(end_year, start_year))

        dly_delimiter = [11,4,2,4] + [5,1,1,1] * 31
        dly_usecols = [1,2,3] + [4*i for i in range(1,32)]
        dly_dtype = _DTYPES_ORIG + [np.int32] * 31
        dly_names = _COLUMNS_ORIG + [str(day) for day in range(1,31+1)]

        self._data = np.genfromtxt(self._file,
                        delimiter=dly_delimiter,
                        usecols=dly_usecols,
                        dtype=dly_dtype,
                        names=dly_names)

        if start_year:
            self._data = self._data[self._data['year'] >= start_year]
        if end_year:
            self._data = self._data[self._data['year'] <= end_year]

        if self._data.shape[0] == 0:
            return

        self._data = self._unroll()
        if replace_missing_data:
            self._data['value'][self._data['value'] == -9999] = np.nan


    @staticmethod
    def interpolate(data, fp_column, adjust_temp_values=True):
        """
        Interpolate missing values

        Parameters
        ----------
        data : numpy.ndarray
            Data obtained by calling get_data

        fp_column : str
            The independent variable name. This is a column name. For example, to plot temp values against months, you would pass 'months'

        adjust_temp_values: bool, optional
            Divide all temp values by 10
        """
        nan = np.isnan(data['value'])
        data['value'][nan] = np.interp(data[fp_column][nan],data[fp_column][~nan], data['value'][~nan])

        if adjust_temp_values:
            try:
                data['value'][data['obs'] == 'TMIN'] = data['value']/10
                log.debug('Divided TMIN values by 10, so units are degrees Celcius')
            except ValueError:
                # ignore if column is not in data
                pass

            try:
                data['value'][data['obs'] == 'TMAX'] = data['value']/10
                log.debug('Divided TMAX values by 10, so units are degrees Celcius')
            except ValueError:
                # ignore if column is not in data
                pass
            
        return data

    def get_data(self, filters=None):
        """Return parsed data, optionally  filtered.

        Parameters
        ----------
        filters : list, optional
            Data filters to apply sequentially

        Returns
        -------
        numpy.ndarray
            Filtered data. 
        """
        if not filters:
            return self._data
        data = self._data
        for f in filters:
            data = f.filter(data)
        return data

    @staticmethod
    def get_data_as_dict(data):
        """Return pythonic view of data.

        This will return of dict of lists. Keys are ['year','month', 'day', 'obs', 'value'], and values are lists of data values.

        Parameters
        ----------
        data : numpy.ndarray
            Data to convert, usually after filtering and interpolation

        Returns
        -------
        dict
            Dictionary of lists
        """
        d = {}
        for c in _COLUMNS:
            d[c] = data[c].tolist()
        return d

    @staticmethod    
    def _unroll_record(record):
        startdate = np.datetime64('{}-{:02}'.format(record['year'],record['month']))
        dates = np.arange(startdate,startdate + np.timedelta64(1,'M'),np.timedelta64(1,'D'))
        rows = [ (record['year'], record['month'], (i+1), record['obs'], record[str(i+1)]) for i,_ in enumerate(dates) ]
        return np.array(rows, dtype={'names': _COLUMNS, 'formats': _DTYPES})


    def _unroll(self):
        return np.concatenate([self._unroll_record(row) for row in self._data])




    

    