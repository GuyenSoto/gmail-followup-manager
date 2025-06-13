# app.py
import streamlit as st
import pandas as pd
# Configurar pandas para evitar warnings
pd.set_option('future.no_silent_downcasting', False)
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Agregar src al path para imports
sys.path.append(str(Path(__file__).parent / 'src'))

from config import Config
from auth.gmail_auth import GmailAuthenticator
from services.gmail_service import GmailService
from services.calendar_service import CalendarService
from services.data_service import DataService

# Configuración de la página
st.set_page_config(
    page_title=Config.PAGE_TITLE,
    page_icon=Config.PAGE_ICON,
    layout=Config.LAYOUT,
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
    }
    .priority-high {
        background-color: #ffebee;
        border-left: 5px solid #f44336;
    }
    .priority-medium {
        background-color: #fff3e0;
        border-left: 5px solid #ff9800;
    }
    .priority-low {
        background-color: #e8f5e8;
        border-left: 5px solid #4caf50;
    }
</style>
""", unsafe_allow_html=True)

def init_services():
    """Inicializa todos los servicios necesarios"""
    Config.ensure_directories()
    
    # Inicializar servicios
    gmail_auth = GmailAuthenticator(Config.CREDENTIALS_FILE, Config.GMAIL_SCOPES)
    calendar_service = CalendarService(Config.CREDENTIALS_FILE, Config.CALENDAR_SCOPES)
    data_service = DataService(Config.DATA_DIR)
    
    return gmail_auth, calendar_service, data_service

def render_header():
    """Renders the main header"""
    st.markdown(f"""
    <div class="main-header">
        <h1>{Config.PAGE_ICON} {Config.APP_NAME}</h1>
        <p>Intelligently manage your email follow-ups</p>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar(data_service):
    """Renders the sidebar with configuration settings"""
    st.sidebar.title("⚙️ Configuration")
    
    # Load settings
    settings = data_service.load_settings()
    
    # Search configurations
    st.sidebar.subheader("🔍 Search")
    keywords = st.sidebar.text_input(
        "Keywords (comma separated)",
        value=settings.get('default_keywords', 'interview,follow up,proposal,meeting'),
        help="Keywords to filter relevant emails",
        key="sidebar_keywords"
    )
    
    lookback_days = st.sidebar.number_input(
        "Days back",
        min_value=1,
        max_value=3650,  # 10 years
        value=settings.get('default_lookback_days', 30),
        help="How many days back to search for emails (up to 10 years)",
        key="sidebar_lookback_days"
    )
    
    exclude_automated = st.sidebar.checkbox(
        "Exclude automated emails",
        value=True,
        help="Filter out no-reply and automated emails",
        key="sidebar_exclude_automated"
    )
    
    # Reminder configurations
    st.sidebar.subheader("📅 Reminders")
    reminder_time = st.sidebar.time_input(
        "Default time for reminders",
        value=datetime.strptime(settings.get('reminder_default_time', '09:00'), '%H:%M').time(),
        key="sidebar_reminder_time"
    )
    
    reminder_days = st.sidebar.number_input(
        "Days for automatic reminder",
        min_value=1,
        max_value=30,
        value=2,
        help="Days after sending to create reminder",
        key="sidebar_reminder_days"
    )
    
    # Button to save configurations
    if st.sidebar.button("💾 Save Configuration"):
        new_settings = {
            'default_keywords': keywords,
            'default_lookback_days': lookback_days,
            'reminder_default_time': reminder_time.strftime('%H:%M'),
            'auto_backup': settings.get('auto_backup', True),
            'timezone': settings.get('timezone', 'America/New_York'),
            'theme': settings.get('theme', 'light')
        }
        if data_service.save_settings(new_settings):
            st.sidebar.success("✅ Configuration saved")
    
    return {
        'keywords': keywords,
        'lookback_days': lookback_days,
        'exclude_automated': exclude_automated,
        'reminder_time': reminder_time,
        'reminder_days': reminder_days
    }

