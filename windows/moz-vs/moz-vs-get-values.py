#!/mingw64/bin/python.exe

import os
import sys
import platform
from _winreg import *

def usage():
    print "Usage: %s {x86|amd64} {2013|2015|12.0|14.0} [v10.0|v8.1A|v8.1]"
    print "  SDK is optional; highest SDK will be used if not specified"
    sys.exit(1)

if len(sys.argv) < 3 or len(sys.argv) > 4:
    usage()

MSVSTarget = sys.argv[1]  # x86 or amd64
MSVSVersion = sys.argv[2]
RequestedSDK = sys.argv[3] if len(sys.argv) > 3 else None

if MSVSTarget not in ("x86", "amd64"):
    usage()

if MSVSVersion == "2015":   MSVSVersion = "14.0"
elif MSVSVersion == "2013": MSVSVersion = "12.0"
elif MSVSVersion not in ("12.0", "14.0"):
    usage()

is64 = '64bit' in platform.architecture()
USE_32_KEY = KEY_WOW64_32KEY if is64 else 0

try:
    key = OpenKey(HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\VisualStudio\%s' % (MSVSVersion),
                  0, KEY_READ | USE_32_KEY)
    (VSInstallDir,_) = QueryValueEx(key, r'InstallDir')
    CloseKey(key)

    key = OpenKey(HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\VisualStudio\%s\Setup\VC' % (MSVSVersion),
                  0, KEY_READ | USE_32_KEY)
    (VCProductDir,_) = QueryValueEx(key, r'ProductDir')
    CloseKey(key)
except WindowsError, ex:
    print "Can't find VS product dir"
    print ex
    sys.exit(1)

sdkvers = ('v10.0', 'v8.1A', 'v8.1')
if RequestedSDK is not None:
    if RequestedSDK not in sdkvers:
        usage()
    sdkvers = (RequestedSDK,)
for sdkv in sdkvers:
    try:
        key = OpenKey(HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Microsoft SDKs\Windows\%s' % (sdkv),
                      0, KEY_READ | USE_32_KEY)
    except WindowsError:
        continue

    try:
        SDKVer = sdkv
        (SDKDir,_) = QueryValueEx(key, r'InstallationFolder')
        (SDKFullVersion,_) = QueryValueEx(key, r'ProductVersion')
        (SDKFullName,_) = QueryValueEx(key, r'ProductName')
        CloseKey(key)
        break
    except WindowsError, ex:
        print ex
        SDKVer = None
        continue

    # Verify that things actually exist
    if not os.path.exists(os.path.join(SDKDir, "Include/um/Windows.h")):
        SDKVer = None
        continue

    break

if not SDKVer:
    print "No SDK found -- tried %s" % (sdkvers)
    sys.exit(1)

VCProductDirStr = VCProductDir.replace('\\', '\\\\').rstrip('\\')
VSInstallDirStr = VSInstallDir.replace('\\', '\\\\').rstrip('\\')
SDKDirStr = SDKDir.replace('\\', '\\\\').rstrip('\\')

print r'export VSINSTALLDIR="%s"' % (VSInstallDirStr)
print r'export VCINSTALLDIR="%s"' % (VCProductDirStr)
print r'export WINDOWSSDKDIR="%s"' % (SDKDirStr)

print r'INCLUDE=""'
print r'INCLUDE="${INCLUDE};%s\\include"' % (VCProductDirStr)
print r'INCLUDE="${INCLUDE};%s\\atlmfc\\include"' % (VCProductDirStr)
print r'INCLUDE="${INCLUDE};%s\\include\\%s\\ucrt"' % (SDKDirStr, SDKFullVersion)
print r'INCLUDE="${INCLUDE};%s\\include\\%s\\shared"' % (SDKDirStr, SDKFullVersion)
print r'INCLUDE="${INCLUDE};%s\\include\\%s\\um"' % (SDKDirStr, SDKFullVersion)
print r'INCLUDE="${INCLUDE};%s\\include\\%s\\winrt"' % (SDKDirStr, SDKFullVersion)
print r'export INCLUDE'

vclibsuffix = "amd64" if MSVSTarget == "amd64" else ""
sdklibsuffix = "x64" if MSVSTarget == "amd64" else "x86"

print r'LIB=""'
print r'LIB="${LIB};%s\\lib\\%s"' % (VCProductDirStr, vclibsuffix)
print r'LIB="${LIB};%s\\atlmfc\\lib\\%s"' % (VCProductDirStr, vclibsuffix)
print r'LIB="${LIB};%s\\lib\\%s\\ucrt\\%s"' % (SDKDirStr, SDKFullVersion, sdklibsuffix)
print r'LIB="${LIB};%s\\lib\\%s\\um\\%s"' % (SDKDirStr, SDKFullVersion, sdklibsuffix)
print r'export LIB'

# These are printed in reverse order, because we're prepending to path

def prepend_path(*args):
    realpath = os.path.abspath(os.path.join(*args))
    if realpath[1] != ':' or realpath[2] not in ('/', '\\'):
        print "abspath returned a path that isn't in windows form C://... ?"
        sys.exit(1)
    realpath = '/' + realpath[0] + '/' + realpath[3:]
    print r'PATH="%s:${PATH}"' % (realpath)

prepend_path(SDKDir, "bin", "x86")
if is64: prepend_path(SDKDir, "bin", "x64")
prepend_path(VSInstallDir, "Team Tools", "Performance Tools")
if is64: prepend_path(VSInstallDir, "Team Tools", "Performance Tools", "x64")
prepend_path(VSInstallDir, "Common7", "Tools")
prepend_path(VSInstallDir, "Common7", "IDE")
prepend_path(VSInstallDir, "VC", "VCPackages")
if is64 and MSVSTarget == "x86":
    # Prefer 64-bit compiler cross-compiling to 32-bit, if found
    if os.path.exists(os.path.join(VCProductDir, "bin", "amd64_x86", "cl.exe")):
        prepend_path(VCProductDir, "bin", "amd64_x86")
    else:
        prepend_path(VCProductDir, "bin")
elif is64 and MSVSTarget == "amd64":
    prepend_path(VCProductDir, "bin", "amd64")
elif MSVSTarget == "x86":
    prepend_path(VCProductDir, "bin")
elif MSVSTarget == "amd64":
    prepend_path(VCProductDir, "bin", "x86_amd64")
print r'export PATH'

