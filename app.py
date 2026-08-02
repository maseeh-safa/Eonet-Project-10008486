# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, Response
from models import EventFetcher, NaturalEvent, WatchedEvent

import sqlite3
from datetime import datetime

# Database configuration
DATABASE = 'events.db'

def get_db_connection():
    """
    Create a connection to the database
    Returns a connection object
    """
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # This lets us access columns by name
    return conn

def init_db():
    """
    Initialize the database - create tables if they don't exist
    This runs automatically when the app starts
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create watched_events table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS watched_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            eonet_id TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            category TEXT,
            status TEXT,
            latitude REAL,
            longitude REAL,
            event_date TEXT,
            magnitude REAL,
            mag_unit TEXT,
            source_url TEXT,
            note TEXT DEFAULT '',
            alert_active INTEGER DEFAULT 0,
            saved_at TEXT DEFAULT (datetime('now'))
        )
    ''')
    
    # Create categories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT NOT NULL UNIQUE,
            label TEXT NOT NULL
        )
    ''')
    
    # Create search_log table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_text TEXT,
            searched_at TEXT DEFAULT (datetime('now'))
        )
    ''')
    
    # Seed categories (if they don't exist)
    seed_categories(cursor)
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")

def seed_categories(cursor):
    """
    Seed the categories table with default categories
    These are the main categories from NASA's EONET
    """
    categories = [
        ('wildfires', 'Wildfires'),
        ('severeStorms', 'Severe Storms'),
        ('volcanoes', 'Volcanoes'),
        ('floods', 'Floods'),
        ('earthquakes', 'Earthquakes'),
        ('seaIce', 'Sea Ice'),
        ('drought', 'Drought'),
        ('dustHaze', 'Dust and Haze'),
        ('landslides', 'Landslides'),
        ('manmade', 'Manmade'),
        ('snow', 'Snow'),
        ('temperatureExtremes', 'Temperature Extremes'),
        ('waterColor', 'Water Color'),
        ('algae', 'Algae')
    ]
    
    for slug, label in categories:
        cursor.execute('''
            INSERT OR IGNORE INTO categories (slug, label)
            VALUES (?, ?)
        ''', (slug, label))
    
    print(f"✅ Seeded {len(categories)} categories")

# Database helper functions

def add_to_watchlist(eonet_id):
    """
    Fetch an event from NASA and save it to the watchlist
    Returns True if successful, False if already exists or error
    """
    # First, check if already in watchlist
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM watched_events WHERE eonet_id = ?', (eonet_id,))
    existing = cursor.fetchone()
    
    if existing:
        conn.close()
        return False  # Already in watchlist
    
    # Fetch from API
    event_data = EventFetcher.fetch_event(eonet_id)
    
    if not event_data:
        conn.close()
        return False  # Could not fetch event
    
    # Save to database
    cursor.execute('''
        INSERT INTO watched_events (
            eonet_id, title, category, status, latitude, longitude,
            event_date, magnitude, mag_unit, source_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        event_data.get_eonet_id(),
        event_data.title,
        event_data.category,
        event_data.status,
        event_data.latitude,
        event_data.longitude,
        event_data.event_date,
        event_data.magnitude,
        event_data.mag_unit,
        event_data.source_url
    ))
    
    conn.commit()
    conn.close()
    return True

def remove_from_watchlist(eonet_id):
    """
    Remove an event from the watchlist
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM watched_events WHERE eonet_id = ?', (eonet_id,))
    deleted = cursor.rowcount > 0
    
    conn.commit()
    conn.close()
    return deleted

def get_watchlist():
    """
    Get all events from the watchlist
    Returns a list of WatchedEvent objects
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM watched_events
        ORDER BY saved_at DESC
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    # Convert database rows to WatchedEvent objects
    events = []
    for row in rows:
        event = WatchedEvent(
            eonet_id=row['eonet_id'],
            title=row['title'],
            category=row['category'],
            status=row['status'],
            latitude=row['latitude'],
            longitude=row['longitude'],
            event_date=row['event_date'],
            magnitude=row['magnitude'],
            mag_unit=row['mag_unit'],
            source_url=row['source_url'],
            note=row['note'] or '',
            alert_active=bool(row['alert_active'])
        )
        # Add the database ID (for operations)
        event.db_id = row['id']
        events.append(event)
    
    return events


def get_watchlist_paginated(page=1, per_page=10):
    """
    Get a paginated list of watched events from the database
    Uses SQL LIMIT and OFFSET for pagination
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Calculate OFFSET
    offset = (page - 1) * per_page
    
    # Get total count (for pagination info)
    cursor.execute('SELECT COUNT(*) as total FROM watched_events')
    total = cursor.fetchone()['total']
    
    # Get paginated events with LIMIT and OFFSET
    cursor.execute('''
        SELECT * FROM watched_events
        ORDER BY saved_at DESC
        LIMIT ? OFFSET ?
    ''', (per_page, offset))
    
    rows = cursor.fetchall()
    conn.close()
    
    # Convert to WatchedEvent objects
    events = []
    for row in rows:
        event = WatchedEvent(
            eonet_id=row['eonet_id'],
            title=row['title'],
            category=row['category'],
            status=row['status'],
            latitude=row['latitude'],
            longitude=row['longitude'],
            event_date=row['event_date'],
            magnitude=row['magnitude'],
            mag_unit=row['mag_unit'],
            source_url=row['source_url'],
            note=row['note'] or '',
            alert_active=bool(row['alert_active'])
        )
        event.db_id = row['id']
        event.saved_at = row['saved_at']
        events.append(event)
    
    # Calculate total pages
    total_pages = (total + per_page - 1) // per_page
    
    return {
        'events': events,
        'total': total,
        'total_pages': total_pages,
        'page': page,
        'per_page': per_page
    }

