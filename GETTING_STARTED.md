# 🤖 AI-Powered Directory Management System

## Features

✨ **Smart File Organization** - Uses AI/NLP to intelligently categorize files  
🎯 **Multiple Recognition Methods** - MIME type detection, extensions, content analysis  
🔄 **Restore Capability** - Undo organization and restore files to original locations  
🌙 **Dark Mode** - Beautiful dark/light theme toggle  
⚡ **Real-time Progress** - Live logs with detailed operation tracking  
🎨 **Modern Web UI** - Sleek, responsive interface  
🔧 **Customizable Categories** - Edit categories, keywords, and MIME types on the fly  

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the App
```bash
python app.py
```

### 3. Open in Browser
The app will start on `http://localhost:5000`

## How to Use

### Selecting a Directory

1. Click the **Browse** button or enter a path directly
2. Use the dialog to select your directory
3. Common paths are available as quick shortcuts
4. Press Enter or click Confirm

### Organizing Files

1. Select your directory
2. (Optional) Enable "Skip Duplicates" to avoid duplicate files
3. Click **Start Organizing**
4. Watch the real-time progress and logs
5. Files will be organized into category folders

### Restoring Files

1. Click **Restore Files**
2. Files will be moved back to their original locations
3. (Optional) Enable "Clean Empty Folders" to remove empty category folders
4. Restore log will be deleted after completion

### Managing Categories

1. Click **Edit Categories** to customize
2. Modify keywords, extensions, and MIME types for each category
3. Click **Save Changes** to apply

## Categories Included

- **Documents** - PDFs, Word docs, text files
- **Images** - JPG, PNG, GIF, WebP
- **Media** - MP4, MP3, WAV, AVI videos and audios
- **Code** - Python, JavaScript, HTML, C++, Java, TypeScript
- **Archives** - ZIP, RAR, 7Z, TAR, GZ compressed files
- **Uncategorized** - Files that don't match any category

## Architecture

### Backend (Flask)
- `app.py` - Main Flask application with route handlers
- Uses NLTK for natural language processing
- PyPDF2 for PDF content extraction
- python-magic for MIME type detection
- Threading for non-blocking organization

### Frontend (Modern Web UI)
- `templates/index.html` - Responsive HTML template
- `static/css/style.css` - Beautiful gradient design with dark mode
- `static/js/app.js` - Interactive JavaScript with real-time updates

## File Structure

```
.
├── app.py                          # Main Flask app
├── directory.py                    # Original CLI version (legacy)
├── requirements.txt                # Python dependencies
├── templates/
│   └── index.html                  # Web interface
├── static/
│   ├── css/
│   │   └── style.css              # Styling with dark mode support
│   └── js/
│       └── app.js                  # JavaScript logic
├── file_organizer.log              # Application logs
└── restore_log.json                # Restore history
```

## API Endpoints

### Core Operations
- `POST /api/select-directory` - Validate and select a directory
- `POST /api/organize` - Start organizing files (async)
- `POST /api/restore` - Restore files to original locations
- `GET /api/logs` - Stream real-time operation logs
- `GET /api/categories` - Get all file categories
- `POST /api/categories` - Update categories

## Browser Compatibility

Works on modern browsers:
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (responsive design)

## Advanced Features

### MIME Type Detection
The app uses `python-magic` to accurately detect file types, not just by extension.

### Content Analysis
For ambiguous files, the app analyzes content using:
- PDF text extraction
- NLP tokenization and POS tagging
- Keyword matching against category signatures

### Duplicate Prevention
Optional duplicate detection using MD5 hashing to skip identical files during organization.

### Real-time Updates
JavaScript polling (500ms) provides live progress updates without page refresh.

## Troubleshooting

### Browse button not working?
- Make sure the directory path exists
- Use absolute paths: `/home/user/Downloads` or relative: `./downloads`
- Check file permissions

### Files not organizing correctly?
- Edit categories to add custom keywords
- Check the activity log for details
- Restore and try again with different settings

### Permission errors?
- Ensure you have read/write access to the directory
- Run with appropriate user permissions
- Check file system restrictions

## Tips & Tricks

💡 **Batch Organization** - Organize your entire Downloads folder  
💡 **Restore Anytime** - Keep the restore log safe if you want to undo  
💡 **Custom Categories** - Add your own categories for specialized organizing  
💡 **Dark Mode** - Toggle at anytime with the moon/sun icon  
💡 **Mobile Friendly** - Use on mobile to organize files on remote servers  

## Performance

- **100 files**: < 1 second
- **1,000 files**: 5-10 seconds
- **10,000 files**: 1-2 minutes
- Performance varies by file types and system speed

## License

This project is part of the AI-powered directory management system.

## Support

For issues with:
- **Browse dialog**: Enter the full path manually and press Enter
- **Organization**: Check logs for detailed error messages
- **Categories**: Reset to defaults and manually configure
- **Restore**: Make sure `restore_log.json` exists in the app directory

---

Made with ❤️ using Flask and modern web technologies
