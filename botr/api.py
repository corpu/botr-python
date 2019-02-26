# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Python API kit for the Bits on the Run API
#
# Author:      Sergey Lashin
# Copyright:   (c) 2009 Bits on the Run
# Licence:     GNU Lesser General Public License, version 3
#              http://www.gnu.org/licenses/lgpl-3.0.txt
#
# Updated:     Tue Jun 23 10:09:13 CEST 2009
#
# For the System API documentation see http://docs.bitsontherun.com/system-api
#-----------------------------------------------------------------------------

__version__ = '1.2'

import hashlib
import pickle
import random
import io
import time
import urllib

import urllib.request as request


class API(object):
    """
        API
        ===
        An interface to the Bits on the Run API
    """

    def __init__(self, key, secret, version='v1'):
        self._url = 'http://api.bitsontherun.com' + '/' + version

        self._key = key
        self._secret = secret

    def _sign(self, args):
        """Hash the provided arguments"""

        # Convert parameters values to UTF-8 and escape them
        for key, value in args.items():
            args[key] = urllib.quote((unicode(value).encode("utf-8")), safe='~')

        # Construct Signature Base String
        sbs = '&'.join(['%s=%s' % (str(key), value) for key, value in sorted(args.items())])

        # Calculate the sha1 hash
        return hashlib.sha1(sbs + self._secret).hexdigest()

    def _args(self, args):
        """Append required arguments"""

        args['api_nonce'] = str(random.randint(0, 99999999)).zfill(8)
        args['api_timestamp'] = int(time.time())

        args['api_key'] = self._key

        if ('api_format' not in args):
            # Use serialised Python format for the API output,
            # otherwise use format specified in the call() args.
            args['api_format'] = 'py'

        # Sign the dictionary of arguments
        args['api_signature'] = self._sign(args)

        return args

    def call(self, api_call, args=None, url=None, verbose=False):
        """Execute an API call, returning a Python structure"""

        if url:
            url = url + api_call
        else:
            url = self._url + api_call

        args = self._args(args or {})
        query = urllib.urlencode(args)

        if request.__name__ == 'pycurl':
            curl = request.Curl()

            if verbose:
                # Enable verbose output
                curl.setopt(curl.VERBOSE, 1)

            curl.setopt(request.URL, url + '?' + query)
            curl.setopt(request.HTTPGET, 1)

            # Write response to a string
            output = io.StringIO()
            curl.setopt(request.WRITEFUNCTION, output.write)

            curl.perform()
            curl.close()

            response = output.getvalue()
        elif request.__name__ == 'urllib2':
            try:
                response = request.urlopen(url, query).read()
            except request.URLError as e:
                try:
                    error_code = e.code
                    response = e.read()
                except AttributeError:
                    response = e

        try:
            return pickle.loads(response)
        except:
            return response

    def upload(self, args={}, url=None, file_path=None, verbose=False):
        """Execute an API upload call, returning a Python structure"""

        if url:
            url = str(url)
        else:
            url = self._url

        if ('api_format' not in args):
            # Use serialised Python format for the API output,
            # otherwise use format specified in the args.
            args['api_format'] = 'py'

        query = urllib.urlencode(args)

        if request.__name__ == 'pycurl':
            curl = request.Curl()

            if verbose:
                # Enable verbose output
                curl.setopt(curl.VERBOSE, 1)

            curl.setopt(request.URL, url + '?' + query)

            post = [('file', (request.FORM_FILE, str(file_path)))]
            curl.setopt(request.HTTPPOST, post)

            if verbose:
                # Show upload progress
                curl.setopt(request.NOPROGRESS, 0)
                curl.setopt(request.PROGRESSFUNCTION, self._progress)

            # Have the response written back to a string
            output = io.StringIO()
            curl.setopt(request.WRITEFUNCTION, output.write)

            curl.perform()
            curl.close()

            response = output.getvalue()
        elif request.__name__ == 'urllib2':
            try:
                response = request.urlopen(url, urllib.urlencode(args)).read()
            except request.URLError as e:
                try:
                    error_code = e.code
                    response = e.read()
                except AttributeError:
                    response = e

        try:
            return pickle.loads(response)
        except:
            return response

    # On download/upload progress callback function
    def _progress(self, download_t, download_d, upload_t, upload_d):
        import sys
        uploaded = upload_d * 100 / upload_t
        sys.stdout.write(chr(27) + '[2K' + chr(27)+'[G')
        sys.stdout.write("Uploaded: %.2f%%" % uploaded)

