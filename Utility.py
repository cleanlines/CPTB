import os
import sys
import uuid
import shutil
import subprocess
import glob
import time

class Utility(object):

    @staticmethod
    def get_install_path():
        """ Return 64bit python install path from registry (if installed and registered),
            otherwise fall back to current 32bit process install path.
        """
        if sys.maxsize > 2 ** 32: return sys.exec_prefix  # We're running in a 64bit process

        # We're 32 bit so see if there's a 64bit install
        path = r'SOFTWARE\Python\PythonCore\2.7'

        from _winreg import OpenKey, QueryValue
        from _winreg import HKEY_LOCAL_MACHINE, KEY_READ, KEY_WOW64_64KEY

        try:
            with OpenKey(HKEY_LOCAL_MACHINE, path, 0, KEY_READ | KEY_WOW64_64KEY) as key:
                return QueryValue(key, "InstallPath").strip(os.sep)  # We have a 64bit install, so return that.
        except Exception:
            return sys.exec_prefix  # No 64bit, so return 32bit path

    @staticmethod
    def some_filename():
        return os.path.join(os.getenv('TEMP'), str(uuid.uuid4()).replace('-', ''))

    @staticmethod
    def some_unique_string():
        return str(uuid.uuid4()).replace('-', '')

    @staticmethod
    def get_file_name(filename):
        return os.path.split(filename)[1]

    @staticmethod
    def copy_file(src_file,dest_dir):
        try:
            file_name = os.path.split(src_file)[1]
            shutil.copy(src_file,os.path.join(dest_dir,file_name))
            return file_name
        except:
            raise

    @staticmethod
    def jpg_a_pdf(a_file,an_exe,out_loc):
        try:
            if not os.path.exists(out_loc): os.mkdir(out_loc)
            cmd = "{0} -ip {1} -ol {2}".format(an_exe, a_file, out_loc)
            subprocess.call(cmd, shell=False)
            return [f for f in glob.glob(out_loc+"/"+os.path.splitext(os.path.split(a_file)[1])[0]+"*.jpg")]
        except:
            raise

    @staticmethod
    def some_unique_subdirectory(root):
        return os.path.join(root, "_ags_" + Utility.some_unique_string())

    @staticmethod
    def current_milli_time():
        return int(round(time.time() * 1000))