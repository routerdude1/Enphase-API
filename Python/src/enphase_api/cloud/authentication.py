#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Enphase-API <https://github.com/Matthew1471/Enphase-API>
# Copyright (C) 2023 Matthew1471!
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# We can check JWT claims/expiration first before making a request to prevent annoying Enphase® ("pip install pyjwt" if not already installed).
import jwt

# Third party library for making HTTP(S) requests; "pip install requests" if getting import errors.
import requests

class Authentication:
    """A class to talk to Enphase®'s Cloud based Authentication Server, Entrez (French for "Access").
    This server also supports granting tokens for local access to the Gateway.
    """

    # Authentication host, Entrez (French for "Access").
    AUTHENTICATION_HOST = 'https://entrez.enphaseenergy.com'

    # This prevents the requests module from creating its own user-agent (and ask to not be included in analytics).
    STEALTHY_HEADERS = {'User-Agent': None, 'Accept':'application/json', 'DNT':'1'}
    STEALTHY_HEADERS_FORM = {'User-Agent': None, 'Accept':'application/json', 'Content-Type':'application/x-www-form-urlencoded', 'DNT':'1'}

    def authenticate(self, username, password):
        # Build the login request payload.
        payload = {'username':username, 'password':password}

        # Send the login request.
        response = requests.post(Authentication.AUTHENTICATION_HOST + '/login', headers=Authentication.STEALTHY_HEADERS_FORM, data=payload)

        # There's only 1 cookie value that is important to maintain session once we are authenticated.
        # SESSION - This links our future requests to our existing login session on this server.
        self.session_cookies = {'SESSION': response.cookies.get('SESSION')}

        # Return a true/false on whether login was successful.
        return (response.status_code == 200)

    def get_site(self, siteName):
        return requests.get(Authentication.AUTHENTICATION_HOST + '/site/' + requests.utils.quote(siteName, safe=''), headers=Authentication.STEALTHY_HEADERS, cookies=self.session_cookies).json()

    def get_token(self):
        #data = {'session_id': response_data['session_id'], 'serial_num': envoy_serial, 'username': user}
        return requests.post(Authentication.AUTHENTICATION_HOST + '/tokens', headers=Authentication.STEALTHY_HEADERS, cookies=self.session_cookies).json()

    @staticmethod
    def check_token_valid(token, serial):

        # An installer is always allowed to access any Gateway serial number.
        if serial:
            calculated_audience = [serial, 'un-commissioned']
        else:
            calculated_audience = ['un-commissioned']

        try:
            # Is the token still valid?
            jwt.decode(token, key='', algorithms='ES256', options={'verify_signature':False, 'require':['aud', 'iss', 'enphaseUser', 'exp', 'iat', 'jti', 'username'], 'verify_aud':True, 'verify_iss':True, 'verify_exp':True, 'verify_iat':True}, audience=calculated_audience, issuer='Entrez')

            # If we got to this line then no exceptions were generated by the above.
            return True

        # Should never happen as we do not currently validate the token's signature.
        except (jwt.exceptions.InvalidSignatureError, jwt.exceptions.InvalidKeyError):
            raise

        # We mask the specific reason and just ultimately inform the user that the token is invalid.
        except (jwt.exceptions.InvalidTokenError,
                jwt.exceptions.DecodeError,
                jwt.exceptions.ExpiredSignatureError,
                jwt.exceptions.InvalidAudienceError,
                jwt.exceptions.InvalidIssuerError,
                jwt.exceptions.InvalidIssuedAtError,
                jwt.exceptions.InvalidAlgorithmError,
                jwt.exceptions.MissingRequiredClaimError):

            # The token is invalid.
            return False

    def logout(self):
        response = requests.post(Authentication.AUTHENTICATION_HOST + '/logout', headers=Authentication.STEALTHY_HEADERS, cookies=self.session_cookies)
        return (response.status_code == 200)