def render_analytics_dashboard(data_service):
    """Renders the analytics dashboard"""
    st.subheader("📊 Follow-up Dashboard")
    
    analytics = data_service.get_analytics_data()
    
    if not analytics:
        st.info("No data to display. Please search for emails first.")
        return
    
    # Main metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📧 Total Emails",
            value=analytics['total_emails'],
            delta=f"+{analytics['weekly_count']} this week"
        )
    
    with col2:
        st.metric(
            label="⏳ Pending",
            value=analytics['pending_emails'],
            delta=f"{analytics['follow_up_rate']}% of total"
        )
    
    with col3:
        st.metric(
            label="✅ With Reply",
            value=analytics['replied_emails'],
            delta=f"{analytics['response_rate']}% response rate"
        )
    
    with col4:
        st.metric(
            label="⏱️ Average Time",
            value=f"{analytics['avg_response_time']:.1f} days",
            delta="response time"
        )
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Status distribution chart
        df_current = data_service.load_email_data()
        if not df_current.empty and 'status' in df_current.columns:
            status_counts = df_current['status'].value_counts()
            
            fig_status = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="Distribution by Status",
                color_discrete_map={
                    'Pending': '#ff7f0e',
                    'Closed': '#2ca02c',
                    'Following Up': '#d62728',
                    'Contacted Again': '#9467bd'
                }
            )
            fig_status.update_layout(height=400)
            st.plotly_chart(fig_status, use_container_width=True)
    
    with col2:
        # Priority chart
        if analytics['priority_distribution']:
            priority_data = analytics['priority_distribution']
            
            fig_priority = px.bar(
                x=list(priority_data.keys()),
                y=list(priority_data.values()),
                title="Distribution by Priority",
                color=list(priority_data.keys()),
                color_discrete_map={
                    'High': '#d62728',
                    'Medium': '#ff7f0e',
                    'Low': '#2ca02c'
                }
            )
            fig_priority.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig_priority, use_container_width=True)

def render_email_search(gmail_service, data_service, search_config):
    """Renders the email search section"""
    st.subheader("🔍 Email Search")
    
    # Search options
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Get available labels
        labels = gmail_service.get_labels()
        label_options = {label['name']: label['id'] for label in labels}
        
        selected_labels = st.multiselect(
            "Select Gmail labels",
            options=list(label_options.keys()),
            default=['SENT'] if 'SENT' in label_options else [],
            help="Select the folders/labels to search in",
            key="gmail_labels_unique"
        )
    
    with col2:
        max_results = st.number_input(
            "Maximum results",
            min_value=10,
            max_value=2000,
            value=500,
            step=50,
            key="max_results",
            help="Number of emails to retrieve. Higher values may take longer to process."
        )
    
    # Search button
    if st.button("🔍 Search Emails", type="primary", use_container_width=True):
        if not selected_labels:
            st.error("Please select at least one label")
            return None
        
        with st.spinner("🔄 Searching emails..."):
            # Perform search
            label_ids = [label_options[name] for name in selected_labels]
            
            try:
                df_results = gmail_service.analyze_sent_emails(
                    days_back=search_config['lookback_days'],
                    keywords=search_config['keywords'],
                    exclude_automated=search_config['exclude_automated'],
                    max_results=max_results
                )
                if not df_results.empty:
                    emergency_columns = {
                        'calendar_event_id': None,
                        'follow_up_count': 0,
                        'final_outcome': None
                    }
                    for col, default_val in emergency_columns.items():
                        if col not in df_results.columns:
                            df_results[col] = default_val

                if df_results.empty:
                    st.warning("No emails found with the specified criteria")
                    return None
                
                # Merge with existing data
                df_merged = data_service.merge_with_existing_data(df_results)
                
                # Save updated data
                if data_service.save_email_data(df_merged):
                    st.success(f"✅ Found {len(df_merged)} emails. Data saved successfully.")
                    return df_merged
                else:
                    st.error("Error saving data")
                    return df_results
                
            except Exception as e:
                st.error(f"Error during search: {e}")
                return None
    
    return None


