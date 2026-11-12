
import ast
import sys

filepath = "E:\hermes\ag-gis\tools\auth_network_feasibility_test.py"

# Read the file
with open(filepath, 'r') as f:
    content = f.read()

# The problem is in lines 62-68 where the import statement is malformed
# Let's replace that section with a correct version

# Find the section to replace
import_section_start = content.find("# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable")
if import_section_start == -1:
    print("Could not find import section")
    sys.exit(1)

# Find where this section ends (next comment or blank line)
next_section = content.find("\n\n", import_section_start)
if next_section == -1:
    next_section = len(content)

section_to_replace = content[import_section_start:next_section]
print(f"Section to replace (first 500 chars):")
print(section_to_replace[:500])
print()

# Replace with correct version
correct_section = """# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable
    try:
        from qgis.core import (QgsApplication, QgsNetworkAccessManager,
                               QgsNetworkRequestParameters, Qgis)
    except ImportError:
        pass  # QGIS not available, skip this import
"""

print(f"Correct section:")
print(correct_section)
print()

# Do the replacement
new_content = content[:import_section_start] + correct_section + content[next_section:]

# Write the file
with open(filepath, 'w') as f:
    f.write(new_content)

print("File written successfully")
