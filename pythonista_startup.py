# https://gist.github.com/dgelessus/fe8e267149862eb67127f4fff7e017be

# This is an example pythonista_startup.py script.
# The code below is from https://github.com/dgelessus/pythonista_startup/blob/master/enable_faulthandler.py

from __future__ import absolute_import, division, print_function
import sys
import argparse
from objc_util import *


class ImportFrameworkError(Exception):

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return 'Couldn\'t import {}.framewrork. (Neither from public, nor from private frameworks)'.format(
            self.name)


def _framework_path(name, private):
    return '/System/Library/{}Frameworks/{}.framework'.format(
        'Private' if private else '', name)


def importFramework(name):
    global _framework_path  # This is required to work when the import stuff is importes in the startup file
    public_path = _framework_path(name, private=False)
    private_path = _framework_path(name, private=True)

    bundle = NSBundle.bundleWithPath_(public_path)

    if not bundle is None:
        bundle.load()
    else:
        # Could not load public bundle, will try private
        bundle = NSBundle.bundleWithPath_(private_path)
        if not bundle is None:
            bundle.load()
        else:
            raise ImportFrameworkError(name)

module_names = (
    'stash',
    'system.shcommon',
    'system.shstreams',
    'system.shscreens',
    'system.shui',
    'system.shui.base',
    'system.shio',
    'system.shiowrapper',
    'system.shparsers',
    'system.shruntime',
    'system.shthreads',
    'system.shuseractionproxy',
    'system.shhistory',
)

# Attempt to reload modules when startup, does not seem to work
if 'stash.stash' in sys.modules:
    for name in module_names:
        sys.modules.pop('stash.' + name)
from stash import stash

ap = argparse.ArgumentParser()
ap.add_argument('--no-cfgfile',
                action='store_true',
                help='do not load external config files')
ap.add_argument('--no-rcfile',
                action='store_true',
                help='do not load external resource file')
ap.add_argument('--no-historyfile',
                action='store_true',
                help='do not load history file from last session')
ap.add_argument('--log-level',
                choices=['DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'],
                default='INFO',
                help='the logging level')
ap.add_argument('--log-file', help='the file to send logging messages')
ap.add_argument(
    '--debug-switch',
    default='',
    help='a comma separate list to turn on debug switch for components')
ap.add_argument('-c',
                '--command',
                default=None,
                dest='command',
                help='command to run')
ap.add_argument(
    'args',  # the editor shortcuts may pass additional arguments
    nargs='*',
    help='additional arguments (ignored)')
ns = ap.parse_args()

log_setting = {
    'level': ns.log_level,
    'file': ns.log_file,
}

if ns.debug_switch == '':
    debug = (
        # stash._DEBUG_STREAM,
        # stash._DEBUG_RENDERER,
        # stash._DEBUG_MAIN_SCREEN,
        # stash._DEBUG_MINI_BUFFER,
        # stash._DEBUG_IO,
        stash._DEBUG_UI,
        # stash._DEBUG_TERMINAL,
        # stash._DEBUG_TV_DELEGATE,
        # stash._DEBUG_RUNTIME,
        # stash._DEBUG_PARSER,
        # stash._DEBUG_EXPANDER,
        # stash._DEBUG_COMPLETER,
    )
elif ns.debug_switch == "all":
    debug = []
    for key in dir(stash):
        if key.startswith("_DEBUG_"):
            value = getattr(stash, key, None)
            if value is not None:
                debug.append(value)
else:
    debug = []
    for ds in ns.debug_switch.split(','):
        ds = getattr(stash, '_DEBUG_{}'.format(ds.upper()), None)
        if ds is not None:
            debug.append(ds)

if ns.command:
    # tell StaSh not to run any command if command is passed
    # (we will call the command manually later)
    ctp = False
else:
    # tell StaSh to run the default command (totd.py)
    ctp = None

_stash = stash.StaSh(
    debug=debug,
    log_setting=log_setting,
    no_cfgfile=ns.no_cfgfile,
    no_rcfile=ns.no_rcfile,
    no_historyfile=ns.no_historyfile,
    #command=ctp,claudev3
    command=ctp)

_stash.launch(ns.command)
if ns.command is not None:
    import console
    import dialogs
    import clipboard
    # TODO: _stash.launch() may block, which prevents this from being executed
    console.hide_output()
    _stash(ns.command, add_to_history=True, persistent_level=0)


