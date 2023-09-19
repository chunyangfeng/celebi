"""用户认证授权
Date: 2023/9/14 18:01

Author: Fengchunyang

Contact: fengchunyang

Record:
    2023/9/14 Create file.

"""
import jwt
from jwt import DecodeError
from rest_framework import authentication


class JWTAuthentication(authentication.BasicAuthentication):
    """JWT用户认证"""

    def authenticate(self, request):
        """JWT用户认证

        Args:
            request(HttpRequest): request

        Returns:
            username(str): 用户名
            token(str): token
        """
        user = ""
        session = ""
        return user, session


class CasAuthentication(authentication.BasicAuthentication):
    """Cas用户认证"""

    def authenticate(self, request):
        """Cas用户认证

        Args:
            request(HttpRequest): request

        Returns:
            username(str): 用户名
            token(str): token
        """
        user = ""
        session = ""
        return user, session


class LdapAuthentication(authentication.BasicAuthentication):
    """Ldap用户认证"""

    def authenticate(self, request):
        """Ldap用户认证

        Args:
            request(HttpRequest): request

        Returns:
            username(str): 用户名
            token(str): token
        """
        user = ""
        session = ""
        return user, session
