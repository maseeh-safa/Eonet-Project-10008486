# models.py
import requests
from datetime import datetime

class NaturalEvent:
    """Represents a natural event from NASA's EONET API"""
    
    def __init__(self, eonet_id, title, category, status, latitude, longitude, 
                 event_date, magnitude=None, mag_unit=None, source_url=None):
        """
        This is the constructor - it runs when we create a new event
        
        Parameters:
        - eonet_id: Unique ID from NASA (string)
        - title: Event title (string)
        - category: Type of event (string)
        - status: "open" or "closed" (string)
        - latitude: Latitude coordinate (float)
        - longitude: Longitude coordinate (float)
        - event_date: Date as string (YYYY-MM-DD)
        - magnitude: Optional number like 4.5 (float or None)
        - mag_unit: Optional unit like "MW" (string or None)
        - source_url: Optional link (string or None)
        """
        
        # Store all the data
        self._eonet_id = eonet_id  # Using _ to show it's "private"
        self.title = title
        self.category = category
        self.status = status
        self.latitude = latitude
        self.longitude = longitude
        self.event_date = event_date
        self.magnitude = magnitude
        self.mag_unit = mag_unit
        self.source_url = source_url
    
    # Getter method - demonstrates encapsulation!
    def get_eonet_id(self):
        """Returns the EONET ID - this is how we access the 'private' attribute"""
        return self._eonet_id
    
    def is_active(self):
        """
        Returns True if event is still 'open'
        Returns False if event is 'closed'
        """
        return self.status.lower() == "open"
    
    def summary(self):
        """
        Returns a descriptive string about the event
        Include: category, title, and status
        """
        return f"{self.category}: {self.title} ({self.status})"
    
    def __str__(self):
        """
        This is a special method that Python uses when you print an event
        Try it: print(my_event)
        """
        return self.summary()


class WatchedEvent(NaturalEvent):
    """
    WatchedEvent inherits from NaturalEvent
    Adds: note (personal notes) and alert_active (toggle alerts)
    """
    
    def __init__(self, eonet_id, title, category, status, latitude, longitude,
                 event_date, magnitude=None, mag_unit=None, source_url=None,
                 note="", alert_active=False):
        """
        Initialize a WatchedEvent
        
        First, call the parent (NaturalEvent) constructor with all the event data
        Then add the two new attributes
        """
        # Call the parent constructor
        super().__init__(eonet_id, title, category, status, latitude, longitude,
                        event_date, magnitude, mag_unit, source_url)
        
        # Add the new attributes specific to WatchedEvent
        self.note = note
        self.alert_active = alert_active
    
    def toggle_alert(self):
        """
        Flip the alert_active status
        Returns the new value (True or False)
        """
        self.alert_active = not self.alert_active
        return self.alert_active
    
    def summary(self):
        """
        Override (extend) the parent summary method
        Add note and alert state when present
        """
        # Get the parent summary
        base_summary = super().summary()
        
        # Add note if it exists
        if self.note:
            base_summary += f" - Note: {self.note}"
        
        # Add alert status if active
        if self.alert_active:
            base_summary += " ⚠️ ALERT ACTIVE"
        
        return base_summary

""