def enable_faulthandler():
    import ctypes
    import datetime
    import errno
    import io
    import objc_util
    import os
    import shutil
    import sys

    try:
        unicode
    except NameError:
        unicode = str

    #print(u"Enabling fault handler and Objective-C exception handler...")

    LOGDIR = os.path.expanduser(u"~/Documents/faultlog")
    LOGNAME_TEMPLATE = u"faultlog-{:%Y-%m-%d-%H-%M-%S}.txt"
    LOGNAME_DEFAULT = u"faultlog-temp.txt"
    EXCEPTIONLOGNAME_DEFAULT = u"exceptionlog-temp.txt"

    # Create the faultlog directory if necessary
    try:
        os.mkdir(LOGDIR)
    except (IOError, OSError) as err:
        if err.errno != errno.EEXIST:
            raise

    # Check whether an Objective-C exception log exists and append it to the fault log
    try:
        fin = io.open(os.path.join(LOGDIR, EXCEPTIONLOGNAME_DEFAULT), "rb")
    except (IOError, OSError) as err:
        if err.errno != errno.ENOENT:
            raise
    else:
        with fin:
            data = fin.read()

        if data:
            with io.open(os.path.join(LOGDIR, LOGNAME_DEFAULT), "ab") as fout:
                # If the faultlog is not empty, add a separator
                if fout.tell() != 0:
                    fout.write(b"\n" + b"-" * 72 + b"\n\n")

                fout.write(data)

        os.remove(os.path.join(LOGDIR, EXCEPTIONLOGNAME_DEFAULT))

    # Check whether a faultlog was written
    did_fault = False

    try:
        f = io.open(os.path.join(LOGDIR, LOGNAME_DEFAULT), "rb")
    except (IOError, OSError) as err:
        if err.errno != errno.ENOENT:
            raise
    else:
        with f:
            if f.read(1):
                did_fault = True

    # Notify the user that a crash has happened
    if did_fault:
        print(u"Pythonista quit abnormally last time.", file=sys.stderr)

        stamped_name = LOGNAME_TEMPLATE.format(
            datetime.datetime.fromtimestamp(
                os.stat(os.path.join(LOGDIR, LOGNAME_DEFAULT)).st_mtime))
        shutil.move(os.path.join(LOGDIR, LOGNAME_DEFAULT),
                    os.path.join(LOGDIR, stamped_name))
        print(u"For details, see the log file '{}'.".format(stamped_name),
              file=sys.stderr)

    if sys.version_info < (3,):
        #print(u"Setting exception handler.")
        # Set the Objective-C exception handler only under Python 2.
        # Otherwise under Pythonista 3 it would be set twice - once by Python 2 and once by Python 3.
        # This way the exception handler is set exactly once and works under Pythonista 2 and 3.

        # typedef void (*objc_uncaught_exception_handler)(id exception);
        objc_uncaught_exception_handler = ctypes.CFUNCTYPE(
            None, ctypes.c_void_p)

        # objc_uncaught_exception_handler objc_setUncaughtExceptionHandler(objc_uncaught_exception_handler fn);
        objc_util.c.objc_setUncaughtExceptionHandler.argtypes = [
            objc_uncaught_exception_handler
        ]
        objc_util.c.objc_setUncaughtExceptionHandler.restype = objc_uncaught_exception_handler

        # Set Objective-C uncaught exception handler
        @objc_uncaught_exception_handler
        def handler(exc_pointer):
            exc = objc_util.ObjCInstance(exc_pointer)

            name = exc.name()
            reason = exc.reason()
            user_info = exc.userInfo()

            call_stack_symbols = exc.callStackSymbols()

            with io.open(os.path.join(LOGDIR, EXCEPTIONLOGNAME_DEFAULT),
                         "wb") as f:
                try:
                    f.write(b"Objective-C exception details:\n\n")

                    if reason is None:
                        f.write(str(name).encode("utf-8") + b"\n")
                    else:
                        f.write(
                            str(name).encode("utf-8") + b": " +
                            str(reason).encode("utf-8") + b"\n")

                    if user_info is not None:
                        f.write(str(user_info).encode("utf-8") + b"\n")

                    f.write(b"\nStack trace:\n\n")

                    for sym in call_stack_symbols:
                        f.write(str(sym).encode("utf-8") + b"\n")

                    f.write(b"\nEnd of exception details.\n")
                except Exception as err:
                    import traceback
                    f.write(b"I messed up! Python exception:\n")
                    f.write(traceback.format_exc().encode("utf-8"))
                    raise

        # The exception handler must be kept in some kind of permanent location, otherwise it will be collected by the garbage collector, because there are no more references to it from Python.
        objc_util._dgelessus_pythonista_startup_exception_handler = handler
        objc_util.c.objc_setUncaughtExceptionHandler(handler)
    else:
        # The faulthandler module is only available under Python 3.
        #print("Setting fault handler.")

        import faulthandler

        logfile = io.open(os.path.join(LOGDIR, LOGNAME_DEFAULT), "wb")
        faulthandler.enable(logfile)

    #print(u"Done enabling fault handler and Objective-C exception handler.")


enable_faulthandler()

# https://gist.github.com/lukaskollmer/1e0587599ab4d40f59299d72870f22b1



UIView.beginAnimations_(None)
UIView.setAnimationDuration_(0)
importFramework('UIKit')
importFramework('MediaPlayer')