def get_watchlist_count():
    """
    Get the number of events in the watchlist
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) as count FROM watched_events')
    count = cursor.fetchone()['count']
    conn.close()
    
    return count

def update_note(eonet_id, note):
    """
    Update the note for a watched event
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE watched_events
        SET note = ?
        WHERE eonet_id = ?
    ''', (note, eonet_id))
    
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated

def toggle_alert(eonet_id):
    """
    Toggle the alert_active status for a watched event
    Returns the new status (True/False)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get current status
    cursor.execute('SELECT alert_active FROM watched_events WHERE eonet_id = ?', (eonet_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return False
    
    # Toggle
    new_status = 0 if row['alert_active'] else 1
    cursor.execute('''
        UPDATE watched_events
        SET alert_active = ?
        WHERE eonet_id = ?
    ''', (new_status, eonet_id))
    
    conn.commit()
    conn.close()
    return bool(new_status)

def log_search(query):
    """
    Log a search query to the search_log table
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO search_log (query_text)
        VALUES (?)
    ''', (query,))
    
    conn.commit()
    conn.close()

def get_categories():
    """
    Get all categories from the database
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT slug, label FROM categories ORDER BY label')
    categories = cursor.fetchall()
    conn.close()
    
    return [dict(category) for category in categories]


def get_stats():
    """
    Get statistics about the watchlist
    Returns a dictionary with various stats
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    # Total events
    cursor.execute('SELECT COUNT(*) as total FROM watched_events')
    stats['total'] = cursor.fetchone()['total']
    
    # Open vs Closed
    cursor.execute('''
        SELECT status, COUNT(*) as count 
        FROM watched_events 
        GROUP BY status
    ''')
    stats['by_status'] = {row['status']: row['count'] for row in cursor.fetchall()}
    
    # By category
    cursor.execute('''
        SELECT category, COUNT(*) as count 
        FROM watched_events 
        GROUP BY category
        ORDER BY count DESC
    ''')
    stats['by_category'] = {row['category']: row['count'] for row in cursor.fetchall()}
    
    # With alerts
    cursor.execute('''
        SELECT COUNT(*) as count 
        FROM watched_events 
        WHERE alert_active = 1
    ''')
    stats['with_alerts'] = cursor.fetchone()['count']
    
    # With notes
    cursor.execute('''
        SELECT COUNT(*) as count 
        FROM watched_events 
        WHERE note != '' AND note IS NOT NULL
    ''')
    stats['with_notes'] = cursor.fetchone()['count']
    
    # Most recent saved
    cursor.execute('''
        SELECT title, saved_at 
        FROM watched_events 
        ORDER BY saved_at DESC 
        LIMIT 1
    ''')
    recent = cursor.fetchone()
    stats['most_recent'] = dict(recent) if recent else None
    
    conn.close()
    return stats



# Create the Flask application
app = Flask(__name__)

# Set a secret key for flash messages
app.secret_key = 'This_is_my_final_project_for_programming_1_course_SRH'

# Initialize the database
# This runs when the app starts
init_db()

@app.route('/')
def home():
    """
    Home page - redirects to browse page
    """
    return render_template('home.html')



# ========================================
# BROWSE ROUTES
# ========================================

