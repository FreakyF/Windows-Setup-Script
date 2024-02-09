import ctypes
from ctypes import wintypes

HWND_BROADCAST = 0xFFFF
WM_SETTINGCHANGE = 0x001A

# Constants from WinNls.h and Winnls32.h
LOCALE_USER_DEFAULT = 0x0400
LOCALE_SDECIMAL = 0x000E
LOCALE_STHOUSAND = 0x000F
LOCALE_SGROUPING = 0x0020
LOCALE_INEGNUMBER = 0x1010
LOCALE_SCURRENCY = 0x00014
LOCALE_ICURRDIGITS = 0x00019
LOCALE_SMONDECIMALSEP = 0x00016
LOCALE_SMONTHOUSANDSEP = 0x00017
LOCALE_SMONGROUPING = 0x00018
LOCALE_ICURRENCY = 0x0001B
LOCALE_INEGCURR = 0x0001C

# Load the User32 DLL
user32 = ctypes.WinDLL('user32', use_last_error=True)

# Define necessary types
LCID = wintypes.LCID
LCTYPE = wintypes.DWORD


# Function to change locale settings
def set_locale_info(lctype, value):
    if not ctypes.windll.kernel32.SetLocaleInfoW(LCID(LOCALE_USER_DEFAULT), LCTYPE(lctype), ctypes.c_wchar_p(value)):
        raise ctypes.WinError(ctypes.get_last_error())
    # It's necessary to broadcast a message that settings have changed
    user32.SendMessageTimeoutW(HWND_BROADCAST, WM_SETTINGCHANGE, 0, 0, 0, 1000, ctypes.byref(wintypes.DWORD()))


# Set number format
set_locale_info(LOCALE_SDECIMAL, ".")
set_locale_info(LOCALE_STHOUSAND, " ")
set_locale_info(LOCALE_SGROUPING, "3;0")
set_locale_info(LOCALE_INEGNUMBER, "1")

# Set currency format
set_locale_info(LOCALE_SCURRENCY, "zł")
set_locale_info(LOCALE_ICURRDIGITS, "2")
set_locale_info(LOCALE_SMONDECIMALSEP, ".")
set_locale_info(LOCALE_SMONTHOUSANDSEP, " ")
set_locale_info(LOCALE_SMONGROUPING, "3;0")
set_locale_info(LOCALE_ICURRENCY, "0")  # 0 = prefix, no space
set_locale_info(LOCALE_INEGCURR, "8")  # 8 = minus sign, prefix, no space

print("Locale settings updated.")
