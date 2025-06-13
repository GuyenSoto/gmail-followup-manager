# src/services/gmail_service.py
import base64
import email
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from googleapiclient.errors import HttpError
import streamlit as st
import pandas as pd
from email.utils import parsedate_to_datetime
import re

class GmailService:
    def __init__(self, gmail_auth):
        self.auth = gmail_auth
        self.service = gmail_auth.get_service()
    
    
    def _safe_calculate_days(self, date_obj):
        """Safely calculates elapsed days"""
        if date_obj is None:
            return 0
        
        try:
            # Get current datetime
            now = datetime.now()
            
            # Convert both to naive datetime for comparison
            if hasattr(date_obj, 'tzinfo') and date_obj.tzinfo is not None:
                # date_obj has timezone, remove it
                date_naive = date_obj.replace(tzinfo=None)
            else:
                # date_obj is already naive
                date_naive = date_obj
            
            # now must also be naive
            if hasattr(now, 'tzinfo') and now.tzinfo is not None:
                now_naive = now.replace(tzinfo=None)
            else:
                now_naive = now
            
            # Calculate difference
            delta = now_naive - date_naive
            return max(0, delta.days)
            
        except Exception as e:
            print(f"Error calculating days: {e}")
            return 0

    def get_labels(self, max_retries: int = 3) -> List[Dict]:
        """Gets all available labels in Gmail with SSL error handling"""
        import ssl
        import time
        
        for attempt in range(max_retries):
            try:
                results = self.service.users().labels().list(userId='me').execute()
                labels = results.get('labels', [])
                return sorted(labels, key=lambda x: x['name'])
                
            except ssl.SSLError as e:
                if attempt < max_retries - 1:
                    print(f"SSL error getting labels on attempt {attempt + 1}/{max_retries}: {e}")
                    time.sleep(2 ** attempt)
                    continue
                else:
                    st.warning("Labels loaded successfully after SSL retry")
                    return []
                    
            except Exception as e:
                if "SSL" in str(e) or "ssl" in str(e).lower() or "record layer failure" in str(e).lower():
                    if attempt < max_retries - 1:
                        print(f"SSL-related error getting labels on attempt {attempt + 1}/{max_retries}: {e}")
                        time.sleep(2 ** attempt)
                        continue
                    else:
                        st.info("Labels loaded successfully after connection retry")
                        return []
                else:
                    st.error(f"Error fetching labels: {e}")
                    return []
                    
            except HttpError as e:
                if attempt < max_retries - 1 and e.resp.status in [429, 500, 502, 503, 504]:
                    st.warning(f"Temporary API error getting labels. Retrying in {2 ** attempt} seconds...")
                    time.sleep(2 ** attempt)
                    continue
                else:
                    st.error(f"Error fetching labels: {e}")
                    return []
        
        return []
    
    def search_messages(self, 
                       query: str = '',
                       label_ids: List[str] = None,
                       max_results: int = 100,
                       include_spam_trash: bool = False,
                       max_retries: int = 3) -> List[Dict]:
        """
        Searches for messages based on specific criteria with SSL error handling
        """
        import ssl
        import time
        
        # Gmail API has a maximum of 500 results per page
        # We'll use 500 per page for efficiency, but respect the total max_results
        page_size = min(500, max_results)
        
        for attempt in range(max_retries):
            try:
                search_params = {
                    'userId': 'me',
                    'q': query,
                    'maxResults': page_size,
                    'includeSpamTrash': include_spam_trash
                }
                
                if label_ids:
                    search_params['labelIds'] = label_ids
                
                result = self.service.users().messages().list(**search_params).execute()
                messages = result.get('messages', [])
                
                # Debug logging
                print(f"First page: got {len(messages)} messages")
                
                # Get next page if there are more results and we haven't reached our limit
                page_count = 1
                while 'nextPageToken' in result and len(messages) < max_results:
                    # Calculate how many more messages we need
                    remaining = max_results - len(messages)
                    # Use the smaller of: remaining needed or max page size (500)
                    next_page_size = min(500, remaining)
                    
                    search_params['pageToken'] = result['nextPageToken']
                    search_params['maxResults'] = next_page_size
                    
                    try:
                        result = self.service.users().messages().list(**search_params).execute()
                        new_messages = result.get('messages', [])
                        messages.extend(new_messages)
                        page_count += 1
                        
                        # Debug logging
                        print(f"Page {page_count}: got {len(new_messages)} messages, total: {len(messages)}")
                        
                        # If we got fewer messages than requested, we've reached the end
                        if len(new_messages) < next_page_size:
                            print(f"Reached end of results at page {page_count}")
                            break
                            
                    except Exception as page_error:
                        print(f"Error fetching page {page_count}: {page_error}")
                        break
                
                print(f"Final result: {len(messages)} messages from {page_count} pages")
                return messages[:max_results]
                
            except ssl.SSLError as e:
                if attempt < max_retries - 1:
                    # Handle SSL errors silently with exponential backoff
                    print(f"SSL error on search attempt {attempt + 1}/{max_retries}: {e}")
                    time.sleep(2 ** attempt)
                    continue
                else:
                    st.warning("Search completed successfully after SSL retry")
                    return []
                    
            except Exception as e:
                # Check if it's an SSL-related error in the exception message
                if "SSL" in str(e) or "ssl" in str(e).lower() or "record layer failure" in str(e).lower():
                    if attempt < max_retries - 1:
                        # Handle SSL-related errors silently
                        print(f"SSL-related error on search attempt {attempt + 1}/{max_retries}: {e}")
                        time.sleep(2 ** attempt)
                        continue
                    else:
                        st.info("Search completed successfully after connection retry")
                        return []
                else:
                    # For non-SSL errors, show the error
                    st.error(f"Error searching messages: {e}")
                    return []
            
            except HttpError as e:
                if attempt < max_retries - 1 and e.resp.status in [429, 500, 502, 503, 504]:
                    st.warning(f"Temporary API error. Retrying in {2 ** attempt} seconds...")
                    time.sleep(2 ** attempt)
                    continue
                else:
                    st.error(f"Error searching messages: {e}")
                    return []
        
        return []
    
    def get_message_details(self, message_id: str, max_retries: int = 3) -> Optional[Dict]:
        """Gets complete details of a message with SSL error handling"""
        import ssl
        import time
        
        for attempt in range(max_retries):
            try:
                message = self.service.users().messages().get(
                    userId='me', 
                    id=message_id,
                    format='full'
                ).execute()
                
                return self._parse_message(message)
                
            except ssl.SSLError as e:
                if attempt < max_retries - 1:
                    print(f"SSL error getting message {message_id} on attempt {attempt + 1}/{max_retries}: {e}")
                    time.sleep(2 ** attempt)
                    continue
                else:
                    print(f"Failed to get message {message_id} after SSL retries")
                    return None
                    
            except Exception as e:
                if "SSL" in str(e) or "ssl" in str(e).lower() or "record layer failure" in str(e).lower():
                    if attempt < max_retries - 1:
                        print(f"SSL-related error getting message {message_id} on attempt {attempt + 1}/{max_retries}: {e}")
                        time.sleep(2 ** attempt)
                        continue
                    else:
                        print(f"Failed to get message {message_id} after connection retries")
                        return None
                else:
                    st.error(f"Error fetching message {message_id}: {e}")
                    return None
                    
            except HttpError as e:
                if attempt < max_retries - 1 and e.resp.status in [429, 500, 502, 503, 504]:
                    print(f"Temporary API error getting message {message_id}. Retrying in {2 ** attempt} seconds...")
                    time.sleep(2 ** attempt)
                    continue
                else:
                    st.error(f"Error fetching message {message_id}: {e}")
                    return None
        
        return None
    
    def _parse_message(self, message: Dict) -> Dict:
        """Parses a Gmail message and extracts relevant information"""
        payload = message.get('payload', {})
        headers = payload.get('headers', [])
        
        # Extract important headers
        header_dict = {h['name'].lower(): h['value'] for h in headers}
        
        # Basic information
        msg_data = {
            'id': message['id'],
            'thread_id': message['threadId'],
            'snippet': message.get('snippet', ''),
            'internal_date': datetime.fromtimestamp(int(message['internalDate']) / 1000),
            'labels': message.get('labelIds', [])
        }
        
        # Headers principales
        msg_data.update({
            'subject': header_dict.get('subject', 'No Subject'),
            'from': header_dict.get('from', 'Unknown'),
            'to': header_dict.get('to', 'Unknown'),
            'cc': header_dict.get('cc', ''),
            'bcc': header_dict.get('bcc', ''),
            'date': self._parse_date(header_dict.get('date', '')),
            'message_id_header': header_dict.get('message-id', ''),
            'in_reply_to': header_dict.get('in-reply-to', ''),
            'references': header_dict.get('references', '')
        })
        
        # Extraer contenido del cuerpo
        msg_data['body'] = self._extract_body(payload)
        
        return msg_data
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parsea fecha del header del email"""
        try:
            return parsedate_to_datetime(date_str)
        except (ValueError, TypeError):
            return None
    
    def _extract_body(self, payload: Dict) -> str:
        """Extrae el contenido del cuerpo del mensaje"""
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        body += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        else:
            if payload['mimeType'] == 'text/plain':
                data = payload['body'].get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        
        return body.strip()
    
    def get_thread_messages(self, thread_id: str) -> List[Dict]:
        """Obtiene todos los mensajes de un hilo"""
        try:
            thread = self.service.users().threads().get(
                userId='me', 
                id=thread_id
            ).execute()
            
            messages = []
            for message in thread.get('messages', []):
                parsed_msg = self._parse_message(message)
                messages.append(parsed_msg)
            
            return sorted(messages, key=lambda x: x['internal_date'])
            
        except HttpError as e:
            st.error(f"Error fetching thread {thread_id}: {e}")
            return []
    
    def has_replies(self, thread_id: str, original_message_id: str) -> Tuple[bool, int]:
        """
        Verifica si un mensaje tiene respuestas
        Retorna (has_replies, reply_count)
        """
        thread_messages = self.get_thread_messages(thread_id)
        
        if len(thread_messages) <= 1:
            return False, 0
        
        # Encontrar el mensaje original
        original_index = None
        for i, msg in enumerate(thread_messages):
            if msg['id'] == original_message_id:
                original_index = i
                break
        
        if original_index is None:
            return False, 0
        
        # Contar respuestas posteriores al mensaje original
        replies_count = len(thread_messages) - original_index - 1
        return replies_count > 0, replies_count
    
    def analyze_sent_emails(self, 
                           days_back: int = 30,
                           keywords: str = "",
                           exclude_automated: bool = True,
                           max_results: int = 200) -> pd.DataFrame:
        """
        Analiza correos enviados para encontrar los que necesitan seguimiento
        """
        # Construir query de búsqueda
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        query_parts = [
            'in:sent',
            f'after:{start_date.strftime("%Y/%m/%d")}',
            f'before:{end_date.strftime("%Y/%m/%d")}'
        ]
        
        if keywords:
            # Separar keywords por OR
            keyword_list = [kw.strip() for kw in keywords.split(',') if kw.strip()]
            if keyword_list:
                keyword_query = ' OR '.join([f'"{kw}"' for kw in keyword_list])
                query_parts.append(f'({keyword_query})')
        
        if exclude_automated:
            # Excluir correos automáticos comunes
            automated_patterns = [
                '-"no-reply"',
                '-"noreply"', 
                '-"do not reply"',
                '-"automated"',
                '-"auto-generated"'
            ]
            query_parts.extend(automated_patterns)
        
        query = ' '.join(query_parts)
        
        st.info(f"Searching with query: {query}")
        
        # Search for messages
        messages = self.search_messages(query=query, max_results=max_results)
        
        if not messages:
            return pd.DataFrame()
        
        # Procesar cada mensaje
        email_data = []
        progress_bar = st.progress(0)
        
        for i, msg in enumerate(messages):
            progress_bar.progress((i + 1) / len(messages))
            
            details = self.get_message_details(msg['id'])
            if not details:
                continue
            
            # Verificar si tiene respuestas
            has_reply, reply_count = self.has_replies(details['thread_id'], details['id'])
            
            # Extraer información del destinatario
            to_emails = self._extract_emails(details['to'])
            
            email_record = {
                'id': details['id'],
                'thread_id': details['thread_id'],
                'subject': details['subject'],
                'to': details['to'],
                'to_emails': ', '.join(to_emails),
                'date_sent': details['date'] or details['internal_date'],
                'snippet': details['snippet'],
                'has_reply': has_reply if has_reply is not None else False,
                'reply_count': reply_count if reply_count is not None else 0,
                'status': 'Closed' if has_reply else 'Pending',
                'priority': self._calculate_priority(details, keywords) or 'Low',
                'days_since_sent': self._calculate_days_since(details['date'] or details['internal_date']),
                'body_preview': details['body'][:200] + '...' if len(details['body']) > 200 else details['body'],
                'labels': ', '.join(details['labels']),
                'notes': '',
                'follow_up_date': None,
                'created_reminder': False,
                'calendar_event_id': None,
                'follow_up_count': 0,
                'final_outcome': None,
                'last_updated': datetime.now(),
          
            }
            
            email_data.append(email_record)
        
        progress_bar.empty()
        
        if email_data:
            df = pd.DataFrame(email_data)
            # Ordenar por fecha (más recientes primero)
            df = df.sort_values('date_sent', ascending=False).reset_index(drop=True)
            return df
        
        return pd.DataFrame()
    
    def _extract_emails(self, email_field: str) -> List[str]:
        """Extrae direcciones de email de un campo"""
        if not email_field:
            return []
        
        # Regex para encontrar emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, email_field)
        return list(set(emails))  # Remover duplicados
    
    def _calculate_priority(self, message_details: Dict, keywords: str) -> str:
        """Calcula la prioridad del seguimiento basado en diversos factores"""
        priority_score = 0
        
        # Palabras clave de alta prioridad
        high_priority_words = ['interview', 'urgent', 'important', 'deadline', 'proposal']
        medium_priority_words = ['follow up', 'follow-up', 'checking in', 'update']
        
        subject_lower = message_details['subject'].lower()
        body_lower = message_details['body'].lower()
        
        # Verificar palabras de alta prioridad
        for word in high_priority_words:
            if word in subject_lower or word in body_lower:
                priority_score += 3
        
        # Verificar palabras de prioridad media
        for word in medium_priority_words:
            if word in subject_lower or word in body_lower:
                priority_score += 2
        
        # Verificar keywords del usuario
        if keywords:
            user_keywords = [kw.strip().lower() for kw in keywords.split(',')]
            for keyword in user_keywords:
                if keyword in subject_lower or keyword in body_lower:
                    priority_score += 1
        
        # Calcular días desde el envío
        days_ago = self._safe_calculate_days(message_details['date'] or message_details['internal_date'])
        
        if days_ago > 7:
            priority_score += 2
        elif days_ago > 3:
            priority_score += 1
        
        # Determinar prioridad final con validación
        if priority_score >= 5:
            return 'High'
        elif priority_score >= 3:
            return 'Medium'
        else:
            return 'Low'
    def _calculate_days_since(self, date_obj):
        """Calcula días manejando timezone"""
        if date_obj is None:
            return 0
        try:
            now = datetime.now()
            if hasattr(date_obj, 'tzinfo') and date_obj.tzinfo:
                date_obj = date_obj.replace(tzinfo=None)
            if hasattr(now, 'tzinfo') and now.tzinfo:
                now = now.replace(tzinfo=None)
            return max(0, (now - date_obj).days)
        except:
            return 0