def render_email_table(df, data_service, calendar_service, tab_prefix=""):
    """Renders the email table with editing functionalities"""
    if df is None or df.empty:
        st.info("No emails to display. Please search first.")
        return
    
    # Clean DataFrame of problematic NaN values
    if 'status' in df.columns:
        df['status'] = df['status'].fillna('Pending').infer_objects(copy=False)
    if 'priority' in df.columns:
        df['priority'] = df['priority'].fillna('Low').infer_objects(copy=False)
    
    # Clean problematic NaN data
    if not df.empty:
        # Fill NaN in numeric columns
        if 'days_since_sent' in df.columns:
            df['days_since_sent'] = df['days_since_sent'].fillna(0).infer_objects(copy=False)
        if 'reply_count' in df.columns:
            df['reply_count'] = df['reply_count'].fillna(0).infer_objects(copy=False)
        
        # Fill NaN in text columns
        if 'notes' in df.columns:
            df['notes'] = df['notes'].fillna('').infer_objects(copy=False)
        if 'subject' in df.columns:
            df['subject'] = df['subject'].fillna('(No Subject)').astype(str).infer_objects(copy=False)
        if 'to_emails' in df.columns:
            df['to_emails'] = df['to_emails'].fillna('').astype(str).infer_objects(copy=False)

    st.subheader("📋 Email List")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.multiselect(
            "Filter by status",
            options=[x for x in df['status'].unique() if pd.notna(x)] if 'status' in df.columns else [],
            default=[x for x in df['status'].unique() if pd.notna(x)] if 'status' in df.columns else [],
            key=f"{tab_prefix}status_filter"
        )
    
    with col2:
        # Priority filter
        priority_filter = st.multiselect(
            "Filter by priority",
            options=[x for x in df['priority'].unique() if pd.notna(x)] if 'priority' in df.columns else [],
            default=[x for x in df['priority'].unique() if pd.notna(x)] if 'priority' in df.columns else [],
            key=f"{tab_prefix}priority_filter"
        )
    
    with col3:
        # Additional filters can be added here
        st.write("")  # Placeholder for future filters
    
    # Apply filters
    df_filtered = df.copy()
    if status_filter and 'status' in df.columns:
        df_filtered = df_filtered[df_filtered['status'].isin(status_filter)]
    if priority_filter and 'priority' in df.columns:
        df_filtered = df_filtered[df_filtered['priority'].isin(priority_filter)]
    
    st.write(f"Showing {len(df_filtered)} of {len(df)} emails")
    
    # Column selection for display
    available_columns = df_filtered.columns.tolist()
    display_columns = st.multiselect(
        "Columns to display",
        options=available_columns,
        default=['subject', 'to_emails', 'date_sent', 'status', 'priority', 'days_since_sent', 'has_reply'],
        key=f"{tab_prefix}display_columns"
    )
    
    if not display_columns:
        st.warning("Select at least one column to display")
        return
    
    # Convert data types for data_editor
    if not df_filtered.empty:
        # Convert has_reply from float to boolean
        if 'has_reply' in df_filtered.columns:
            df_filtered['has_reply'] = df_filtered['has_reply'].fillna(False).infer_objects(copy=False).astype(bool)
        
        
        # Convert other boolean columns
        if 'created_reminder' in df_filtered.columns:
            df_filtered['created_reminder'] = df_filtered['created_reminder'].fillna(False).infer_objects(copy=False).astype(bool)
        
        # Convert numeric columns
        if 'days_since_sent' in df_filtered.columns:
            df_filtered['days_since_sent'] = pd.to_numeric(df_filtered['days_since_sent'], errors='coerce').fillna(0).astype(int)

    # Show editable table
    edited_df = st.data_editor(
        df_filtered[display_columns],
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "subject": st.column_config.TextColumn("Subject", width="large"),
            "to_emails": st.column_config.TextColumn("Recipients", width="medium"),
            "date_sent": st.column_config.DatetimeColumn("Date Sent"),
            "status": st.column_config.SelectboxColumn(
                "Status",
                options=["Pending", "Following Up", "Contacted Again", "Closed", "No Response Needed"]
            ),
            "priority": st.column_config.SelectboxColumn(
                "Priority",
                options=["High", "Medium", "Low"]
            ),
            "notes": st.column_config.TextColumn("Notes", width="large"),
            "has_reply": st.column_config.CheckboxColumn("Has Reply")
        },
        hide_index=True,
        key=f"{tab_prefix}data_editor"
    )
    
    # Action buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("💾 Save Changes", use_container_width=True, key=f"{tab_prefix}save_changes"):
            # Apply changes to original DataFrame
            for idx, row in edited_df.iterrows():
                original_idx = df_filtered.index[idx]
                for col in display_columns:
                    if col in df.columns:
                        df.loc[original_idx, col] = row[col]
            
            if data_service.save_email_data(df):
                st.success("✅ Changes saved successfully")
                st.rerun()
    
    with col2:
        if st.button("📤 Export Excel", use_container_width=True, key=f"{tab_prefix}export_excel"):
            export_path = data_service.export_to_excel(df_filtered)
            if export_path:
                st.success(f"✅ Exported to: {export_path}")
    
    with col3:
        # Multiple selection for creating reminders
        def format_subject(x):
            """Safely format email subject for display"""
            subject = df_filtered.loc[x, 'subject']
            # Handle NaN or non-string values
            if pd.isna(subject) or not isinstance(subject, str):
                return f"Email {x} (No Subject)"
            # Handle normal string subjects
            return f"{subject[:50]}..." if len(subject) > 50 else subject
        
        selected_emails = st.multiselect(
            "Select for reminders",
            options=df_filtered.index.tolist(),
            format_func=format_subject,
            key=f"{tab_prefix}selected_emails"
        )
    
    with col4:
        if st.button("📅 Create Reminders", use_container_width=True, disabled=not selected_emails, key=f"{tab_prefix}create_reminders"):
            create_calendar_reminders(df_filtered, selected_emails, calendar_service, data_service)

