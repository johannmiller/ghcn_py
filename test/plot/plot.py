import os
import matplotlib.pyplot as pp

from ghcn_py.dly import Dly, Filter


test_dir = os.path.abspath(
        os.path.join('..', os.path.dirname(__file__)))


if __name__ == "__main__":
    """
    Generate 3 plots for demonstration. 
    This shows 1) you must call interpolate(...) in order to handle absent data values (-9999 in the .dly) and 2) the default behavior of interpolate is to divide TMIN and TMAX values by 10, since the .dly expresses temp values as tenths of a degree.
    """
    file = os.path.join(test_dir, 'data', 'test.dly')
    dly = Dly(file)
    dly.parse()
    filters = [
        Filter(column='year', value=1950),
        Filter(column='month', value=4),
        Filter(column='obs', value='TMAX', operator='eq'),
    ]
    data = dly.get_data(filters)
    fig, axs = pp.subplots(3, 1, constrained_layout=True)

    axs[0].plot(data['day'],data['value'])
    axs[0].set_title('No interpolation (NaN still present)')
    axs[0].set_xlabel('day')
    axs[0].set_ylabel('TMAX')

    data = dly.interpolate(data, 'day', adjust_temp_values=False)

    axs[1].plot(data['day'],data['value'])
    axs[1].set_title('Interpolated')
    axs[1].set_xlabel('day')
    axs[1].set_ylabel('TMAX')

    data = dly.interpolate(data, 'day')
    axs[2].plot(data['day'],data['value'])
    axs[2].set_title('TMAX expressed as degrees Celcius')
    axs[2].set_xlabel('day')
    axs[2].set_ylabel('TMAX')

    pp.show()