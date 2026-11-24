"""Normalize quoted Windows paths only for CMD filesystem built-ins."""
import re

def normalize_cmd_paths(command):
    if not re.match(r'^\s*(?:ren|rename|copy|mkdir|md|move|dir|robocopy|xcopy)\s',command,re.I):return command
    return re.sub(r'"([A-Za-z]:/[^"\r\n]*)"',lambda match:'"'+match[1].replace('/',chr(92))+'"',command)
