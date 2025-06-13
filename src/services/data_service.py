# src/services/data_service.py
import pandas as pd
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import streamlit as st

class DataService:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(exist_ok=True)
        self.emails_file = self.data_dir / 'email_tracking.xlsx'
        self.settings_file = self.data_dir / 'app_settings.json'
        self.backup_dir = self.data_dir / 'backups'
        self.backup_dir.mkdir(exist_ok=True)
    
    def load_email_data(self) -> pd.DataFrame:
        """Carga los datos de seguimiento de emails"""
        if self.emails_file.exists():
            try:
                df = pd.read_excel(self.emails_file)
                # Asegurar que las columnas de fecha sean datetime
                date_columns = ['date_sent', 'follow_up_date', 'last_updated']
                for col in date_columns:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                return df
            except Exception as e:
                st.error(f"Error loading email data: {e}")
                return self._create_empty_dataframe()
        else:
            return self._create_empty_dataframe()
    
    def _create_empty_dataframe(self) -> pd.DataFrame:
        """Crea un DataFrame vacío con las columnas necesarias"""
        columns = [
            'id', 'thread_id', 'subject', 'to', 'to_emails', 'date_sent', 
            'snippet', 'has_reply', 'reply_count', 'status', 'priority',
            'days_since_sent', 'body_preview', 'labels', 'notes', 
            'follow_up_date', 'created_reminder', 'last_updated',
            'calendar_event_id', 'follow_up_count', 'final_outcome'
        ]
        return pd.DataFrame(columns=columns)
    
    def save_email_data(self, df: pd.DataFrame) -> bool:
        """Guarda los datos de seguimiento de emails"""
        try:
            # Crear backup antes de guardar
            self._create_backup()
            
            # Agregar timestamp de última actualización
            df['last_updated'] = datetime.now()
            

            # Convertir fechas con timezone a naive para Excel
            datetime_columns = ['date_sent', 'follow_up_date', 'last_updated']
            for col in datetime_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    if hasattr(df[col].dtype, 'tz') and df[col].dt.tz is not None:
                        df[col] = df[col].dt.tz_localize(None)

            # Guardar en Excel
            df.to_excel(self.emails_file, index=False)
            
            # También guardar en CSV para compatibilidad
            csv_file = self.emails_file.with_suffix('.csv')
            df.to_csv(csv_file, index=False)
            
            return True
            
        except Exception as e:
            st.error(f"Error saving email data: {e}")
            return False
    
    def _create_backup(self) -> bool:
        """Crea un backup de los datos actuales"""
        if not self.emails_file.exists():
            return True
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.backup_dir / f'email_tracking_backup_{timestamp}.xlsx'
            
            # Copiar archivo actual
            import shutil
            shutil.copy2(self.emails_file, backup_file)
            
            # Mantener solo los últimos 10 backups
            self._cleanup_old_backups()
            
            return True
            
        except Exception as e:
            st.warning(f"Could not create backup: {e}")
            return False
    
    def _cleanup_old_backups(self, keep_count: int = 10):
        """Limpia backups antiguos, manteniendo solo los más recientes"""
        try:
            backup_files = list(self.backup_dir.glob('email_tracking_backup_*.xlsx'))
            if len(backup_files) > keep_count:
                # Ordenar por fecha de modificación
                backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                # Eliminar los más antiguos
                for old_backup in backup_files[keep_count:]:
                    old_backup.unlink()
        except Exception as e:
            st.warning(f"Could not cleanup old backups: {e}")
    
    def merge_with_existing_data(self, new_df: pd.DataFrame) -> pd.DataFrame:
        """
        Fusiona datos nuevos con existentes, preservando estados y notas
        """
        existing_df = self.load_email_data()
        
        if existing_df.empty:
            return new_df
        
        # Columnas que queremos preservar de los datos existentes
        preserve_columns = [
            'status', 'notes', 'follow_up_date', 'created_reminder',
            'calendar_event_id', 'follow_up_count', 'final_outcome'
        ]
        
        # Hacer merge manteniendo datos existentes
        merged_df = pd.merge(
            new_df, 
            existing_df[['id'] + preserve_columns], 
            on='id', 
            how='left',
            suffixes=('', '_existing')
        )
        
        # Para cada columna a preservar, usar valor existente si está disponible
        for col in preserve_columns:
            existing_col = f'{col}_existing'
            if existing_col in merged_df.columns:
                merged_df[col] = merged_df[existing_col].combine_first(merged_df[col])
                merged_df = merged_df.drop(columns=[existing_col])
        
        return merged_df
    
    def update_email_status(self, email_id: str, status: str, notes: str = None) -> bool:
        """Actualiza el estado de un email específico"""
        try:
            df = self.load_email_data()
            
            # Encontrar el email
            mask = df['id'] == email_id
            if not mask.any():
                st.error(f"Email with ID {email_id} not found")
                return False
            
            # Actualizar estado
            df.loc[mask, 'status'] = status
            if notes is not None:
                df.loc[mask, 'notes'] = notes
            
            # Incrementar contador de seguimientos si es apropiado
            if status in ['Following Up', 'Contacted Again']:
                current_count = df.loc[mask, 'follow_up_count'].fillna(0).iloc[0]
                df.loc[mask, 'follow_up_count'] = current_count + 1
            
            # Guardar cambios
            return self.save_email_data(df)
            
        except Exception as e:
            st.error(f"Error updating email status: {e}")
            return False
    
    def get_analytics_data(self) -> Dict:
        """Genera datos analíticos del seguimiento de emails"""
        df = self.load_email_data()
        
        if df.empty:
            return {}
        
        total_emails = len(df)
        pending_emails = len(df[df['status'] == 'Pending'])
        replied_emails = len(df[df['has_reply'] == True])
        closed_emails = len(df[df['status'] == 'Closed'])
        
        # Calcular métricas
        response_rate = (replied_emails / total_emails * 100) if total_emails > 0 else 0
        follow_up_rate = (pending_emails / total_emails * 100) if total_emails > 0 else 0
        
        # Análisis por prioridad
        priority_counts = df['priority'].value_counts().to_dict() if 'priority' in df.columns else {}
        
        # Análisis temporal
        if 'date_sent' in df.columns:
            df['date_sent'] = pd.to_datetime(df['date_sent'], errors='coerce')
            recent_emails = df[df['date_sent'] >= (datetime.now() - pd.Timedelta(days=7))]
            weekly_count = len(recent_emails)
        else:
            weekly_count = 0
        
        # Tiempo promedio de respuesta
        replied_df = df[df['has_reply'] == True].copy()
        if not replied_df.empty and 'date_sent' in replied_df.columns:
            replied_df['response_time'] = replied_df['days_since_sent']
            avg_response_time = replied_df['response_time'].mean()
        else:
            avg_response_time = 0
        
        analytics = {
            'total_emails': total_emails,
            'pending_emails': pending_emails,
            'replied_emails': replied_emails,
            'closed_emails': closed_emails,
            'response_rate': round(response_rate, 1),
            'follow_up_rate': round(follow_up_rate, 1),
            'weekly_count': weekly_count,
            'avg_response_time': round(avg_response_time, 1),
            'priority_distribution': priority_counts,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M')
        }
        
        return analytics
    
    def export_to_excel(self, df: pd.DataFrame, filename: str = None) -> str:
        """Exporta DataFrame a Excel con formato mejorado"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'email_followup_export_{timestamp}.xlsx'
        
        export_path = self.data_dir.parent / 'exports' / filename
        export_path.parent.mkdir(exist_ok=True)
        
        try:
            with pd.ExcelWriter(export_path, engine='openpyxl') as writer:
                # Hoja principal con datos
                df.to_excel(writer, sheet_name='Email Tracking', index=False)
                
                # Hoja de analytics
                analytics = self.get_analytics_data()
                if analytics:
                    analytics_df = pd.DataFrame([analytics])
                    analytics_df.to_excel(writer, sheet_name='Analytics', index=False)
                
                # Hoja de resumen por estado
                if not df.empty:
                    status_summary = df.groupby('status').agg({
                        'id': 'count',
                        'priority': lambda x: x.value_counts().to_dict(),
                        'days_since_sent': 'mean'
                    }).reset_index()
                    status_summary.columns = ['Status', 'Count', 'Priority Distribution', 'Avg Days Since Sent']
                    status_summary.to_excel(writer, sheet_name='Status Summary', index=False)
            
            return str(export_path)
            
        except Exception as e:
            st.error(f"Error exporting to Excel: {e}")
            return None
    
    def load_settings(self) -> Dict:
        """Carga configuraciones de la aplicación"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                st.warning(f"Error loading settings: {e}")
        
        # Configuraciones por defecto
        return {
            'default_keywords': 'interview,follow up,proposal,meeting',
            'default_lookback_days': 30,
            'auto_backup': True,
            'reminder_default_time': '09:00',
            'timezone': 'America/New_York',
            'theme': 'light'
        }
    
    def save_settings(self, settings: Dict) -> bool:
        """Guarda configuraciones de la aplicación"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            return True
        except Exception as e:
            st.error(f"Error saving settings: {e}")
            return False
    
    def get_backup_files(self) -> List[Dict]:
        """Obtiene lista de archivos de backup disponibles"""
        try:
            backup_files = list(self.backup_dir.glob('email_tracking_backup_*.xlsx'))
            backups_info = []
            
            for backup_file in sorted(backup_files, key=lambda x: x.stat().st_mtime, reverse=True):
                stat = backup_file.stat()
                backups_info.append({
                    'filename': backup_file.name,
                    'path': str(backup_file),
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'created': datetime.fromtimestamp(stat.st_mtime),
                    'age_days': (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).days
                })
            
            return backups_info
            
        except Exception as e:
            st.error(f"Error getting backup files: {e}")
            return []
    
    def restore_from_backup(self, backup_path: str) -> bool:
        """Restaura datos desde un archivo de backup"""
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                st.error("Backup file not found")
                return False
            
            # Crear backup del estado actual antes de restaurar
            self._create_backup()
            
            # Copiar backup al archivo principal
            import shutil
            shutil.copy2(backup_file, self.emails_file)
            
            st.success(f"Data restored from backup: {backup_file.name}")
            return True
            
        except Exception as e:
            st.error(f"Error restoring from backup: {e}")
            return False