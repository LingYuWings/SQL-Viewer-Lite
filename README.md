# SQL-Viewer Lite

A lightweight, modern MySQL database client built with Python and PyQt5. Browse tables, run queries, and export data with a clean, responsive GUI.

## Features

- **Secure Connections** — Save and manage multiple MySQL connection profiles with AES-encrypted password storage
- **Table Browser** — Tree-view navigation of databases and tables with emoji indicators
- **Virtual Scroll** — Smooth browsing of large datasets (100K+ rows) without performance degradation
- **SQL Editor** — Execute custom queries with syntax highlighting and real-time execution
- **Data Export** — Export query results to CSV or JSON formats
- **Smart Filtering** — Column-level filtering with multiple operators (=, >, <, LIKE, etc.)
- **Dark & Light Themes** — Switchable themes for comfortable viewing in any environment
- **Bilingual UI** — English and Chinese interface with runtime language switching
- **Keyboard Shortcuts** — Efficient navigation with customizable shortcuts (Ctrl+E execute, Ctrl+R refresh, Ctrl+F filter, Ctrl+D export)
- **Connection Pool** — Built-in connection pooling for efficient database resource management
- **Multi-Connection** — Manage multiple database connections simultaneously (planned)
- **SSH Tunnel** — Secure connections through SSH tunneling (planned)

## Screenshots

> _Screenshots coming soon_

## Requirements

- Python 3.8+
- MySQL 5.7+ or MariaDB 10.3+

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/sql-viewer-lite.git
cd sql-viewer-lite
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
python main.py
```

## Project Structure

```
sql-viewer-lite/
├── main.py                          # Application entry point
├── requirements.txt                 # Python dependencies
├── pytest.ini                       # Test configuration
├── sql_viewer_lite/
│   ├── __init__.py
│   ├── app.py                       # Application initialization
│   ├── models/
│   │   └── connection.py            # Connection configuration models
│   ├── core/
│   │   ├── db_connection.py         # Database connection management
│   │   ├── db_worker.py             # Background query execution
│   │   ├── connection_pool.py       # Connection pooling
│   │   └── ssh_tunnel.py            # SSH tunnel support
│   ├── ui/
│   │   ├── login_window.py          # Connection login dialog
│   │   ├── main_window.py           # Main application window
│   │   ├── table_view.py            # Virtual scroll table view
│   │   ├── filter_panel.py          # Column filter controls
│   │   ├── theme_manager.py         # Theme switching
│   │   └── shortcuts.py             # Keyboard shortcut management
│   ├── utils/
│   │   ├── config_manager.py        # Configuration persistence
│   │   ├── encryption.py            # AES password encryption
│   │   └── i18n.py                  # Internationalization
│   └── tests/
│       ├── test_connection.py       # Connection tests
│       ├── test_db_connection.py    # Database connection tests
│       └── test_config_manager.py   # Config manager tests
└── .claude/                         # Claude Code configuration
```

## Usage

### Connecting to a Database

1. Launch the application with `python main.py`
2. Enter your MySQL connection details (host, port, username, password)
3. Optionally save the connection for future use
4. Click **Login** to connect

### Browsing Tables

- Expand the database tree in the left panel to view tables
- Click a table to view its structure and data
- Use the column headers to sort data

### Running Queries

- Type your SQL query in the editor panel
- Press **Ctrl+Enter** or click **Execute** to run
- Results appear in the table view below

### Exporting Data

- Right-click on query results or use **Ctrl+D**
- Select export format (CSV or JSON)
- Choose save location

## Configuration

### Theme

Switch between light and dark themes using the theme toggle in the toolbar or via **Ctrl+T**.

### Language

Switch between English and Chinese using **Ctrl+L** or the language menu.

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+E` | Execute query |
| `Ctrl+R` | Refresh current view |
| `Ctrl+F` | Open filter panel |
| `Ctrl+D` | Export data |
| `Ctrl+T` | Toggle theme |
| `Ctrl+L` | Toggle language |
| `Ctrl+N` | New connection |
| `Ctrl+Q` | Quit |

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=sql_viewer_lite --cov-report=html

# Run specific test file
pytest sql_viewer_lite/tests/test_connection.py
```

## Tech Stack

- **GUI**: PyQt5
- **Database**: PyMySQL
- **Encryption**: PyCryptodome (AES)
- **SSH**: Paramiko
- **Testing**: pytest

## Roadmap

- [x] Basic MySQL connection and table browsing
- [x] Virtual scroll for large datasets
- [x] Dark/Light theme support
- [x] Bilingual UI (EN/CN)
- [x] Data export (CSV/JSON)
- [ ] SSH tunnel support
- [ ] Multi-connection management
- [ ] Query history
- [ ] Table structure editor
- [ ] Data import (CSV)
- [ ] PostgreSQL support
- [ ] SQLite support

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [PyQt5](https://www.riverbankcomputing.com/software/pyqt/)
- Inspired by popular database management tools
- Developed with assistance from Claude Code