def create_calendar_reminders(df, selected_indices, calendar_service, data_service):
    """Creates reminders in Google Calendar for selected emails"""
    if not selected_indices:
        st.warning("No emails selected")
        return
    
    with st.spinner("📅 Creating reminders in Google Calendar..."):
        selected_records = []
        for idx in selected_indices:
            record = df.loc[idx].to_dict()
            selected_records.append(record)
        
        # Create events in Calendar
        created_events = calendar_service.create_bulk_events(selected_records)
        
        if created_events:
            # Update data with created event IDs
            for event_info in created_events:
                email_id = event_info['email_id']
                calendar_event_id = event_info['event_id']
                
                # Update in DataFrame
                mask = df['id'] == email_id
                if mask.any():
                    df.loc[mask, 'created_reminder'] = True
                    df.loc[mask, 'calendar_event_id'] = calendar_event_id
                    df.loc[mask, 'follow_up_date'] = event_info['scheduled_time']
            
            # Save changes
            data_service.save_email_data(df)
            
            st.success(f"✅ Created {len(created_events)} reminders in Google Calendar")
            
            # Show links to events
            st.subheader("🔗 Created Reminder Links")
            for event_info in created_events:
                st.markdown(f"• [{event_info['subject'][:50]}...]({event_info['event_link']})")
        else:
            st.error("Could not create reminders")

