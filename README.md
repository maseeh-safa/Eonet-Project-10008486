# 🌍 NASA Natural Events Tracker

A Flask web application that tracks real-time natural events using NASA's EONET (Earth Observatory Natural Event Tracker) API. Users can browse live events, save them to a personal watchlist, add notes, set alerts, and view statistics—all in a clean, professional interface.

---

## 🚀 Features

- **Browse Live Events** – View real-time natural events from NASA with filters (category, status, days) and pagination.
- **Personal Watchlist** – Save events, add personal notes, and enable alerts.
- **Search & Filter** – Search by title/category, filter by category or note/alert status, and sort by date, title, or status.
- **Statistics** – View summary counts, category breakdown with a visual bar chart, and recent search history.
- **CSV Export** – Export your entire watchlist as a CSV file.
- **3D Earth Visualization** – Interactive 3D globe on the home page showing event locations.
- **Responsive Design** – Works on desktop, tablet, and mobile devices.

---

## 🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| Python 3.x | Backend logic |
| Flask | Web framework |
| SQLite | Local database |
| NASA EONET API | Live event data |
| HTML/CSS | Frontend styling |
| Three.js | 3D Earth rendering |

---

## 📁 Project Structure

```
eonet_project/
├── app.py                 # Flask routes, database helpers
├── models.py              # OOP classes (NaturalEvent, WatchedEvent, EventFetcher)
├── templates/
│   ├── base.html          # Base template with navigation
│   ├── home.html          # Home page with 3D Earth
│   ├── browse.html        # Browse events with filters & pagination
│   ├── watchlist.html     # Watchlist with search/filter/sort
│   ├── stats.html         # Statistics with bar chart & search history
│   ├── event_detail.html  # Single event details
│   ├── edit_note.html     # Edit note form
│   └── earth_component.html # 3D Earth component
├── static/
│   ├── style.css          # All custom styles
│   └── images/
│       └── logo.png       # Logo (AI-generated)
├── events.db              # SQLite database (auto-created)
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

---

## 📦 Installation & Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd eonet_project
```

### 2. Create and Activate a Virtual Environment

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
python app.py
```

### 5. Open in Browser

Navigate to: `http://127.0.0.1:5000`

---

## 📋 Dependencies (requirements.txt)

```
flask
requests
```

To generate your own `requirements.txt`:
```bash
pip freeze > requirements.txt
```

---

## 🧱 OOP Design

The application uses object-oriented programming to model events and API communication.

### `NaturalEvent` (Base Class)

Represents a single natural event fetched from NASA's EONET API.

**Attributes:**
- `_eonet_id` – Unique event ID (encapsulated with getter)
- `title`, `category`, `status`, `latitude`, `longitude`, `event_date`
- `magnitude`, `mag_unit`, `source_url` (optional)

**Methods:**
- `is_active()` – Returns `True` if status is "open"
- `summary()` – Returns a descriptive string with category, title, and status
- `get_eonet_id()` – Getter for the private `_eonet_id`

---

### `WatchedEvent` (Inherits from `NaturalEvent`)

Extends `NaturalEvent` with watchlist-specific features.

**Additional Attributes:**
- `note` – Personal note (string, default empty)
- `alert_active` – Alert status (boolean, default `False`)

**Methods:**
- `toggle_alert()` – Flips `alert_active` and returns new value
- `summary()` – Extends parent summary to include note and alert state

---

### `EventFetcher` (Utility Class)

Handles all communication with NASA's EONET API. Wraps all `requests` calls so Flask routes do not call `requests` directly.

**Methods:**
- `fetch_events(status, category, days, limit)` – Returns a list of `NaturalEvent` objects
- `fetch_event(eonet_id)` – Returns a single `NaturalEvent` object
- `_parse_event(event_data)` – Internal helper to parse API JSON into `NaturalEvent`

---

## 🗄️ Database Schema

The SQLite database is auto-created on first run with three tables:

### `watched_events`
Stores events saved to the watchlist.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `eonet_id` | TEXT | Unique NASA event ID |
| `title` | TEXT | Event title |
| `category` | TEXT | Event category |
| `status` | TEXT | "open" or "closed" |
| `latitude` | REAL | Latitude coordinate |
| `longitude` | REAL | Longitude coordinate |
| `event_date` | TEXT | Event date (YYYY-MM-DD) |
| `magnitude` | REAL | Magnitude value (optional) |
| `mag_unit` | TEXT | Magnitude unit (optional) |
| `source_url` | TEXT | Source URL |
| `note` | TEXT | Personal note (default empty) |
| `alert_active` | INTEGER | 0 or 1 (boolean) |
| `saved_at` | TEXT | Timestamp of save |

### `categories`
Stores event categories for filter dropdowns.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `slug` | TEXT | URL-friendly category name |
| `label` | TEXT | Display name |

### `search_log`
Tracks search queries for the statistics page.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `query_text` | TEXT | Search query |
| `searched_at` | TEXT | Timestamp of search |

---

## 🌐 API Integration

The application uses NASA's EONET API v3:

- **Base URL:** `https://eonet.gsfc.nasa.gov/api/v3`
- **No API key required** – fully public
- **Endpoints Used:**
  - `/events` – List events with filters (status, category, days, limit)
  - `/events/{id}` – Single event details
  - `/categories` – Available event categories

---

## ⚠️ Known Limitations

| Limitation | Description |
|------------|-------------|
| **No User Authentication** | Single-user application; no login system |
| **API Rate Limits** | Limited by NASA's public API availability |
| **Event Limit** | Fetches up to 200 events per API call |
| **No Real-Time Updates** | Requires manual page refresh for new events |
| **Magnitude Data** | Not all events have magnitude values (handled gracefully) |

---

## 🤖 Academic Integrity & AI Disclosure

This project is an individual submission for the **Programming 1** course at SRH Berlin University of Applied Sciences.

In accordance with the course's academic integrity policy, I disclose the following:

- **AI-Assisted Development:** Generative AI tools (including ChatGPT/Claude) were used as a learning aid during the development of this project. These tools were used for:
  - Debugging and error resolution
  - Explaining complex concepts (e.g., Flask routing, SQLite, OOP)
  - Generating boilerplate code and suggesting best practices
  - Structuring the README documentation

- **AI-Generated Assets:** The project logo located at `static/images/logo.png` was generated using an AI image generation tool.

- **Student Understanding:** All code submitted is my own work. I have reviewed, tested, and fully understand every line of code in this project. I can explain the implementation choices and logic during the viva examination.

- **No Code Plagiarism:** No code was copied from other students or external repositories. All code was written by me, with AI assistance limited to guidance and explanation.

---

## 📝 Future Improvements

- [ ] User authentication and multi-user support
- [ ] Real-time WebSocket updates for new events
- [ ] Map integration (Leaflet) for event visualization
- [ ] Email notifications for alert-triggered events
- [ ] Export watchlist as JSON/PDF

---

## 🙏 Credits

- Data provided by [NASA EONET](https://eonet.gsfc.nasa.gov/)
- Built with [Flask](https://flask.palletsprojects.com/)
- 3D Earth powered by [Three.js](https://threejs.org/)

---

## 📄 License

This project was created for educational purposes as part of the **Programming 1** course at SRH Berlin University of Applied Sciences.

---

**Happy Tracking! 🚀🌍**