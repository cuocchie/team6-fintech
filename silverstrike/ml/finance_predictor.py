import sys
import time
from pathlib import Path
import requests
import itertools
import json
from pandas import json_normalize
import numpy
import pandas
from sklearn.linear_model import LinearRegression, Lasso
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ExpSineSquared, WhiteKernel

from .tseries import TimeSeriesRegressor, time_series_split

# from feature_engineering.csv_handler import csv_to_formatted_dataframe
# from graphing.graphing import plot_predictions


def convert_json_to_dataframe():
    s = requests.Session()

    url = "http://localhost:8000/api"
    result = s.get(url, auth=('cuocchie@gmail.com','banmai111'))

    print(result.json())
    # dict = json.loads(result)
    
    df2 = json_normalize(result.json())
    return df2

def run_linear_regression(X, y, datelist):
    """
    Receives a formatted pandas dataframe,
    and performs a linear regression.
    Returns the root mean squared error on the test set.
    """
    stime = time.time()
    # print("\nLinear Regression")

    # Format data for fitting
    X_numeric = [pandas.to_numeric(example) for example in X]
    datelist_numeric = [pandas.to_numeric(date) for date in datelist]

    # Create linear regression object
    regression = LinearRegression()

    # Train the model using the training sets
    regression.fit(X_numeric, y)

    # Make predictions using the testing set
    y_pred = regression.predict(X_numeric)  # predictions on the domain of X
    y_pred_all = regression.predict(datelist_numeric)
    etime = time.time()
    # print("Run:{}".format(etime - stime))
    # # print(datelist)
    # print(len(y_pred_all))

    return y_pred, y_pred_all


# def run_gaussian_process_regression(X, y, datelist):
#     """
#     Receives a formatted pandas dataframe,
#     and performs a gaussian process regression.
#     Returns the root mean squared error on the test set.
#     """
#     stime = time.time()
#     # print("\nGaussian Process Regression")
#     # Format data for fitting
#     X_numeric = [pandas.to_numeric(example) for example in X]
#     datelist_numeric = [pandas.to_numeric(date) for date in datelist]
#
#     # Create linear regression object
#     kernel = ExpSineSquared(1.0, 5.0, periodicity_bounds=(1e-2, 1e2)) + WhiteKernel(1e-1)
#     regression = GaussianProcessRegressor(kernel=kernel, alpha=35, normalize_y=True)
#
#     # Fit the model
#     regression.fit(X_numeric, y)
#
#     # Make predictions using the testing set
#     y_pred = regression.predict(X_numeric)  # predictions on the domain of X
#     y_pred_all = regression.predict(datelist_numeric)
#     etime = time.time()
#     # print("Run:{}".format(etime - stime))
#
#     return y_pred, y_pred_all


def run_time_series(X, y, datelist):
    """
    Receives a formatted pandas dataframe,
    and performs a support vector regression.
    Returns the root mean squared error on the test set.
    """
    stime = time.time()
    # print("\nTime Series")
    # Format data for fitting
    X = X.astype('float64', copy=True)
    datelist = datelist.astype('float64', copy=True)

    # Create time series lasso regressor object
    n_prev = int(len(y)/2)
    empty_values = [numpy.nan for _ in range(0, n_prev)]
    tsr = TimeSeriesRegressor(n_prev=n_prev)  # uses linear regressions

    # Train the model using the training sets
    tsr.fit(X, y)

    # Make predictions using the testing set
    y_pred = tsr.predict(X)
    # y_pred = [*empty_values, *y_pred]
    """
    X = X[n_prev:]

    for date in datelist:
        tsr.fit(X, y_pred)
        X = numpy.append(X, date)
        X = X.reshape(len(X), 1)
        new_y_pred = tsr.predict(X)
        y_pred = numpy.append(y_pred, new_y_pred[-1])
    """

    datelist = numpy.append(X, datelist)
    datelist = datelist.reshape(len(datelist), 1)

    y_pred_all = tsr.predict(datelist)
    y_pred_all = [*empty_values, *y_pred_all]
    #y_pred_all = y_pred.copy()
    #y_pred_all = [*empty_values, *y_pred_all]
    etime = time.time()
    # print("Run:{}".format(etime - stime))
    # print(len(y_pred_all))

    return y_pred, y_pred_all