def render_upcoming_followups(calendar_service):
    """Renders the upcoming follow-ups section"""
    st.subheader("📅 Upcoming Follow-ups")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        days_ahead = st.number_input(
            "Days ahead",
            min_value=1,
            max_value=30,
            value=7,
            key="days_ahead"
        )
    
    with col1:
        if st.button("🔄 Update Upcoming Follow-ups", use_container_width=True):
            upcoming_events = calendar_service.get_upcoming_follow_ups(days_ahead)
            
            if upcoming_events:
                for event in upcoming_events:
                    with st.expander(f"📧 {event['summary']} - {event['start'][:10]}"):
                        st.write(f"**Date:** {event['start']}")
                        st.write(f"**Description:** {event['description'][:200]}...")
                        if event['html_link']:
                            st.markdown(f"[🔗 Open in Google Calendar]({event['html_link']})")
            else:
                st.info("No follow-ups scheduled for the upcoming days")

def render_backup_management(data_service):
    """Renders the backup management section"""
    with st.expander("🔄 Backup Management"):
        st.subheader("Backup Files")
        
        backups = data_service.get_backup_files()
        
        if backups:
            backup_df = pd.DataFrame(backups)
            st.dataframe(backup_df[['filename', 'size_mb', 'created', 'age_days']], use_container_width=True)
            
            col1, col2 = st.columns(2)
            with col1:
                selected_backup = st.selectbox(
                    "Select backup to restore",
                    options=[b['filename'] for b in backups]
                )
            
            with col2:
                if st.button("🔄 Restore Backup", type="secondary"):
                    selected_path = next(b['path'] for b in backups if b['filename'] == selected_backup)
                    if data_service.restore_from_backup(selected_path):
                        st.rerun()
        else:
            st.info("No backup files available")

def main():
    """Main application function"""
    # Render header
    render_header()
    
    # Initialize services
    try:
        gmail_auth, calendar_service, data_service = init_services()
    except Exception as e:
        st.error(f"Error initializing services: {e}")
        return
    
    # Verify authentication
    if not gmail_auth.test_connection():
        st.error("❌ Could not connect to Gmail. Please verify your authentication.")
        if st.button("🔄 Re-authenticate"):
            gmail_auth.revoke_credentials()
            st.rerun()
        return
    
    if not calendar_service.test_connection():
        st.warning("⚠️ Could not connect to Google Calendar. Some features will not be available.")
    
    # Render sidebar with configurations
    search_config = render_sidebar(data_service)
    
    # Create main tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "🔍 Search", "📋 Management", "⚙️ Settings"])
    
    with tab1:
        render_analytics_dashboard(data_service)
        render_upcoming_followups(calendar_service)
    
    with tab2:
        gmail_service = GmailService(gmail_auth)
        df_results = render_email_search(gmail_service, data_service, search_config)
        
        if df_results is not None:
            render_email_table(df_results, data_service, calendar_service, "search_")
    
    with tab3:
        # Load existing data for management
        existing_df = data_service.load_email_data()
        if not existing_df.empty:
            render_email_table(existing_df, data_service, calendar_service, "manage_")
        else:
            st.info("No data to manage. Go to the 'Search' tab to get started.")
    
    with tab4:
        st.subheader("⚙️ Advanced Settings")
        
        # Credential management
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Renew Gmail Credentials"):
                gmail_auth.revoke_credentials()
                st.success("Gmail credentials removed. Restart the app to re-authenticate.")
        
        with col2:
            if st.button("🔄 Renew Calendar Credentials"):
                calendar_service.revoke_credentials()
                st.success("Calendar credentials removed. Restart the app to re-authenticate.")
        
        # Backup management
        render_backup_management(data_service)
        
        # System information
        st.subheader("ℹ️ System Information")
        st.info(f"""
        **Version:** 1.0.0
        **Data directory:** {Config.DATA_DIR}
        **Credentials file:** {Config.CREDENTIALS_FILE}
        **Last update:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """)

if __name__ == "__main__":
    main()