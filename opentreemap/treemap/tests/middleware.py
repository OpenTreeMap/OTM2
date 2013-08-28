from django.test import TestCase
from django.conf import settings
from django.http import HttpResponseRedirect
from opentreemap.middleware import InternetExplorerRedirectMiddleware


class USER_AGENT_STRINGS:
    IE_6 = 'Mozilla/5.0 (compatible; MSIE 6.0; Windows NT 5.1)'
    IE_7 = 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)'
    IE_8 = 'Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0)'
    IE_9 = 'Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0)'
    FIREFOX_22 = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; ' +\
                 'rv:22.0) Gecko/20130328 Firefox/22.0'


class MockRequest():
    def __init__(self, http_user_agent=None, path_info='/'):
        self.META = {
            'HTTP_USER_AGENT': http_user_agent,
            'PATH_INFO': path_info
        }


class InternetExplorerRedirectMiddlewareTests(TestCase):

    def _request_with_agent(self, http_user_agent):
        req = MockRequest(http_user_agent)
        res = InternetExplorerRedirectMiddleware().process_request(req)
        return req, res

    def _assert_redirects(self, response, expected_url):
        self.assertTrue(isinstance(response, HttpResponseRedirect))
        self.assertEquals(expected_url, response["Location"])

    def test_detects_ie(self):
        req, _ = self._request_with_agent(USER_AGENT_STRINGS.IE_7)
        self.assertTrue(req.from_ie,
                        'Expected the middleware to set "from_ie" '
                        'to True for an IE connection string')

    def test_does_not_detect_ie(self):
        req, _ = self._request_with_agent(USER_AGENT_STRINGS.FIREFOX_22)
        self.assertFalse(req.from_ie,
                         'Expected the middleware to set "from_ie" '
                         'to False for a Firefox user agent string')
        self.assertIsNone(req.ie_version,
                          'Expected the middleware to set "ie_version" '
                          'to None')

    def test_sets_version_and_does_not_redirect_for_ie_9(self):
        req, res = self._request_with_agent(USER_AGENT_STRINGS.IE_9)
        self.assertIsNone(res, 'Expected the middleware to return a None '
                          'response (no redirect) for IE 9')
        self.assertEquals(9, req.ie_version, 'Expected the middleware to '
                          'set "ie_version" to 9')

    def test_sets_version_and_redirects_ie_8(self):
        req, res = self._request_with_agent(USER_AGENT_STRINGS.IE_8)
        self._assert_redirects(res,
                               settings.IE_VERSION_UNSUPPORTED_REDIRECT_PATH)
        self.assertEquals(8, req.ie_version, 'Expected the middleware to set '
                          '"ie_version" to 8')

    def test_sets_version_and_redirects_ie_7(self):
        req, res = self._request_with_agent(USER_AGENT_STRINGS.IE_7)
        self._assert_redirects(res,
                               settings.IE_VERSION_UNSUPPORTED_REDIRECT_PATH)
        self.assertEquals(7, req.ie_version, 'Expected the middleware to set '
                          '"ie_version" to 7')

    def test_sets_version_and_redirects_ie_6(self):
        req, res = self._request_with_agent(USER_AGENT_STRINGS.IE_6)
        self._assert_redirects(res,
                               settings.IE_VERSION_UNSUPPORTED_REDIRECT_PATH)
        self.assertEquals(6, req.ie_version, 'Expected the middleware to set '
                          '"ie_version" to 6')
