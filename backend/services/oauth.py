# services/oauth.py
"""
OAuth2 Authentication Service
Handles Google and Meta (Facebook) social login
"""
import os
import httpx
from typing import Optional, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# OAuth Provider URLs
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

FACEBOOK_AUTH_URL = "https://www.facebook.com/v18.0/dialog/oauth"
FACEBOOK_TOKEN_URL = "https://graph.facebook.com/v18.0/oauth/access_token"
FACEBOOK_USERINFO_URL = "https://graph.facebook.com/me"


@dataclass
class OAuthUser:
    """Standardized user data from OAuth providers"""
    provider: str  # 'google' or 'facebook'
    provider_id: str  # Unique ID from provider
    email: str
    name: str
    picture_url: Optional[str] = None


class GoogleOAuth:
    """Google OAuth2 handler"""
    
    def __init__(self):
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.redirect_uri = os.getenv("OAUTH_REDIRECT_URI", "https://trackrecord.life/auth/callback")
    
    def get_auth_url(self, state: str) -> str:
        """Generate Google OAuth authorization URL"""
        params = {
            "client_id": self.client_id,
            "redirect_uri": f"{self.redirect_uri}/google",
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "consent"
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{GOOGLE_AUTH_URL}?{query}"
    
    async def exchange_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for tokens"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uri": f"{self.redirect_uri}/google",
                    "grant_type": "authorization_code"
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Google token exchange failed: {response.text}")
                return None
    
    async def get_user_info(self, access_token: str) -> Optional[OAuthUser]:
        """Get user info from Google"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                return OAuthUser(
                    provider="google",
                    provider_id=data["id"],
                    email=data["email"],
                    name=data.get("name", data["email"].split("@")[0]),
                    picture_url=data.get("picture")
                )
            else:
                logger.error(f"Google user info failed: {response.text}")
                return None


class FacebookOAuth:
    """Facebook/Meta OAuth2 handler"""
    
    def __init__(self):
        self.app_id = os.getenv("FACEBOOK_APP_ID")
        self.app_secret = os.getenv("FACEBOOK_APP_SECRET")
        self.redirect_uri = os.getenv("OAUTH_REDIRECT_URI", "https://trackrecord.life/auth/callback")
    
    def get_auth_url(self, state: str) -> str:
        """Generate Facebook OAuth authorization URL"""
        params = {
            "client_id": self.app_id,
            "redirect_uri": f"{self.redirect_uri}/facebook",
            "response_type": "code",
            "scope": "email,public_profile",
            "state": state
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{FACEBOOK_AUTH_URL}?{query}"
    
    async def exchange_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for tokens"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                FACEBOOK_TOKEN_URL,
                params={
                    "code": code,
                    "client_id": self.app_id,
                    "client_secret": self.app_secret,
                    "redirect_uri": f"{self.redirect_uri}/facebook"
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Facebook token exchange failed: {response.text}")
                return None
    
    async def get_user_info(self, access_token: str) -> Optional[OAuthUser]:
        """Get user info from Facebook"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                FACEBOOK_USERINFO_URL,
                params={
                    "fields": "id,name,email,picture.type(large)",
                    "access_token": access_token
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                picture_url = None
                if "picture" in data and "data" in data["picture"]:
                    picture_url = data["picture"]["data"].get("url")
                
                return OAuthUser(
                    provider="facebook",
                    provider_id=data["id"],
                    email=data.get("email", f"{data['id']}@facebook.com"),
                    name=data.get("name", "Facebook User"),
                    picture_url=picture_url
                )
            else:
                logger.error(f"Facebook user info failed: {response.text}")
                return None


# Singleton instances
_google_oauth: Optional[GoogleOAuth] = None
_facebook_oauth: Optional[FacebookOAuth] = None


def get_google_oauth() -> GoogleOAuth:
    global _google_oauth
    if _google_oauth is None:
        _google_oauth = GoogleOAuth()
    return _google_oauth


def get_facebook_oauth() -> FacebookOAuth:
    global _facebook_oauth
    if _facebook_oauth is None:
        _facebook_oauth = FacebookOAuth()
    return _facebook_oauth
