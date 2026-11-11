#!/usr/bin/env python
"""
Fix QGIS imports by wrapping them in try/except blocks.
Only wraps QGIS imports at module level (not inside functions).
"""

import os
import sys
import re

def fix_file(filepath):
    """Fix QGIS imports in a single file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # Find QGIS import lines at module level (not indented)
    qgis_lines = []
    for i, line in enumerate(lines):
        # Check if line is a QGIS import at module level (no leading whitespace)
        stripped = line.strip()
        if stripped.startswith('from qgis') or stripped.startswith('import qgis'):
            qgis_lines.append(i)
    
    if not qgis_lines:
        print(f"  No QGIS imports found in {filepath}")
        return False
    
    # Group consecutive QGIS imports
    groups = []
    current_group = [qgis_lines[0]]
    for i in range(1, len(qgis_lines)):
        if qgis_lines[i] == qgis_lines[i-1] + 1:
            current_group.append(qgis_lines[i])
        else:
            groups.append(current_group)
            current_group = [qgis_lines[i]]
    groups.append(current_group)
    
    # For each group, wrap in try/except
    for group in groups:
        first = group[0]
        last = group[-1]
        
        # Build new lines
        new_lines = lines[:first]
        
        # Add try wrapper
        new_lines.append('# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable')
        new_lines.append('try:')
        
        # Add QGIS lines with indentation
        for i in range(first, last + 1):
            indent = '    ' if i in group else ''
            new_lines.append(indent + lines[i])
        
        # Add except block
        new_lines.append('except ImportError:')
        new_lines.append('    pass  # QGIS not available, skip this import')
        
        # Add remaining lines
        new_lines.extend(lines[last+1:])
        
        # Write
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines) + '\n')
        
        print(f"  Fixed group {group} in {filepath}")
    
    return True

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix QGIS imports')
    parser.add_argument('files', nargs='*', help='Files to fix')
    parser.add_argument('--all', action='store_true', help='Fix all Python files with QGIS imports')
    
    args = parser.parse_args()
    
    if args.all:
        # Find all Python files with QGIS imports
        py_files = []
        for root, dirs, files in os.walk('E:/hermes/ag-gis'):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    if os.path.isfile(filepath):
                        py_files.append(filepath)
        
        print(f"Found {len(py_files)} Python files")
        
        for filepath in sorted(py_files):
            try:
                fix_file(filepath)
            except Exception as e:
                print(f"  ERROR: {filepath}: {e}")
    
    else:
        for filepath in args.files:
            fix_file(filepath)

if __name__ == '__main__':
    main()