@app.route('/browse')
def browse():
    """
    Browse page - shows live events from NASA with filters and pagination
    """

    # Get query parameters
    category_filter = request.args.get('category', '')
    status_filter = request.args.get('status', 'all')
    days_filter = request.args.get('days', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    try:
        # Fetch events from NASA based on status filter and days
        if status_filter == 'all':
            all_events = EventFetcher.fetch_events(status='all', days=days_filter, limit=200)
        else:
            all_events = EventFetcher.fetch_events(status=status_filter, days=days_filter, limit=200)

        # Additional status filter (for safety)
        if status_filter and status_filter != 'all':
            all_events = [e for e in all_events if e.status.lower() == status_filter.lower()]
        
        # --- Category Filter ---
        if category_filter:
            # Get the category label from the slug
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT label FROM categories WHERE slug = ?', (category_filter,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                category_label = result['label']
                # Filter by the full category name (case-insensitive)
                all_events = [e for e in all_events if e.category.lower() == category_label.lower()]
            else:
                # Fallback: try matching by slug directly
                all_events = [e for e in all_events if e.category.lower() == category_filter.lower()]
        
        # --- Pagination ---
        total_events = len(all_events)
        total_pages = (total_events + per_page - 1) // per_page
        
        if page < 1:
            page = 1
        if page > total_pages and total_pages > 0:
            page = total_pages
        
        start = (page - 1) * per_page
        end = start + per_page
        page_events = all_events[start:end]
        
        # Get categories for filter dropdown
        categories = get_categories()

        # Get IDs of events already in watchlist (for visual marking)
        watchlist_ids = [e.get_eonet_id() for e in get_watchlist()]
        
        return render_template(
            'browse.html',
            events=page_events,
            total_events=total_events,
            page=page,
            total_pages=total_pages,
            per_page=per_page,
            categories=categories,
            category_filter=category_filter,
            status_filter=status_filter,
            days_filter=days_filter,
            watchlist_ids=watchlist_ids,
            error=error_message if 'error_message' in locals() else None
        )
        
    except Exception as e:
        error_message = f"Unable to fetch events: {str(e)}"
        return render_template(
            'browse.html',
            events=[],
            total_events=0,
            page=1,
            total_pages=0,
            per_page=per_page,
            categories=[],
            category_filter='',
            status_filter='open',
            error=error_message
        )
    
        

# ========================================
# WATCHLIST ROUTES
# ========================================

@app.route('/watch')
def watchlist():
    """
    Display the user's watchlist with search, filter, sort, and pagination
    """
    # Get query parameters
    search_query = request.args.get('search', '').strip()
    category_filter = request.args.get('category', '')
    status_filter = request.args.get('status', '')
    sort_by = request.args.get('sort', 'saved_at_desc')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Get all watched events (for filtering)
    all_events = get_watchlist()
    
    # --- SEARCH ---
    if search_query:
        search_lower = search_query.lower()
        all_events = [
            e for e in all_events 
            if search_lower in e.title.lower() 
            or search_lower in e.category.lower()
        ]
        if search_query:
            log_search(search_query)
    
    # --- FILTERS ---
    if category_filter:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT label FROM categories WHERE slug = ?', (category_filter,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            category_label = result['label']
            all_events = [e for e in all_events if e.category == category_label]
        else:
            all_events = [e for e in all_events if e.category.lower() == category_filter.lower()]
    
    if status_filter == 'has_note':
        all_events = [e for e in all_events if e.note and e.note.strip()]
    elif status_filter == 'no_note':
        all_events = [e for e in all_events if not e.note or not e.note.strip()]
    elif status_filter == 'alert_on':
        all_events = [e for e in all_events if e.alert_active is True]
    elif status_filter == 'alert_off':
        all_events = [e for e in all_events if e.alert_active is False]
    
    # --- SORT ---
    if sort_by == 'title_asc':
        all_events.sort(key=lambda e: e.title.lower())
    elif sort_by == 'title_desc':
        all_events.sort(key=lambda e: e.title.lower(), reverse=True)
    elif sort_by == 'date_asc':
        all_events.sort(key=lambda e: e.event_date or '')
    elif sort_by == 'date_desc':
        all_events.sort(key=lambda e: e.event_date or '', reverse=True)
    elif sort_by == 'status_asc':
        all_events.sort(key=lambda e: e.status.lower())
    elif sort_by == 'status_desc':
        all_events.sort(key=lambda e: e.status.lower(), reverse=True)
    elif sort_by == 'saved_at_asc':
        all_events.sort(key=lambda e: getattr(e, 'saved_at', ''))
    # Default: saved_at_desc (newest first)
    
    # --- PAGINATION ---
    total = len(all_events)
    total_pages = (total + per_page - 1) // per_page
    
    if page < 1:
        page = 1
    if page > total_pages and total_pages > 0:
        page = total_pages
    
    start = (page - 1) * per_page
    end = start + per_page
    page_events = all_events[start:end]
    
    # Get categories for filter dropdown
    categories = get_categories()
    
    return render_template(
        'watchlist.html',
        events=page_events,
        count=total,
        page=page,
        total_pages=total_pages,
        per_page=per_page,
        categories=categories,
        search_query=search_query,
        category_filter=category_filter,
        status_filter=status_filter,
        sort_by=sort_by
    )

@app.route('/watch/add/<eonet_id>', methods=['POST'])
def add_to_watchlist_route(eonet_id):
    """
    Add an event to the watchlist
    Redirects back to the previous page
    """
    success = add_to_watchlist(eonet_id)
    
    if success:
        flash('✅ Event added to your watchlist!', 'success')
    else:
        flash('⚠️ Event is already in your watchlist or could not be fetched.', 'warning')
    
    # Redirect back to the page they came from
    return redirect(request.referrer or url_for('watchlist'))

@app.route('/watch/remove/<eonet_id>', methods=['POST'])
def remove_from_watchlist_route(eonet_id):
    """
    Remove an event from the watchlist
    """
    success = remove_from_watchlist(eonet_id)
    
    if success:
        flash('🗑️ Event removed from watchlist', 'success')
    else:
        flash('⚠️ Event not found in watchlist', 'warning')
    
    return redirect(url_for('watchlist'))

@app.route('/watch/note/<eonet_id>', methods=['GET', 'POST'])
def edit_note(eonet_id):
    """
    Edit the note for a watched event
    GET: Show the edit form
    POST: Save the note
    """
    if request.method == 'POST':
        note = request.form.get('note', '')
        success = update_note(eonet_id, note)
        
        if success:
            flash('📝 Note updated successfully!', 'success')
        else:
            flash('⚠️ Could not update note', 'warning')
        
        return redirect(url_for('watchlist'))
    
    # GET - show the form
    events = get_watchlist()
    event = next((e for e in events if e.get_eonet_id() == eonet_id), None)
    
    if not event:
        flash('⚠️ Event not found in watchlist', 'warning')
        return redirect(url_for('watchlist'))
    
    return render_template('edit_note.html', event=event)

@app.route('/watch/toggle/<eonet_id>', methods=['POST'])
def toggle_alert_route(eonet_id):
    """
    Toggle alert status for a watched event
    """
    new_status = toggle_alert(eonet_id)
    
    if new_status is not False:
        status_text = 'activated' if new_status else 'deactivated'
        flash(f'🔔 Alert {status_text} for this event', 'success')
    else:
        flash('⚠️ Could not toggle alert', 'warning')
    
    return redirect(url_for('watchlist'))


def get_categories():
    """Get all categories from the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT slug, label FROM categories ORDER BY label')
    categories = cursor.fetchall()
    conn.close()
    return [dict(cat) for cat in categories]

def log_search(query):
    """Log a search query to the search_log table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO search_log (query_text) VALUES (?)', (query,))
    conn.commit()
    conn.close()

@app.route('/watchlist/export')
def export_watchlist():
    """
    Export the watchlist as a CSV file
    """
    import csv
    from io import StringIO
    
    # Get all watched events
    events = get_watchlist()
    
    # Create a string buffer to write CSV data
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header row
    writer.writerow([
        'ID',
        'Title',
        'Category',
        'Status',
        'Latitude',
        'Longitude',
        'Event Date',
        'Magnitude',
        'Magnitude Unit',
        'Note',
        'Alert Active',
        'Saved At'
    ])
    
    # Write data rows
    for event in events:
        writer.writerow([
            event.get_eonet_id(),
            event.title,
            event.category,
            event.status,
            event.latitude,
            event.longitude,
            event.event_date,
            event.magnitude or '',
            event.mag_unit or '',
            event.note,
            'Yes' if event.alert_active else 'No',
            getattr(event, 'saved_at', '')
        ])
    
    # Create response with CSV content
    csv_content = output.getvalue()
    output.close()
    
    # Return as a downloadable file
    return Response(
        csv_content,
        mimetype='text/csv',
        headers={
            'Content-Disposition': 'attachment; filename=events_export.csv'
        }
    )



# ========================================
# STATISTICS ROUTES
# ========================================

@app.route('/stats')
def stats():
    """
    Display statistics about the watchlist
    """
    stats_data = get_stats()
    search_history = get_search_history()  # Add this line
    return render_template('stats.html', stats=stats_data, search_history=search_history)

@app.route('/event/<eonet_id>')
def event_detail(eonet_id):
    """
    Show detailed information about a single event
    """
    try:
        event = EventFetcher.fetch_event(eonet_id)
        if event:
            return render_template('event_detail.html', event=event)
        else:
            flash('Event not found', 'error')
            return redirect(url_for('browse'))
    except Exception as e:
        flash(f'Error fetching event: {str(e)}', 'error')
        return redirect(url_for('browse'))
    
def get_search_history(limit=10):
    """Get the most recent search queries from search_log"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT query_text, searched_at 
        FROM search_log 
        ORDER BY searched_at DESC 
        LIMIT ?
    ''', (limit,))
    history = cursor.fetchall()
    conn.close()
    return [dict(row) for row in history]


# This runs the app when you execute the file directly
if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)