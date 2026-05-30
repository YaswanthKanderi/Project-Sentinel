import msal
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class MSALAuthenticator:
    def __init__(self):
        self.tenant_id = config.TENANT_ID
        self.client_id = config.CLIENT_ID
        self.client_secret = config.CLIENT_SECRET
        self.scope = config.GRAPH_SCOPE if hasattr(config, 'GRAPH_SCOPE') else ["https://graph.microsoft.com/.default"]
        self.token = None
        self._app = None

    def _build_app(self):
        authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self._app = msal.ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=authority
        )

    def get_token(self):
        if self._app is None:
            self._build_app()
        result = self._app.acquire_token_silent(scopes=self.scope, account=None)
        if not result:
            result = self._app.acquire_token_for_client(scopes=self.scope)
        if "access_token" in result:
            self.token = result["access_token"]
            return self.token
        raise Exception(f"Auth failed: {result.get('error')}")

    def get_headers(self):
        token = self.get_token()
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

authenticator = MSALAuthenticator()

def get_headers():
    return authenticator.get_headers()