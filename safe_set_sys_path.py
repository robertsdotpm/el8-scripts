"""
Python3

This module is for safely setting the system PATH on Windows
which turns out to be rife with problems. Note that this isn't the same as
%path% which is a combination of the system path + the users path.

To get the path from batch: 
SET Key="HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment"
SET DIR=%~dp0%
FOR /F "usebackq tokens=2*" %%A IN (`REG QUERY %Key% /v PATH`) DO Set CurrPath=%%B
echo %CurrPath%

If calling this script from the command line like python3 script.py "%var%"
var will be evaluated and parsed as its value. You will need to use a batch
script and use setlocal enableDelayedExpansion with !"%var%"! to avoid
variable expansion. This is not an issue with the above fragment because
%CurrPath% gets evaluated to the system path value and any parameters inside
aren't evaluated a second time.
"""
import sys, re, winreg
from subprocess import check_output
cmd = lambda c: check_output(c, shell=True)

# For editing the SYSTEM path
REG_PATH = r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"

# Program takes 1 arg -- a list of paths to add to sys path.
if len(sys.argv) == 2:
    unclean_sys_path = sys.argv[1]
    unclean_sub_paths = unclean_sys_path.split(";")
    clean_sub_paths = []
    
    # Strip duplicate paths to keep PATH nice and clean.
    for sub_path in unclean_sub_paths:
        # Only interested in valid Windows paths.
        valid_path = r"[a-zA-Z0-9!@#%^&()_,.{}`~'\[\]\-\^\$ \\\/:%]"
        
        # Don't assume paths will all be neatly terminated.
        pattern    = r"^(" + valid_path + "+[;]?)*"
        pattern   += r"(" + valid_path + "+)+$"
        
        if re.match(pattern, sub_path) != None:
            if sub_path not in clean_sub_paths:
                clean_sub_paths.append(sub_path)
                
    # Recombine into a clean path.
    if len(clean_sub_paths):
        # Every path should end with ;.
        clean_sys_path = ";".join(clean_sub_paths) + ";"
        
        # Modify system path registry entry.
        registry_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
            REG_PATH, 0, winreg.KEY_WRITE)
        winreg.SetValueEx(registry_key, "Path", 0, winreg.REG_EXPAND_SZ, clean_sys_path)
        winreg.CloseKey(registry_key)
        
        """
        The windows setx /m command updates the system path on Windows.
        But it contains a 1024 byte char limit and truncates the path.
        It also sends a special message WM_SETTINGCHANGE to propagate
        environmental variable changes without a reboot. The work around
        is to create a dummy setx call that changes nothing to make
        it send this message to make our registry changes take effect.
        
        Source: https://superuser.com/questions/387619/overcoming-the-1024-character-limit-with-setx
        """
        cmd(r"SETX /M USERNAME %USERNAME%")
        
        """
        Finally, if one wishes to make the new path changes take effect in
        the CURRENT session (e.g. an already open command window or executing
        batch script) then one can install Chocolatey and call the
        refresh variables script:
        
        start /wait cmd /c "%systemdrive%\ProgramData\chocolatey\bin\RefreshEnv.cmd"
        """
    else:
        print("No valid paths found.")
else:
    print("Usage: " + sys.argv[0] + " \"new system path to set s...;...;\"")
    print("Make sure to call this as admin.")
    


