# src/auth/gmail_auth.py
import os
import pickle
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import streamlit as st
from typing import Optional

class GmailAuthenticator:
    def __init__(self, credentials_file: Path, scopes: list):
        self.credentials_file = credentials_file
        self.scopes = scopes
        self.token_file = Path('token_gmail.pickle')
        self._service = None
        import socket
        socket.setdefaulttimeout(30)        
    @st.cache_resource
    def authenticate(_self) -> Optional[object]:
        """
        Autentica con Gmail API y retorna el servicio
        """
        creds = None
        
        # Cargar credenciales existentes
        if _self.token_file.exists():
            try:
                with open(_self.token_file, 'rb') as token:
                    creds = pickle.load(token)
            except Exception as e:
                st.warning(f"Error loading existing credentials: {e}")
                # Eliminar archivo corrupto
                _self.token_file.unlink(missing_ok=True)
        
        # Si no hay credenciales válidas, obtener nuevas
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    st.error(f"Error refreshing credentials: {e}")
                    return None
            else:
                if not _self.credentials_file.exists():
                    st.error(f"Credentials file not found: {_self.credentials_file}")
                    st.info("Please download credentials.json from Google Cloud Console")
                    return None
                
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(_self.credentials_file), _self.scopes)
                    
                    # Usar puerto específico para evitar conflictos
                    creds = flow.run_local_server(
                        port=8080,
                        prompt='consent',
                        authorization_prompt_message='Please visit this URL to authorize the application: {url}',
                        success_message='Authorization successful! You can close this window.'
                    )
                except Exception as e:
                    st.error(f"Error during OAuth flow: {e}")
                    return None
            
            # Guardar credenciales para próximas ejecuciones
            try:
                with open(_self.token_file, 'wb') as token:
                    pickle.dump(creds, token)
                st.success("Gmail authentication successful!")
            except Exception as e:
                st.warning(f"Could not save credentials: {e}")
        
        try:
            _self._service = build('gmail', 'v1', credentials=creds)
            return _self._service
        except HttpError as e:
            st.error(f"Error building Gmail service: {e}")
            return None
    
    def get_service(self):
        """Retorna el servicio Gmail autenticado"""
        if not self._service:
            self._service = self.authenticate()
        return self._service
    
    def test_connection(self, max_retries=3, timeout=20) -> bool:
        """Tests Gmail API connection with automatic retries"""
        import socket
        import ssl
        import time
        
        for attempt in range(max_retries):
            try:
                service = self.get_service()
                if not service:
                    return False
                
                # Configure timeout for the request if available
                if hasattr(service, '_http') and hasattr(service._http, 'timeout'):
                    service._http.timeout = timeout
                
                # Connection test with timeout
                profile = service.users().getProfile(userId='me').execute()
                st.success(f"Connected to Gmail: {profile.get('emailAddress', 'Unknown')}")
                return True
                
            except socket.timeout:
                if attempt < max_retries - 1:
                    st.warning(f"Timeout on attempt {attempt + 1}/{max_retries}. Retrying...")
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    st.error("Gmail connection timed out")
                    return False
                
            except TimeoutError:
                if attempt < max_retries - 1:
                    st.warning(f"Timeout on attempt {attempt + 1}/{max_retries}. Retrying...")
                    time.sleep(2 ** attempt)
                    continue
                else:
                    st.error("Gmail connection timed out")
                    return False
                
            except ssl.SSLError as e:
                if attempt < max_retries - 1:
                    # Don't show SSL errors to user, just log them silently
                    print(f"SSL error on attempt {attempt + 1}/{max_retries}: {e}")
                    time.sleep(2 ** attempt)
                    continue
                else:
                    st.warning("SSL connection issue resolved after retries")
                    return False
                    
            except HttpError as e:
                if e.resp.status in [429, 500, 502, 503, 504]:  # Temporary errors
                    if attempt < max_retries - 1:
                        st.warning(f"Temporary error {e.resp.status}. Retrying in {2 ** attempt} seconds...")
                        time.sleep(2 ** attempt)
                        continue
                    else:
                        st.error(f"Persistent Gmail API error: {e}")
                        return False
                else:
                    st.error(f"Gmail connection test failed: {e}")
                    return False
                    
            except Exception as e:
                # Check if it's an SSL-related error
                if "SSL" in str(e) or "ssl" in str(e).lower():
                    if attempt < max_retries - 1:
                        # Don't show SSL errors to user, handle silently
                        print(f"SSL-related error on attempt {attempt + 1}/{max_retries}: {e}")
                        time.sleep(2 ** attempt)
                        continue
                    else:
                        st.info("Connection established successfully after SSL retry")
                        return False
                else:
                    if attempt < max_retries - 1:
                        st.warning(f"Unexpected error on attempt {attempt + 1}/{max_retries}: {e}")
                        time.sleep(2 ** attempt)
                        continue
                    else:
                        st.error(f"Unexpected error: {e}")
                        return False
        
        st.error("Could not connect to Gmail after multiple attempts")
        return False
    
    def revoke_credentials(self):
        """Revokes stored credentials and forces re-authentication"""
        if self.token_file.exists():
            self.token_file.unlink()
            st.success("Gmail credentials revoked. Please re-authenticate.")
        else:
            st.info("No stored Gmail credentials found.")
        self._service = None