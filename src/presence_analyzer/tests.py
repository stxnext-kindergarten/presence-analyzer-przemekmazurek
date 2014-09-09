# -*- coding: utf-8 -*-
"""
Presence analyzer unit tests.
"""
import os.path
import json
import datetime
import unittest

from presence_analyzer import main, views, utils


TEST_DATA_CSV = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_data.csv'
)


# pylint: disable=maybe-no-member, too-many-public-methods
class PresenceAnalyzerViewsTestCase(unittest.TestCase):
    """
    Views tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})
        self.client = main.app.test_client()

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_mainpage(self):
        """
        Test main page redirect.
        """
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)
        assert resp.headers['Location'].endswith('/presence_weekday.html')

    def test_api_users(self):
        """
        Test users listing.
        """
        resp = self.client.get('/api/v1/users')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 2)
        self.assertDictEqual(data[0], {u'user_id': 10, u'name': u'User 10'})

    def test_api_mean_time_weekday(self):
        """
        Test mean weekday for given user.
        """
        resp = self.client.get('/api/v1/mean_time_weekday/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 7)
        self.assertEquals(data, [
            [u'Mon', 0],
            [u'Tue', 30047.0],
            [u'Wed', 24465.0],
            [u'Thu', 23705.0],
            [u'Fri', 0],
            [u'Sat', 0],
            [u'Sun', 0]])

    def test_mean_time_weekday_non_existing_id(self):
        """
        Test mean time for non-existing ID.
        """
        resp = self.client.get('/api/v1/mean_time_weekday/1')
        self.assertEqual(resp.status_code, 404)

    def test_api_presence_weekday(self):
        """
        Test if total presence of a given user is correctly computed.
        """
        resp = self.client.get('/api/v1/presence_weekday/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 8)
        self.assertEquals(data, [
            [u'Weekday', u'Presence (s)'],
            [u'Mon', 0],
            [u'Tue', 30047],
            [u'Wed', 24465],
            [u'Thu', 23705],
            [u'Fri', 0],
            [u'Sat', 0],
            [u'Sun', 0]])

    def test_presence_weekday_non_existing_id(self):
        """
        Tests presence of non-existing ID.
        """
        resp = self.client.get('/api/v1/presence_weekday/1')
        self.assertEqual(resp.status_code, 404)

    def test_api_presence_start_end(self):
        """
        Test if start/end presence of a given user is correctly computed.
        """
        resp = self.client.get('/api/v1/mean_start_end/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 7)
        self.assertEquals(data, [
            [u'Mon', 0, 0],
            [u'Tue', 34745.0, 64792.0],
            [u'Wed', 33592.0, 58057.0],
            [u'Thu', 38926.0, 62631.0],
            [u'Fri', 0, 0], [u'Sat', 0, 0],
            [u'Sun', 0, 0]])

    def test_presence_start_end_non_existing_id(self):
        """
        Test if start/end presence of a given user is correctly computed.
        """
        resp = self.client.get('/api/v1/mean_start_end/1')
        self.assertEqual(resp.status_code, 404)

class PresenceAnalyzerUtilsTestCase(unittest.TestCase):
    """
    Utility functions tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_get_data(self):
        """
        Test parsing of CSV file.
        """
        data = utils.get_data()
        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys(), [10, 11])
        sample_date = datetime.date(2013, 9, 10)
        self.assertIn(sample_date, data[10])
        self.assertItemsEqual(data[10][sample_date].keys(), ['start', 'end'])
        self.assertEqual(
            data[10][sample_date]['start'],
            datetime.time(9, 39, 5)
        )

    def test_seconds_since_midnight(self):
        """
        Test if seconds are computed correctly.
        """
        data = utils.seconds_since_midnight(datetime.time(1, 2, 3))
        self.assertEqual(data, 3723)

    def test_interval(self):
        """
        Test if interval is computed correctly.
        """
        start = datetime.time(1)
        end = datetime.time(1, 2, 3)
        data = utils.interval(start, end)
        self.assertEqual(data, 123)

    def test_mean(self):
        """
        Test calculation of arithmetic mean.
        """
        self.assertEqual(utils.mean([0]), 0)
        self.assertEqual(utils.mean(range(1, 10)), 5.)
        self.assertEqual(utils.mean(range(1, 5)), 2.5)
        self.assertIsInstance(utils.mean([0]), float)

    def test_group_by_weekday(self):
        """
        Test if function correctly groups by weekdays.
        """
        data = utils.get_data()
        li = [[], [30047], [24465], [23705], [], [], []]
        self.assertEqual(utils.group_by_weekday(data[10]), li)


def suite():
    """
    Default test suite.
    """
    base_suite = unittest.TestSuite()
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerViewsTestCase))
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerUtilsTestCase))
    return base_suite


if __name__ == '__main__':
    unittest.main()
