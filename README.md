# 🤖 AI-Powered Directory Management System

An intelligent file organization system that uses AI/NLP to automatically categorize and organize files in your directories.

## 🚀 Quick Start

### Web UI (Recommended)
```bash
pip install -r requirements.txt
python app.py
# Open http://localhost:5000 in your browser
```

### Legacy CLI Version
```bash
python directory.py
```

## 🎯 Features

- **Smart AI Categorization** - Uses MIME type detection, NLP analysis, and content analysis
- **Beautiful Web Interface** - Modern, responsive design with dark mode
- **Restore Capability** - Undo changes and restore files to original locations
- **Real-time Progress Tracking** - Live logs and progress updates
- **Customizable Categories** - Edit file categories on the fly
- **Duplicate Detection** - Optional MD5-based duplicate file skipping
- **Cross-Platform** - Works on Windows, macOS, and Linux

## 📁 How It Works

1. **Scan** - Analyzes all files in a directory
2. **Detect** - Uses multiple methods to identify file types:
   - MIME type detection (accurate)
   - File extension matching
   - Content analysis for text files
   - NLP keyword extraction
3. **Organize** - Moves files into category folders
4. **Log** - Keeps track of all movements for restoration

## 🎨 Default Categories

| Category | File Types |
|----------|-----------|
| Documents | PDF, DOCX, TXT, DOC |
| Images | JPG, PNG, GIF, WEBP |
| Media | MP4, MP3, WAV, AVI, MKV |
| Code | PY, JS, HTML, CPP, JAVA, TS |
| Archives | ZIP, RAR, 7Z, TAR, GZ |
| Uncategorized | Any unmatched files |

## 📖 Full Documentation

See [GETTING_STARTED.md](GETTING_STARTED.md) for detailed usage instructions, API documentation, and troubleshooting.

## 🛠️ Technology Stack

- **Backend**: Flask, Python
- **NLP**: NLTK (Natural Language Toolkit)
- **File Detection**: python-magic, PyPDF2
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Design**: Modern gradient UI with dark mode support

## 📋 Requirements

- Python 3.8+
- See `requirements.txt` for dependencies

## 🔒 The Smart Way to Organize

Instead of manually moving files, let AI do the work:

```
Before:
/Downloads/
  ├── report.pdf
  ├── photo.jpg
  ├── script.py
  ├── video.mp4
  └── archive.zip

After:
/Downloads/
  ├── Documents/ → report.pdf
  ├── Images/ → photo.jpg
  ├── Code/ → script.py
  ├── Media/ → video.mp4
  └── Archives/ → archive.zip
```

## 🎮 Interactive Features

✨ **Dark Mode** - Easy on the eyes  
⚡ **Real-time Logs** - See exactly what's happening  
📊 **Progress Bar** - Track organization progress  
🎯 **Quick Actions** - One-click organize or restore  
🔧 **Advanced Options** - Skip duplicates, clean empty folders  

## ⚙️ Configuration

Customize categories, keywords, and MIME types directly from the web UI. All changes are saved and applied immediately.

## 🐛 Troubleshooting

**Browse not working?** → Enter path directly or use quick path buttons  
**Files not organizing?** → Check permissions and edit categories  
**Want to undo?** → Click "Restore Files" to revert changes  

For more help, see [GETTING_STARTED.md](GETTING_STARTED.md#troubleshooting)

---

**Made with ❤️ using AI and Python**
