import os

file_path = 'pages/2_Job_Generator.py'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Keep lines 1-592 (indices 0-591) and 789-end (indices 788-end)
# Line 593 (index 592) is the start of the duplicate block
# Line 788 (index 787) is the end of the duplicate block
new_lines = lines[:592] + lines[788:]

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"Successfully removed lines 593-788. New line count: {len(new_lines)}")
