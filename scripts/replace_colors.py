#!/usr/bin/env python3
"""
Automated color replacement script for ProMirrorGolf theme migration.

This script replaces hardcoded old theme colors with design constants from
app.design_constants, ensuring consistency across the codebase.

Usage:
    python scripts/replace_colors.py [--dry-run] [--file <path>] [--all]
    
Options:
    --dry-run    Show what would be changed without making changes
    --file       Process a specific file
    --all        Process all Python files in app/ directory
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


# Color mapping: old color -> (design_constant, context_hint)
COLOR_MAPPINGS = {
    # Backgrounds
    "#0f1116": ("COLORS.BACKGROUND_BASE", "background"),
    "#161b22": ("COLORS.BACKGROUND_SURFACE", "background"),
    "#1c2128": ("COLORS.BACKGROUND_SURFACE_ELEVATED", "background"),
    "#21262d": ("COLORS.BACKGROUND_SURFACE_ELEVATED", "background/border"),  # Context-dependent
    "#0d1117": ("COLORS.BACKGROUND_CONTROL", "background"),
    "#232323": ("COLORS.BACKGROUND_CONTROL", "background"),  # Already correct, but might be hardcoded
    
    # Borders
    "#30363d": ("COLORS.BORDER_HOVER", "border"),
    "#484f58": ("COLORS.BORDER_ACTIVE", "border"),  # Or TEXT_DISABLED, context-dependent
    
    # Text colors
    "#c9d1d9": ("COLORS.TEXT_PRIMARY", "text"),
    "#8b949e": ("COLORS.TEXT_SECONDARY", "text"),
    "#f0f3f6": ("COLORS.TEXT_PRIMARY", "text"),
    "#fafafa": ("COLORS.TEXT_PRIMARY", "text"),  # Already correct, but might be hardcoded
    
    # Accent (red - matching design system)
    "#ff4d4d": ("COLORS.ACCENT", "accent"),
    "#ff5c5c": ("COLORS.ACCENT_HOVER", "accent"),
    "#ff6b6b": ("COLORS.ACCENT_HOVER", "accent"),
    
    # Success (green)
    "#4ade80": ("COLORS.SUCCESS", "success"),
    "#238636": ("COLORS.SUCCESS", "success"),
    "#2ea043": ("COLORS.SUCCESS_HOVER", "success"),
    
    # Danger (red)
    "#da3633": ("COLORS.DANGER", "danger"),
    "#f85149": ("COLORS.DANGER_TEXT", "danger"),
    "#b62324": ("COLORS.DANGER_HOVER", "danger"),
    "#ff453a": ("COLORS.DANGER_TEXT", "danger"),
}

# Files to process (if --all is not used)
DEFAULT_FILES = [
    "app/widgets/shot_review_window.py",
    "app/widgets/main_window.py",
    "app/widgets/enhanced_table.py",
    "app/widgets/settings_dialog.py",
    "app/widgets/report_builder_dialog.py",
    "app/widgets/goals_dialog.py",
    "app/widgets/custom_field_editor.py",
    "app/widgets/thumbnail_grid.py",
    "app/main_window.py",
]


@dataclass
class Replacement:
    """Represents a single color replacement."""
    line_num: int
    old_text: str
    new_text: str
    old_color: str
    new_constant: str


class ColorReplacer:
    """Handles color replacement in Python files."""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.replacements: List[Replacement] = []
        self.files_processed = 0
        self.total_replacements = 0
        
    def find_color_patterns(self, content: str) -> List[Tuple[int, str, str]]:
        """
        Find all color patterns in content.
        Returns list of (line_number, matched_text, color_code).
        """
        matches = []
        lines = content.split('\n')
        
        # Pattern to find hex colors
        hex_color_pattern = r'#([0-9a-fA-F]{6})'
        
        for line_num, line in enumerate(lines, 1):
            # Skip lines that are comments
            stripped = line.strip()
            if stripped.startswith('#'):
                continue
            
            # Find all hex colors in the line
            for match in re.finditer(hex_color_pattern, line, re.IGNORECASE):
                color_code = '#' + match.group(1).lower()
                if color_code in COLOR_MAPPINGS:
                    matches.append((line_num, match.group(0), color_code))
        
        return matches
    
    def replace_color_in_line(self, line: str, color_code: str, constant: str) -> Tuple[str, bool]:
        """
        Replace a color code in a line with a design constant.
        Returns (new_line, was_replaced).
        """
        color_code_lower = color_code.lower()
        if color_code_lower not in COLOR_MAPPINGS:
            return line, False
        
        constant_name = COLOR_MAPPINGS[color_code_lower][0]
        original_line = line
        
        # Pattern 1: QColor("#ff4d4d") or QColor('#ff4d4d')
        if f'QColor("{color_code}")' in line:
            line = line.replace(f'QColor("{color_code}")', f'QColor({constant_name})')
            return line, True
        if f"QColor('{color_code}')" in line:
            line = line.replace(f"QColor('{color_code}')", f'QColor({constant_name})')
            return line, True
        
        # Pattern 2: In stylesheet strings
        # Check if this line contains setStyleSheet or similar
        is_stylesheet = 'setStyleSheet' in line or 'StyleSheet' in line or 'stylesheet' in line.lower()
        
        if color_code in line:
            # Check if it's already an f-string
            is_fstring = 'f"""' in line or "f'''" in line or ('f"' in line and line.count('"') >= 2) or ("f'" in line and line.count("'") >= 2)
            
            if is_fstring:
                # Already f-string, replace color with constant
                line = line.replace(f'"{color_code}"', f'{{{constant_name}}}')
                line = line.replace(f"'{color_code}'", f'{{{constant_name}}}')
                # Also handle colors not in quotes (in stylesheet properties)
                line = re.sub(rf'\b{re.escape(color_code)}\b', f'{{{constant_name}}}', line)
            elif is_stylesheet:
                # Need to convert to f-string
                # Find string delimiters
                if '"""' in line:
                    # Triple-quoted string
                    line = line.replace('"""', 'f"""', 1)
                    line = line.replace(f'"{color_code}"', f'{{{constant_name}}}')
                    line = line.replace(f"'{color_code}'", f'{{{constant_name}}}')
                    line = re.sub(rf'\b{re.escape(color_code)}\b', f'{{{constant_name}}}', line)
                elif "'''" in line:
                    line = line.replace("'''", "f'''", 1)
                    line = line.replace(f'"{color_code}"', f'{{{constant_name}}}')
                    line = line.replace(f"'{color_code}'", f'{{{constant_name}}}')
                    line = re.sub(rf'\b{re.escape(color_code)}\b', f'{{{constant_name}}}', line)
                elif '"' in line:
                    # Double-quoted string
                    # Find the opening quote (first " that's not escaped)
                    quote_pos = line.find('"')
                    if quote_pos >= 0:
                        line = line[:quote_pos+1] + 'f' + line[quote_pos+1:]
                        line = line.replace(f'"{color_code}"', f'{{{constant_name}}}')
                        line = re.sub(rf'\b{re.escape(color_code)}\b', f'{{{constant_name}}}', line)
                elif "'" in line:
                    # Single-quoted string
                    quote_pos = line.find("'")
                    if quote_pos >= 0:
                        line = line[:quote_pos+1] + 'f' + line[quote_pos+1:]
                        line = line.replace(f"'{color_code}'", f'{{{constant_name}}}')
                        line = re.sub(rf'\b{re.escape(color_code)}\b', f'{{{constant_name}}}', line)
            else:
                # Not a stylesheet, might be a regular string assignment
                # Just replace the color code
                line = line.replace(f'"{color_code}"', f'"{constant_name}"')
                line = line.replace(f"'{color_code}'", f"'{constant_name}'")
        
        return line, line != original_line
    
    def ensure_imports(self, content: str) -> str:
        """Ensure design_constants imports are present."""
        if 'from app.design_constants import' in content:
            # Check if COLORS is imported
            import_line = None
            for line in content.split('\n'):
                if 'from app.design_constants import' in line:
                    import_line = line
                    break
            
            if import_line and 'COLORS' not in import_line:
                # Add COLORS to imports
                if 'import' in import_line:
                    # Extract what's already imported
                    parts = import_line.split('import')
                    if len(parts) == 2:
                        existing = parts[1].strip()
                        new_import = f"{parts[0]}import COLORS, {existing}"
                        content = content.replace(import_line, new_import)
        else:
            # Add import at the top (after other imports)
            lines = content.split('\n')
            insert_pos = 0
            for i, line in enumerate(lines):
                if line.startswith('from ') or line.startswith('import '):
                    insert_pos = i + 1
                elif line.strip() and not line.startswith('#') and insert_pos > 0:
                    break
            
            if insert_pos > 0:
                lines.insert(insert_pos, 'from app.design_constants import COLORS')
                content = '\n'.join(lines)
        
        return content
    
    def process_file(self, file_path: Path) -> bool:
        """Process a single file and replace colors."""
        # Skip design_constants.py - it contains the actual color values
        if file_path.name == "design_constants.py":
            return False
            
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            print(f"[ERROR] Error reading {file_path}: {e}")
            return False
        
        original_content = content
        file_replacements: List[Replacement] = []
        
        # Find all color patterns
        matches = self.find_color_patterns(content)
        
        if not matches:
            return False
        
        # Process line by line
        lines = content.split('\n')
        modified_lines = []
        processed_lines = set()  # Track which lines we've already processed
        
        for line_num, line in enumerate(lines, 1):
            original_line = line
            
            # Check each match for this line
            for match_line_num, match_text, color_code in matches:
                if match_line_num == line_num and line_num not in processed_lines:
                    constant_name = COLOR_MAPPINGS[color_code.lower()][0]
                    new_line, was_replaced = self.replace_color_in_line(line, color_code, constant_name)
                    
                    if was_replaced:
                        line = new_line
                        processed_lines.add(line_num)
                        file_replacements.append(Replacement(
                            line_num=line_num,
                            old_text=original_line,
                            new_text=line,
                            old_color=color_code,
                            new_constant=constant_name
                        ))
            
            modified_lines.append(line)
        
        if not file_replacements:
            return False
        
        # Reconstruct content
        new_content = '\n'.join(modified_lines)
        
        # Ensure imports are present
        new_content = self.ensure_imports(new_content)
        
        # Report changes
        print(f"\n[FILE] {file_path}")
        print(f"   Found {len(file_replacements)} color replacements:")
        for rep in file_replacements[:5]:  # Show first 5
            print(f"   Line {rep.line_num}: {rep.old_color} -> {rep.new_constant}")
        if len(file_replacements) > 5:
            print(f"   ... and {len(file_replacements) - 5} more")
        
        # Apply changes
        if not self.dry_run:
            try:
                file_path.write_text(new_content, encoding='utf-8')
                print(f"   [OK] Updated file")
            except Exception as e:
                print(f"   [ERROR] Error writing file: {e}")
                return False
        else:
            print(f"   [DRY RUN] Would update file")
        
        self.replacements.extend(file_replacements)
        self.total_replacements += len(file_replacements)
        self.files_processed += 1
        return True
    
    def process_directory(self, directory: Path) -> None:
        """Process all Python files in a directory."""
        python_files = list(directory.rglob("*.py"))
        print(f"Found {len(python_files)} Python files in {directory}")
        
        for file_path in python_files:
            if self.process_file(file_path):
                self.files_processed += 1
    
    def print_summary(self) -> None:
        """Print summary of replacements."""
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"Files processed: {self.files_processed}")
        print(f"Total replacements: {self.total_replacements}")
        
        if self.dry_run:
            print("\n[DRY RUN MODE] No files were modified")
            print("Run without --dry-run to apply changes")
        else:
            print("\n[SUCCESS] Changes applied successfully")
        
        # Show color mapping statistics
        color_counts: Dict[str, int] = {}
        for rep in self.replacements:
            color_counts[rep.old_color] = color_counts.get(rep.old_color, 0) + 1
        
        if color_counts:
            print("\nColor replacement breakdown:")
            for color, count in sorted(color_counts.items(), key=lambda x: -x[1]):
                constant = COLOR_MAPPINGS[color.lower()][0]
                print(f"  {color} -> {constant}: {count} replacements")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Replace hardcoded colors with design constants"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes"
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Process a specific file"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all Python files in app/ directory"
    )
    
    args = parser.parse_args()
    
    replacer = ColorReplacer(dry_run=args.dry_run)
    
    if args.file:
        # Process single file
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"[ERROR] File not found: {file_path}")
            sys.exit(1)
        replacer.process_file(file_path)
    elif args.all:
        # Process all files in app/
        app_dir = Path("app")
        if not app_dir.exists():
            print(f"[ERROR] Directory not found: {app_dir}")
            sys.exit(1)
        replacer.process_directory(app_dir)
    else:
        # Process default files
        print("Processing default files...")
        for file_str in DEFAULT_FILES:
            file_path = Path(file_str)
            if file_path.exists():
                replacer.process_file(file_path)
            else:
                print(f"[WARNING] File not found: {file_path}")
    
    replacer.print_summary()


if __name__ == "__main__":
    main()

