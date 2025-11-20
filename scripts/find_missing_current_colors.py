#!/usr/bin/env python3
"""Find methods that use current_colors without get_current_colors() initialization."""

import re
from pathlib import Path

def find_issues_in_file(file_path: Path) -> list[tuple[int, str, str]]:
    """Find methods with current_colors usage but no get_current_colors()."""
    issues = []
    
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return issues
    
    lines = content.split('\n')
    
    # Find all method definitions
    method_pattern = re.compile(r'^\s+def\s+(\w+)\s*\(')
    current_colors_pattern = re.compile(r'current_colors\.')
    get_current_colors_pattern = re.compile(r'get_current_colors\s*\(')
    
    i = 0
    while i < len(lines):
        method_match = method_pattern.match(lines[i])
        if method_match:
            method_name = method_match.group(1)
            method_start = i
            method_end = i + 1
            
            # Find method end (next def or class at same or less indentation)
            indent_level = len(lines[i]) - len(lines[i].lstrip())
            j = i + 1
            while j < len(lines):
                line_stripped = lines[j].lstrip()
                if not line_stripped or line_stripped.startswith('#'):
                    j += 1
                    continue
                current_indent = len(lines[j]) - len(line_stripped)
                if current_indent <= indent_level and (line_stripped.startswith('def ') or line_stripped.startswith('class ')):
                    break
                j += 1
            method_end = j
            
            # Check if method uses current_colors
            method_body = '\n'.join(lines[method_start:method_end])
            if current_colors_pattern.search(method_body):
                # Check if get_current_colors() is called at the start (first 20 lines)
                method_start_lines = '\n'.join(lines[method_start:min(method_start + 20, method_end)])
                if not get_current_colors_pattern.search(method_start_lines):
                    # Check if it's inside an f-string (which is wrong)
                    if 'from app.design_constants import get_current_colors' in method_body:
                        # Check if it's inside an f-string
                        fstring_pattern = re.compile(r'f"""|f"|f\'')
                        in_fstring = False
                        for k in range(method_start, method_end):
                            if fstring_pattern.search(lines[k]):
                                in_fstring = True
                            if in_fstring and 'get_current_colors' in lines[k]:
                                issues.append((method_start + 1, method_name, "get_current_colors() inside f-string"))
                                break
                    else:
                        issues.append((method_start + 1, method_name, "Missing get_current_colors() initialization"))
        
        i += 1
    
    return issues

def main():
    """Main function."""
    widget_dir = Path("app/widgets")
    
    if not widget_dir.exists():
        print(f"Directory not found: {widget_dir}")
        return
    
    all_issues = []
    
    for file_path in sorted(widget_dir.glob("*.py")):
        issues = find_issues_in_file(file_path)
        if issues:
            all_issues.append((file_path, issues))
    
    if all_issues:
        print("Found issues:\n")
        for file_path, issues in all_issues:
            print(f"{file_path}:")
            for line_num, method_name, issue in issues:
                print(f"  Line {line_num} ({method_name}): {issue}")
            print()
    else:
        print("No issues found!")

if __name__ == "__main__":
    main()