def process_file():
    try:
        # dataframe = csv_to_formatted_dataframe(file)
        dataframe = convert_json_to_dataframe()
    except Exception as err:
        print(str(err), "Skipping file.")
        exit()

    # print(dataframe)
    # Grab graphing data
    X = dataframe["date"].values
    # print(X)
    X = numpy.array(X, dtype='datetime64[ns]')
    y = dataframe["Networth"]
    # print(type(X[0]))
    # print(type(y[0]))

    # Create a list of dates with a 30-day interval
    datelist = numpy.arange(
        str(X[-1]),
        '2023-01-01T00:00:00.0000000',
        numpy.timedelta64(int(24), 'h'),
        dtype='datetime64'
    )
    datelist = numpy.delete(datelist, 0)

    # Format inputs
    X = X.reshape(len(X), 1)
    datelist = datelist.reshape(len(datelist), 1)
    X_and_datelist = [*X, *datelist]
    # print(type(X[0][0]))
    # print(X)
    # # print(X_and_datelist)
    # print(y)

    # Get predicted values
    lr_y, lr_y_all = run_linear_regression(X, y, X_and_datelist)
    ts_y, ts_y_all = run_time_series(X, y, datelist)
    # gpr_y, gpr_y_all = run_gaussian_process_regression(X, y, X_and_datelist)

    # print(X_and_datelist)
    datetest = numpy.array(X_and_datelist, dtype='datetime64[D]')
    datelabel = []
    for x in datetest:
        datelabel.append(str(x[0]))
    # print(datelabel)
    # print(len(X))
    dele = len(X)
    datafront = dataframe["Networth"].values.tolist()
    # print(datafront)
    # print(ts_y)
    databack = lr_y_all.tolist()
    databack2 = ts_y_all
    for z in range(0, dele):
        databack[z] = None
        databack2[z] = None
    databack[dele-1] = datafront[dele-1]
    databack2[dele - 1] = datafront[dele - 1]
    for k in range(dele, len(databack)):
        if databack[k] < 0:
            databack[k] = 0
        if databack2[k] < 0:
            databack2[k] = 0
    datatest = {
        'labels': datelabel,
        'datafront': datafront,
        'databack': databack,
        'databack2': databack2
    }
    print(datatest)
    # print(X_and_datelist)
    # datatest = {
    #     'labels': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14],
    #     'datafront': [1, 2, 3, 4, 5, 6, 7],
    #     'databack': [None, None, None, None, None, None, 7, 8, 9, 10, 11, 12, 13, 14],
    #     'databack2': [None, None, None, None, None, None, 7, 8, 9, 10, 11, 12, 13, 14]
    # }
    # datatest = {
    #     'labels': ['2022-10-01', '2022-10-02', '2022-10-03', '2022-10-04', '2022-10-05', '2022-10-06', '2022-10-07', '2022-10-08', '2022-10-09', '2022-10-10', '2022-10-11', '2022-10-12', '2022-10-13', '2022-10-14', '2022-10-15', '2022-10-16', '2022-10-17', '2022-10-18', '2022-10-19', '2022-10-20', '2022-10-21', '2022-10-22', '2022-10-23', '2022-10-24', '2022-10-25', '2022-10-26', '2022-10-27', '2022-10-28', '2022-10-29', '2022-10-30', '2022-10-31'],
    #     'datafront': [0, 243, 524],
    #     'databack': [None, None, 524, 779.6666666669771, 1041.666666666977, 1303.666666666977, 1565.666666666977, 1827.666666666977, 2089.666666666977, 2351.666666666977, 2613.666666666977, 2875.666666666977, 3137.666666666977, 3399.666666666977, 3661.666666666977, 3923.666666666977, 4185.666666666977, 4447.666666666977, 4709.666666666977, 4971.666666666977, 5233.666666666977, 5495.666666666977, 5757.666666666977, 6019.666666666977, 6281.666666666977, 6543.666666666977, 6805.666666666977, 7067.666666666977, 7329.666666666977, 7591.666666666977, 7853.666666666977]
    # }

    return datatest
    # plot_predictions(X, y, pred_dates=X_and_datelist, lines=[lr_y_all, ts_y_all, gpr_y_all])


def main(args):
    """
    Receives a file of transactions for one individual or
    a folder containing transaction files for individuals,
    calls helper functions to run regressions.
    """

    results = []

    # Load the provided personal finance dataset

    if len(args) == 1:
        # Default to preformatted.csv if no file is provided as an argument
        project_root = Path(__file__).resolve().parent.parent
        default_location = project_root/"datasets/preformatted.csv"
        results = process_file(default_location)

    elif len(args) == 2:
        location = Path(args[1])
        if location.is_file():
            results = process_file(location)
        elif location.is_dir():
            print("Folder provided. Please provide a file.")
            exit()
        else:
            print("Please provide a file as an argument.")
            exit()

    else:
        print("Too many arguments provided!")
        exit()


if __name__ == "__main__":
    main(sys.argv)
