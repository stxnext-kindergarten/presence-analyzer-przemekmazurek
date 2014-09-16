# -*- coding: utf-8 -*-
"""
Helper functions used in views.
"""

import csv
import time
from threading import Lock
from json import dumps
from functools import wraps
from datetime import datetime
from flask import Response

from presence_analyzer.main import app

import logging
log = logging.getLogger(__name__)  # pylint: disable=invalid-name

cached_data = {}


def cache(timeout=600):
    """
    Cashes data.
    """

    def middle(function):
        """
        Middle decorator function.
        """
        time_stamp = {}
        lock = Lock()

        def inner(*args, **kwargs):
            """
            Inner decorator function.
            """
            key = hash(function.__name__+repr(args)+repr(kwargs))
            current_time = time.time()

            def time_diff():
                if current_time - time_stamp[key] >= timeout:
                    return True
                else:
                    return False
            with lock:
                if key not in cached_data or time_diff():
                    time_stamp[key] = current_time
                    cached_data[key] = function(*args, **kwargs)
            return cached_data[key]
        return inner
    return middle


def jsonify(function):
    """
    Creates a response with the JSON representation of wrapped function result.
    """
    @wraps(function)
    def inner(*args, **kwargs):
        """
        This docstring will be overridden by @wraps decorator.
        """
        return Response(
            dumps(function(*args, **kwargs)),
            mimetype='application/json'
        )
    return inner


@cache(600)
def get_data():
    """
    Extracts presence data from CSV file and groups it by user_id.

    It creates structure like this:
    data = {
        'user_id': {
            datetime.date(2013, 10, 1): {
                'start': datetime.time(9, 0, 0),
                'end': datetime.time(17, 30, 0),
            },
            datetime.date(2013, 10, 2): {
                'start': datetime.time(8, 30, 0),
                'end': datetime.time(16, 45, 0),
            },
        }
    }
    """
    data = {}
    with open(app.config['DATA_CSV'], 'r') as csvfile:
        presence_reader = csv.reader(csvfile, delimiter=',')
        for i, row in enumerate(presence_reader):
            if len(row) != 4:
                # ignore header and footer lines
                continue

            try:
                user_id = int(row[0])
                date = datetime.strptime(row[1], '%Y-%m-%d').date()
                start = datetime.strptime(row[2], '%H:%M:%S').time()
                end = datetime.strptime(row[3], '%H:%M:%S').time()
            except (ValueError, TypeError):
                log.debug('Problem with line %d: ', i, exc_info=True)

            data.setdefault(user_id, {})[date] = {'start': start, 'end': end}

    return data


def group_by_weekday(items):
    """
    Groups presence entries by weekday.
    """
    result = [[] for x in range(0, 7)]
    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        result[date.weekday()].append(interval(start, end))
    return result


def seconds_since_midnight(time):
    """
    Calculates amount of seconds since midnight.
    """
    return time.hour * 3600 + time.minute * 60 + time.second


def interval(start, end):
    """
    Calculates inverval in seconds between two datetime.time objects.
    """
    return seconds_since_midnight(end) - seconds_since_midnight(start)


def mean(items):
    """
    Calculates arithmetic mean. Returns zero for empty lists.
    """
    return float(sum(items)) / len(items) if len(items) > 0 else 0


def group_by_weekday_start_end(items):
    """
    Groups presence srart/end by weekday.
    """
    result = [[] for x in range(0, 7)]
    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        result[date.weekday()].append([start, end])
    return result


def mean_from_list(items, column):
    """
    Calculates mean value from list.
    """
    if not items:
        return 0
    result = mean([
        seconds_since_midnight(hour[column])
        for hour in items])
    return result
