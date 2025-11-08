# ProMirrorGolf App Icon Integration Guide

## Overview

This guide explains how the ProMirrorGolf app icon is integrated into the application.

## File Location

The icon file should be placed at:
```
assets/icons/ProMirrorGolf_App_Icon.png
```

## Implementation Details

### 1. Icon Loading (`main.py`)

The icon is loaded in the `__init__` method of `ProMirrorGolfUI`:

```python
# Load and set app icon
self.app_icon = None
self.load_app_icon()
```

### 2. Icon Loading Method

The `load_app_icon()` method:
- Checks if the icon file exists at `assets/icons/ProMirrorGolf_App_Icon.png`
- Loads it using `tk.PhotoImage()` (keeps reference to prevent garbage collection)
- Sets it as the window icon using `root.iconphoto(True, self.app_icon)`
- Falls back to `.ico` format if available on Windows
- Logs warnings if the file is not found

**Code Snippet:**
```python
def load_app_icon(self):
    """Load the ProMirrorGolf app icon and set it as window icon"""
    try:
        icon_path = Path(__file__).parent / "assets" / "icons" / "ProMirrorGolf_App_Icon.png"
        
        if icon_path.exists():
            # Load icon using PhotoImage (keep reference to prevent garbage collection)
            self.app_icon = tk.PhotoImage(file=str(icon_path))
            
            # Set window icon (title bar icon)
            try:
                self.root.iconphoto(True, self.app_icon)
            except Exception as e:
                logger.warning(f"Could not set window icon: {e}")
                # Fallback: try iconbitmap if available
                try:
                    ico_path = icon_path.with_suffix('.ico')
                    if ico_path.exists():
                        self.root.iconbitmap(str(ico_path))
                except:
                    pass
            
            logger.info(f"App icon loaded successfully from {icon_path}")
        else:
            logger.warning(f"Icon file not found at {icon_path}")
    except Exception as e:
        logger.error(f"Error loading app icon: {e}", exc_info=True)
```

### 3. Icon Display in Header

The icon is displayed in the top-left corner of the header bar in `create_top_bar()`:

**Code Snippet:**
```python
# App icon (left side, before brand)
if self.app_icon:
    icon_frame = tk.Frame(top_bar, bg=self.colors['bg_main'])
    icon_frame.pack(side='left', padx=(32, 12), pady=8)
    
    # Display icon in header
    icon_label = tk.Label(
        icon_frame,
        image=self.app_icon,
        bg=self.colors['bg_main']
    )
    icon_label.pack()
    # Keep reference to prevent garbage collection
    icon_label.image = self.app_icon
```

### 4. Garbage Collection Prevention

**Important:** Tkinter's `PhotoImage` objects can be garbage collected if not properly referenced. To prevent this:

1. **Store in instance variable:** `self.app_icon = tk.PhotoImage(...)`
2. **Store in widget:** `icon_label.image = self.app_icon` (additional reference)

This ensures the icon remains in memory for the lifetime of the application.

## Adding the Icon File

### Step 1: Place the File

Move or copy `ProMirrorGolf_App_Icon.png` to:
```
assets/icons/ProMirrorGolf_App_Icon.png
```

### Step 2: Commit to Git

```bash
git add assets/icons/ProMirrorGolf_App_Icon.png
git commit -m "Add ProMirrorGolf app icon"
git push origin main
```

## File Requirements

- **Format:** PNG (recommended) or ICO (for Windows title bar)
- **Size:** 256x256 pixels or larger (will be scaled as needed)
- **Background:** Transparent or dark theme compatible
- **Name:** Must be exactly `ProMirrorGolf_App_Icon.png`

## Cross-Platform Support

- **Windows:** Uses `iconphoto()` for PNG, falls back to `iconbitmap()` for `.ico`
- **Linux:** Uses `iconphoto()` with PNG
- **macOS:** Uses `iconphoto()` with PNG

## Troubleshooting

### Icon Not Displaying

1. **Check file path:** Ensure the file is at `assets/icons/ProMirrorGolf_App_Icon.png`
2. **Check file name:** Must match exactly (case-sensitive)
3. **Check logs:** Look for warnings in `promirror.log`
4. **Check file format:** PNG format is required for Tkinter PhotoImage

### Icon Not in Title Bar

- On Windows, try using a `.ico` file instead of `.png`
- The code automatically falls back to `.ico` if available
- Ensure the file is named `ProMirrorGolf_App_Icon.ico` in the same directory

### Icon Disappears

- Ensure `self.app_icon` is stored as an instance variable
- Ensure `icon_label.image = self.app_icon` is set (prevents garbage collection)

## Testing

After adding the icon file:

1. Run the application: `python main.py`
2. Check the title bar for the icon
3. Check the top-left corner of the header for the icon
4. Check `promirror.log` for any warnings or errors

## Current Status

✅ Icon loading code implemented
✅ Window icon setting implemented
✅ Header display code implemented
✅ Garbage collection prevention implemented
⏳ Icon file needs to be added to `assets/icons/ProMirrorGolf_App_Icon.png`

Once the icon file is added, the application will automatically load and display it.