class EventFetcher:
    """
    Handles all communication with NASA's EONET API
    No API key required - it's public!
    """
    
    # Base URL for the API
    BASE_URL = "https://eonet.gsfc.nasa.gov/api/v3"
    
    @staticmethod
    def fetch_events(status="open", category=None, days=None, limit=20):
        """
        Fetch events from NASA's EONET API
        
        Parameters:
        - status: "open", "closed", or "all" (default: "open")
        - category: Filter by category slug (e.g., "wildfires")
        - days: Number of days to look back (e.g., 30)
        - limit: Max number of events to return (default: 20)
        
        Returns:
        - List of NaturalEvent objects
        """
        url = f"{EventFetcher.BASE_URL}/events"
        params = {"status": status}
        
        if category:
            params["category"] = category
        if days:
            params["days"] = days
        if limit:
            params["limit"] = limit
        
        try:
            print(f"🌐 Fetching events from: {url}")
            print(f"📋 Parameters: {params}")
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            events_data = data.get("events", [])
            
            print(f"✅ Found {len(events_data)} events")
            
            events = []
            for event_data in events_data:
                event = EventFetcher._parse_event(event_data)
                if event:
                    events.append(event)
            
            print(f"📦 Created {len(events)} NaturalEvent objects")
            return events
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching events: {e}")
            return []
    
    @staticmethod
    def fetch_event(eonet_id):
        """
        Fetch a single event by its ID
        
        Parameters:
        - eonet_id: The unique ID from NASA
        
        Returns:
        - A NaturalEvent object, or None if not found
        """
        url = f"{EventFetcher.BASE_URL}/events/{eonet_id}"
        
        try:
            print(f"🌐 Fetching event: {eonet_id}")
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse the JSON response
            data = response.json()
            
            # Handle both formats: direct or nested under 'event'
            event_data = data.get("event", data)
            
            return EventFetcher._parse_event(event_data)
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching event {eonet_id}: {e}")
            return None
    
    @staticmethod
    def _parse_event(event_data):
        """
        Helper method to parse raw API data into a NaturalEvent object
        """
        try:
            # Extract basic fields
            eonet_id = event_data.get("id", "")
            title = event_data.get("title", "Unknown Event")
            status = event_data.get("status", "closed")
            
            # If status is empty, default to "closed"
            if not status:
                status = "closed"
            
            # Extract category
            categories = event_data.get("categories", [])
            if categories:
                first_category = categories[0]
                if isinstance(first_category, dict):
                    category = first_category.get("title", "Unknown")
                else:
                    category = str(first_category)
            else:
                category = "Unknown"
            
            # Get geometry data (NASA uses 'geometry' singular!)
            latitude = 0.0
            longitude = 0.0
            event_date = ""
            magnitude = None
            mag_unit = None
            
            geometry_list = event_data.get("geometry", [])
            
            if geometry_list and len(geometry_list) > 0:
                # Get the first geometry
                geometry = geometry_list[0]
                
                # Extract coordinates
                coordinates = geometry.get("coordinates", [])
                
                # EONET uses [longitude, latitude] order!
                if len(coordinates) >= 2:
                    longitude = coordinates[0]   # First is longitude
                    latitude = coordinates[1]    # Second is latitude
                
                # Extract date
                date_str = geometry.get("date", "")
                if date_str:
                    event_date = date_str[:10]  # Just YYYY-MM-DD
                
                # Extract magnitude
                magnitude_val = geometry.get("magnitudeValue")
                if magnitude_val:
                    try:
                        magnitude = float(magnitude_val)
                        mag_unit = geometry.get("magnitudeUnit", "")
                    except (ValueError, TypeError):
                        magnitude = None
            
            # If no magnitude in geometry, try properties
            if magnitude is None:
                properties = event_data.get("properties", {})
                mag = properties.get("magnitude")
                if mag:
                    try:
                        magnitude = float(mag)
                        mag_unit = properties.get("magnitudeUnit", "")
                    except (ValueError, TypeError):
                        magnitude = None
            
            # Extract source URL
            sources = event_data.get("sources", [])
            source_url = None
            if sources:
                source_url = sources[0].get("url", "")
            
            # Create and return a NaturalEvent object
            return NaturalEvent(
                eonet_id=eonet_id,
                title=title,
                category=category,
                status=status,
                latitude=latitude,
                longitude=longitude,
                event_date=event_date,
                magnitude=magnitude,
                mag_unit=mag_unit,
                source_url=source_url
            )
            
        except Exception as e:
            print(f"⚠️ Error parsing event data: {e}")
            print(f"   Data: {event_data}")
            return None
    
    @staticmethod
    def get_categories():
        """Fetch all available categories from NASA"""
        url = f"{EventFetcher.BASE_URL}/categories"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("categories", [])
        except:
            return []

