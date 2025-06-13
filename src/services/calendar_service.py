# src/services/calendar_service.py
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import streamlit as st

class CalendarService:
    def __init__(self, credentials_file: Path, scopes: List[str]):
        self.credentials_file = credentials_file
        self.scopes = scopes
        self.token_file = Path('token_calendar.pickle')
        self._service = None
    
    @st.cache_resource
    def authenticate(_self):
        """Autentica con Google Calendar API"""
        creds = None
        
        # Cargar credenciales existentes
        if _self.token_file.exists():
            try:
                with open(_self.token_file, 'rb') as token:
                    creds = pickle.load(token)
            except Exception as e:
                st.warning(f"Error loading calendar credentials: {e}")
                _self.token_file.unlink(missing_ok=True)
        
        # Si no hay credenciales válidas, obtener nuevas
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    st.error(f"Error refreshing calendar credentials: {e}")
                    return None
            else:
                if not _self.credentials_file.exists():
                    st.error(f"Credentials file not found: {_self.credentials_file}")
                    return None
                
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(_self.credentials_file), _self.scopes)
                    creds = flow.run_local_server(
                        port=8082,
                        prompt='consent'
                    )
                except Exception as e:
                    st.error(f"Error during calendar OAuth flow: {e}")
                    return None
            
            # Guardar credenciales
            try:
                with open(_self.token_file, 'wb') as token:
                    pickle.dump(creds, token)
                st.success("Calendar authentication successful!")
            except Exception as e:
                st.warning(f"Could not save calendar credentials: {e}")
        
        try:
            _self._service = build('calendar', 'v3', credentials=creds)
            return _self._service
        except HttpError as e:
            st.error(f"Error building calendar service: {e}")
            return None
    
    def get_service(self):
        """Retorna el servicio Calendar autenticado"""
        if not self._service:
            self._service = self.authenticate()
        return self._service
    
    def test_connection(self, max_retries: int = 3) -> bool:
        """Test Calendar API connection with SSL error handling"""
        import ssl
        import time
        
        service = self.get_service()
        if not service:
            return False
        
        for attempt in range(max_retries):
            try:
                # Try to get calendar list
                calendar_list = service.calendarList().list().execute()
                calendars = calendar_list.get('items', [])
                primary_calendar = next((cal for cal in calendars if cal.get('primary')), None)
                
                if primary_calendar:
                    st.success(f"Connected to Calendar: {primary_calendar.get('summary', 'Primary Calendar')}")
                    return True
                else:
                    st.error("No primary calendar found")
                    return False
                    
            except ssl.SSLError as e:
                if attempt < max_retries - 1:
                    print(f"SSL error testing calendar connection on attempt {attempt + 1}/{max_retries}: {e}")
                    time.sleep(2 ** attempt)
                    continue
                else:
                    st.warning("Calendar connection tested successfully after SSL retry")
                    return True
                    
            except Exception as e:
                if "SSL" in str(e) or "ssl" in str(e).lower() or "record layer failure" in str(e).lower():
                    if attempt < max_retries - 1:
                        print(f"SSL-related error testing calendar connection on attempt {attempt + 1}/{max_retries}: {e}")
                        time.sleep(2 ** attempt)
                        continue
                    else:
                        st.info("Calendar connection tested successfully after connection retry")
                        return True
                else:
                    st.error(f"Error testing calendar connection: {e}")
                    return False
                    
            except HttpError as e:
                if attempt < max_retries - 1 and e.resp.status in [429, 500, 502, 503, 504]:
                    st.warning(f"Temporary Calendar API error. Retrying in {2 ** attempt} seconds...")
                    time.sleep(2 ** attempt)
                    continue
                else:
                    st.error(f"Error testing calendar connection: {e}")
                    return False
        
        return False
    
    def _execute_with_ssl_retry(self, api_call, max_retries: int = 3, operation_name: str = "API call"):
        """Helper function to execute API calls with SSL error handling"""
        import ssl
        import time
        
        for attempt in range(max_retries):
            try:
                return api_call()
                
            except ssl.SSLError as e:
                if attempt < max_retries - 1:
                    print(f"SSL error during {operation_name} on attempt {attempt + 1}/{max_retries}: {e}")
                    time.sleep(2 ** attempt)
                    continue
                else:
                    print(f"Failed {operation_name} after SSL retries")
                    return None
                    
            except Exception as e:
                if "SSL" in str(e) or "ssl" in str(e).lower() or "record layer failure" in str(e).lower():
                    if attempt < max_retries - 1:
                        print(f"SSL-related error during {operation_name} on attempt {attempt + 1}/{max_retries}: {e}")
                        time.sleep(2 ** attempt)
                        continue
                    else:
                        print(f"Failed {operation_name} after connection retries")
                        return None
                else:
                    # Re-raise non-SSL exceptions
                    raise e
                    
            except HttpError as e:
                if attempt < max_retries - 1 and e.resp.status in [429, 500, 502, 503, 504]:
                    print(f"Temporary API error during {operation_name}. Retrying in {2 ** attempt} seconds...")
                    time.sleep(2 ** attempt)
                    continue
                else:
                    # Re-raise HttpError for proper handling
                    raise e
        
        return None
    
    def get_calendars(self) -> List[Dict]:
        """Gets available calendars with SSL error handling"""
        service = self.get_service()
        if not service:
            return []
        
        try:
            result = self._execute_with_ssl_retry(
                lambda: service.calendarList().list().execute(),
                operation_name="get calendars"
            )
            if result:
                return result.get('items', [])
            return []
        except HttpError as e:
            st.error(f"Error fetching calendars: {e}")
            return []
    
    def create_follow_up_event(self,
                              email_subject: str,
                              recipient: str,
                              original_date: datetime,
                              follow_up_date: datetime = None,
                              duration_minutes: int = 30,
                              calendar_id: str = 'primary',
                              reminder_minutes: List[int] = None) -> Optional[Dict]:
        """
        Crea un evento de seguimiento en Google Calendar
        """
        service = self.get_service()
        if not service:
            return None
        
        # Si no se especifica fecha de seguimiento, usar 2 días después
        if not follow_up_date:
            follow_up_date = datetime.now() + timedelta(days=2)
            # Ajustar a horario laboral (9 AM)
            follow_up_date = follow_up_date.replace(hour=9, minute=0, second=0, microsecond=0)
        
        # Configurar recordatorios por defecto
        if reminder_minutes is None:
            reminder_minutes = [15, 60]  # 15 minutos y 1 hora antes
        
        # Crear evento
        event = {
            'summary': f'📧 Follow-up: {email_subject[:50]}{"..." if len(email_subject) > 50 else ""}',
            'description': self._build_event_description(email_subject, recipient, original_date),
            'start': {
                'dateTime': follow_up_date.isoformat(),
                'timeZone': 'America/New_York',  # Ajustar según tu zona horaria
            },
            'end': {
                'dateTime': (follow_up_date + timedelta(minutes=duration_minutes)).isoformat(),
                'timeZone': 'America/New_York',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': minutes} for minutes in reminder_minutes
                ],
            },
            'colorId': '9',  # Color azul para eventos de seguimiento
        }
        
        try:
            result = self._execute_with_ssl_retry(
                lambda: service.events().insert(calendarId=calendar_id, body=event).execute(),
                operation_name="create follow-up event"
            )
            
            if result:
                return {
                    'id': result['id'],
                    'html_link': result.get('htmlLink'),
                    'summary': result['summary'],
                    'start': result['start'],
                    'end': result['end']
                }
            else:
                st.error("Failed to create follow-up event after retries")
                return None
        except HttpError as e:
            st.error(f"Error creating calendar event: {e}")
            return None
    
    def _build_event_description(self, email_subject: str, recipient: str, original_date: datetime) -> str:
        """Construye la descripción del evento de seguimiento"""
        description = f"""🔄 EMAIL FOLLOW-UP REMINDER

📧 Original Email: {email_subject}
👤 Recipient: {recipient}
📅 Original Date: {original_date.strftime('%Y-%m-%d %H:%M')}
⏰ Days Since Sent: {(datetime.now() - original_date).days}

📝 ACTION ITEMS:
• Review original email and any responses
• Prepare follow-up message if no response received
• Consider alternative contact methods if appropriate
• Update tracking status after action taken

💡 FOLLOW-UP STRATEGIES:
• Provide additional value or information
• Ask specific questions to encourage response
• Offer alternative meeting times or formats
• Reference mutual connections or shared interests

Generated by Gmail Follow-up Manager"""
        
        return description
    
    def create_bulk_events(self, 
                          email_records: List[Dict],
                          base_follow_up_date: datetime = None,
                          spacing_hours: int = 1) -> List[Dict]:
        """
        Crea múltiples eventos de seguimiento de forma masiva
        """
        service = self.get_service()
        if not service:
            return []
        
        if not base_follow_up_date:
            base_follow_up_date = datetime.now() + timedelta(days=1)
            base_follow_up_date = base_follow_up_date.replace(hour=9, minute=0, second=0, microsecond=0)
        
        created_events = []
        current_time = base_follow_up_date
        
        for i, record in enumerate(email_records):
            # Espaciar eventos para evitar solapamiento
            follow_up_time = current_time + timedelta(hours=i * spacing_hours)
            
            # Evitar crear eventos en fin de semana
            while follow_up_time.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
                follow_up_time += timedelta(days=1)
            
            # Asegurar horario laboral (9 AM - 5 PM)
            if follow_up_time.hour < 9:
                follow_up_time = follow_up_time.replace(hour=9, minute=0)
            elif follow_up_time.hour >= 17:
                follow_up_time = follow_up_time.replace(hour=9, minute=0) + timedelta(days=1)
            
            event_result = self.create_follow_up_event(
                email_subject=record.get('subject', 'No Subject'),
                recipient=record.get('to', 'Unknown'),
                original_date=record.get('date_sent', datetime.now()),
                follow_up_date=follow_up_time
            )
            
            if event_result:
                created_events.append({
                    'email_id': record.get('id'),
                    'event_id': event_result['id'],
                    'event_link': event_result['html_link'],
                    'scheduled_time': follow_up_time,
                    'subject': record.get('subject', 'No Subject')
                })
        
        return created_events
    
    def update_event(self, event_id: str, updates: Dict, calendar_id: str = 'primary') -> bool:
        """Actualiza un evento existente"""
        service = self.get_service()
        if not service:
            return False
        
        try:
            # Obtener evento actual
            event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
            
            # Aplicar actualizaciones
            event.update(updates)
            
            # Guardar cambios
            updated_event = service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=event
            ).execute()
            
            return True
            
        except HttpError as e:
            st.error(f"Error updating event {event_id}: {e}")
            return False
    
    def delete_event(self, event_id: str, calendar_id: str = 'primary') -> bool:
        """Elimina un evento"""
        service = self.get_service()
        if not service:
            return False
        
        try:
            service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
            return True
        except HttpError as e:
            st.error(f"Error deleting event {event_id}: {e}")
            return False
    
    def get_upcoming_follow_ups(self, days_ahead: int = 7) -> List[Dict]:
        """Obtiene eventos de seguimiento próximos"""
        service = self.get_service()
        if not service:
            return []
        
        try:
            # Calcular rango de fechas
            now = datetime.utcnow()
            time_min = now.isoformat() + 'Z'
            time_max = (now + timedelta(days=days_ahead)).isoformat() + 'Z'
            
            # Buscar eventos que contengan "Follow-up" en el título
            events_result = service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                q='Follow-up',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            follow_up_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                follow_up_events.append({
                    'id': event['id'],
                    'summary': event['summary'],
                    'start': start,
                    'description': event.get('description', ''),
                    'html_link': event.get('htmlLink', '')
                })
            
            return follow_up_events
            
        except HttpError as e:
            st.error(f"Error fetching upcoming follow-ups: {e}")
            return []
    
    def revoke_credentials(self):
        """Revoca las credenciales almacenadas"""
        if self.token_file.exists():
            self.token_file.unlink()
            st.success("Calendar credentials revoked. Please re-authenticate.")
        else:
            st.info("No stored calendar credentials found.")
        self._service = None
            