# ghcn_py
## Overview
This is a simple python library for parsing Global Historical Climatology Network (GHCN) daily files. Have a look at the [official documentation](https://www1.ncdc.noaa.gov/pub/data/cdo/documentation/GHCND_documentation.pdf) for a thorough understanding, but the basic idea is:

- Every GHCN weather station has a unique id. It is the first column in this [list](https://www1.ncdc.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt).
- The daily weather observations for any given station can be accessed in a file named `{id}.dly` in  ftp://ftp.ncdc.noaa.gov/pub/data/ghcn/daily.

The daily files are structured such that each line represents one month's daily measurements for a particular observation, such as max temperature. The columns have fixed character widths, and each column is designated to hold a specific value, such as a date, measurement, quality flag, etc. The files can be difficult to work with and require a fair bit of manipulation if you want to issue queries like "show me all the years that had a max temp over 40Deg C".

## Installation
It is recommended that you first install and activate a [python3 virtual environment](https://docs.python.org/3/library/venv.html). Fork the repo. `pip install` ghcn_py from disk. This will also install `numpy`.

```
$ python3 -m venv ~/venv/ghcn
$ . ~/venv/ghcn/bin/activate
$ cd ghcn_py
$ pip install .
Collecting numpy>=1.16.0 (from ghcn-py==0.1.0)
  Using cached https://files.pythonhosted.org/packages/46/e4/4a0cc770e4bfb34b4e10843805fef67b9a94027e59162a586c776f35c5bb/numpy-1.16.1-cp37-cp37m-macosx_10_6_intel.macosx_10_9_intel.macosx_10_9_x86_64.macosx_10_10_intel.macosx_10_10_x86_64.whl
Installing collected packages: numpy, ghcn-py
  Running setup.py install for ghcn-py ... done
Successfully installed ghcn-py-0.1.0 numpy-1.16.1
```

## Usage
Import the Dly and Filter classes, and instantiate Dly with the path to a .dly file.
```
from ghcn_py.dly import Dly, Filter
d = Dly('USW00014936.dly')
```
Now parse the file. When calling parse, you may specify `start_year` and/or `end_year` kwargs. This pares down the dataset to the years you're interested in. If unspecified, the entire record set is loaded.
```
d.parse()
```
Create a list of filters to apply to the data. Filtering returns a new numpy array. The parsed data isn't mutated, so you apply any number of filter lists without re-parsing. 

An example might be useful. Let's say you want all the years which had a January TMAX > 5 degrees C. Filters are applied successively in `get_data`. 
```
>>> filters = [
...     Filter(column='month', value=1),
...     Filter(column='obs', value='TMAX', operator='eq'),
... ]
>>> data = d.get_data(filters)
>>> print(data)
[(1882, 1,  1, 'TMAX',  -50.) (1882, 1,  2, 'TMAX',  -50.)
 (1882, 1,  3, 'TMAX',  -11.) ... (2019, 1, 29, 'TMAX', -161.)
 (2019, 1, 30, 'TMAX', -228.) (2019, 1, 31, 'TMAX', -111.)]
```
The shape of the numpy array returned by `get_data` is (N,5), where N is the number of filtered rows. The 5 columns of the structured array can be accessed as `data[{column}]` where `column` is one of `['year','month', 'day', 'obs', 'value']`.

You may have noticed that the temperatures seem extreme. That is because temperatures are expressed in tenths of a degree in the .dly file. To filter temperatures above 5 deg C, you *could* add a 3rd filter for the value column like so `Filter(column='value', value=50, operator='gt')`, but it's better to interpolate first. This has 2 benefits. It automatically corrects the degree units, and more importantly it interpolates missing values (reported as -9999 in the .dly file), so you get better filtered results.

```
>>> data = d.interpolate(data, 'day')
Divided TMAX values by 10, so units are degrees Celcius
>>> print(data)
[(1882, 1,  1, 'TMAX',  -5. ) (1882, 1,  2, 'TMAX',  -5. )
 (1882, 1,  3, 'TMAX',  -1.1) ... (2019, 1, 29, 'TMAX', -16.1)
 (2019, 1, 30, 'TMAX', -22.8) (2019, 1, 31, 'TMAX', -11.1)]
```
Note that the temperatures look more reasonable. Now, you have to filter on the value column. Using numpy boolean masks is the easiest way to do so.
```
data = data[data['value'] > 5]
>>> print(data)
[(1882, 1,  6, 'TMAX',  7.8) (1882, 1,  7, 'TMAX',  7.2)
 (1882, 1,  9, 'TMAX',  5.6) (1883, 1,  9, 'TMAX',  7.2)
 (1884, 1, 12, 'TMAX',  5.6) (1884, 1, 13, 'TMAX',  6.7)
 (1884, 1, 17, 'TMAX',  6.7) (1884, 1, 27, 'TMAX',  6.7)
 (1885, 1,  8, 'TMAX',  7.8) (1886, 1, 13, 'TMAX',  5.6)
 (1889, 1,  2, 'TMAX',  5.6) (1890, 1, 30, 'TMAX',  6.1)
 ...
]
```

There you go. You have all the January observations where the temp exceeded 5 degrees. Your data is still a numpy array, but you can convert it to a python dict, where keys are column names and values are lists of values.

```
>>> py_data = d.get_data_as_dict(data)
>>> py_data.keys()
dict_keys(['year', 'month', 'day', 'obs', 'value'])
>>> py_data['year'][:3]
[1882, 1882, 1882]
```

## Tests
Install ghcn_py using this syntax, which will install test dependencies. Then run the tests as shown.
```
$ pip install -e .[test]
$ pytest
```
To generate a couple of plots to illustrate interpolation using the small test data set, do
```
$ cd test/plot/
$ python plot.py 
```
