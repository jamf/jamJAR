#!/usr/local/munki/munki-python
# encoding: utf-8
# pylint: disable = invalid-name
'''
Copyright (c) 2023, dataJAR Ltd.  All rights reserved.

     Redistribution and use in source and binary forms, with or without
     modification, are permitted provided that the following conditions are met:
             * Redistributions of source code must retain the above copyright
               notice, this list of conditions and the following disclaimer.
             * Redistributions in binary form must reproduce the above copyright
               notice, this list of conditions and the following disclaimer in the
               documentation and/or other materials provided with the distribution.
             * Neither data JAR Ltd nor the names of its contributors may be used to
               endorse or promote products derived from this software without specific
               prior written permission.

     THIS SOFTWARE IS PROVIDED BY DATA JAR LTD "AS IS" AND ANY
     EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
     WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
     DISCLAIMED. IN NO EVENT SHALL DATA JAR LTD BE LIABLE FOR ANY
     DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
     (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
     LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
     ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
     (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
     SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

SUPPORT FOR THIS PROGRAM

    This program is distributed "as is" by DATA JAR LTD.
    For more information or support, please utilise the following resources:

    https://macadmins.slack.com/messages/jamjar
    https://macadmins.slack.com/messages/datajar
    https://github.com/dataJAR/jamJAR
'''


# Version
__version__ = '2.1'


# Standard imports
import os
import subprocess
import sys
# pylint: disable = import-error,no-name-in-module
from CoreFoundation import (CFPreferencesCopyAppValue,
                            CFPreferencesGetAppIntegerValue)
# pylint: disable = import-error,no-name-in-module
from SystemConfiguration import SCDynamicStoreCopyConsoleUser


def main():
    '''
        Check parameters & update manifest as needed, send alert if ran via Self Service &
        up-to-date. Force install if wanted.
    '''

    # Get items details of items in the manifest
    jamjar_installs = process_managed_installs()
    jamjar_uninstalls = process_managed_uninstalls()

    # Processes parameters
    jamjar_installs, jamjar_uninstalls, yolo_mode = process_parameters(
                                                       jamjar_installs, jamjar_uninstalls)

    # Get count of any warning items
    warning_count = process_warnings()

    # Get integer values of pending items in the ManagedInstalls & uk.co.dataJAR.jamJAR plists
    pending_count = CFPreferencesGetAppIntegerValue('PendingUpdateCount',
                                                    'ManagedInstalls', None)[0]
    # Update manifest
    update_client_manifest(jamjar_installs, jamjar_uninstalls)

    # Preflight policy text
    print(f"Preflight: Contains {len(jamjar_installs)} installs {jamjar_installs}, "
          f"{len(jamjar_uninstalls)} uninstalls {jamjar_uninstalls}, {pending_count} pending, "
          f"{warning_count} warnings")

    # Run managedsoftwareupdate --installonly
    if yolo_mode:
        print("WARNING: YOLO mode engaged")
        run_managedsoftwareupdate_yolo()
    else:
        run_managedsoftwareupdate_auto()

    # If running under Self Service, then USERNAME is None but we'll have a USER
    if (not os.environ.get('USERNAME')
        and os.environ.get('USER')
        and os.environ.get('USER') != 'root'):
        # Give feedback that items are uptodate
        process_uptodate()

    # Update counts after installs
    update_counts()


# Other functions
def process_managed_installs():
    '''
        Returns a list of any managed_installs oj the manifest
    '''
    # Var declaration
    jamjar_installs = []

    # If any items are in the managed_installs array
    if CLIENT_MANIFEST.get('managed_installs'):
        # Add each item to the jamjar_installs list
        for items in CLIENT_MANIFEST.get('managed_installs'):
            jamjar_installs.append(items)

    # Returns a list of managed_installs, with dupes removed
    return list(set(jamjar_installs))


def process_managed_install_report():
    '''
        Processes ManagedInstallReport.plist
    '''

    # Var declaration
    managed_install_report = {}

    # Generate path to ManagedInstallReport
    install_report_plist = f'{MANAGED_INSTALL_DIR}/ManagedInstallReport.plist'

    # If the path exists
    if os.path.exists(install_report_plist):
        # Read in the plist
        managed_install_report = FoundationPlist.readPlist(install_report_plist)

    # Return contents of ManagedInstallReport, if exists
    return managed_install_report


def process_managed_uninstalls():
    '''
        Returns a list of any managed_uninstalls oj the manifest
    '''
    # Var declaration
    jamjar_uninstalls = []

    # If any items are in the managed_uninstalls array
    if CLIENT_MANIFEST.get('managed_uninstalls'):
        # Add each item to the jamjar_uninstalls list
        for items in CLIENT_MANIFEST.get('managed_uninstalls'):
            jamjar_uninstalls.append(items)

    # Returns a list of managed_uninstalls, with dupes removed
    return list(set(jamjar_uninstalls))


def process_parameters(jamjar_installs, jamjar_uninstalls):
    '''
        Try & get parameters $4, $7, $6, $7, $8 & assign.
    '''

    # Var declaration
    installs_to_add = None
    installs_to_remove = None
    uninstalls_to_add = None
    uninstalls_to_remove = None
    yolo_mode = None

    # If something has been passed to $4
    if sys.argv[4] != '':
        # Split at ,
        installs_to_add = sys.argv[4]
        # Process to add to jamjar_installs
        process_parameter_4(installs_to_add, jamjar_installs)

    # If something has been passed to $5
    if sys.argv[5] != '':
        # Split at ,
        installs_to_remove = sys.argv[5]
        # Process to add to jamjar_installs
        process_parameter_5(installs_to_remove, jamjar_installs)

    # If something has been passed to $6
    if sys.argv[6] != '':
        # Split at ,
        uninstalls_to_add = sys.argv[6]
        # Process to add to jamjar_uninstalls
        process_parameter_6(jamjar_uninstalls, uninstalls_to_add)

    # If something has been passed to $7
    if sys.argv[7] != '':
        # Split at ,
        uninstalls_to_remove = sys.argv[7]
        # Process to add to jamjar_uninstalls
        process_parameter_7(jamjar_uninstalls, uninstalls_to_remove)

    # Set yolo_mode, if ENGAGE passed to $8
    if sys.argv[8] == 'ENGAGE':
        yolo_mode = 'ENGAGE'

    # Check that we have some values passed to the parameters.. exit if not
    if (installs_to_add is None and installs_to_remove is None and uninstalls_to_add is None
            and uninstalls_to_remove is None and yolo_mode is None):
        print("Nothing assigned to $4, $7, $6, $7 or $8... exiting...")
        sys.exit(1)

    # Values for the processed variables
    return jamjar_installs, jamjar_uninstalls, yolo_mode


def process_parameter_4(installs_to_add, jamjar_installs):
    '''
        Processes items passed to $4.
    '''

    # For each item in installs_to_add
    for install_to_add in installs_to_add.split(','):
        jamjar_installs.append(install_to_add)
        print(f"Adding {install_to_add} to installs")

    # Returns a list of managed_installs, with dupes removed
    return list(set(jamjar_installs))


def process_parameter_5(installs_to_remove, jamjar_installs):
    '''
        Processes items passed to $5.
    '''

    # For each item in installs_to_remove
    for install_to_remove in installs_to_remove.split(','):
        # Try to remove
        try:
            jamjar_installs.remove(install_to_remove)
            print(f"Removed {install_to_remove} to installs")
        except ValueError:
            print(f"{install_to_remove} not in installs")

    # Returns a list of managed_installs, with dupes removed
    return list(set(jamjar_installs))


def process_parameter_6(jamjar_uninstalls, uninstalls_to_add):
    '''
        Processes items passed to $6.
    '''

    # For each item in uninstalls_to_add
    for uninstall_to_add in uninstalls_to_add.split(','):
        jamjar_uninstalls.append(uninstall_to_add)
        print(f"Adding {uninstall_to_add} to uninstalls")

    # Returns a list of managed_uninstalls, with dupes removed
    return list(set(jamjar_uninstalls))


def process_parameter_7(jamjar_uninstalls, uninstalls_to_remove):
    '''
        Processes items passed to $7.
    '''

    # For each item in uninstalls_to_remove
    for uninstall_to_remove in uninstalls_to_remove.split(','):
        # Try to remove
        try:
            jamjar_uninstalls.remove(uninstall_to_remove)
            print(f"Removed {uninstall_to_remove} to uninstalls")
        except ValueError:
            print(f"{uninstall_to_remove} not in uninstalls")

    # Returns a list of managed_uninstalls, with dupes removed
    return list(set(jamjar_uninstalls))


def process_uptodate():
    '''
        Give feedback that items are up-to-date.
    '''

    # Get the latest version of ManagedInstallReport (if exists)
    managed_install_report = process_managed_install_report()

    # If items have been installed
    if managed_install_report:
        # If an item has updated, & Munki doesn't have a newer item.
        # The item will be added to InstalledItems
        if managed_install_report.get('InstalledItems'):
            # Check each item
            for installed_item in managed_install_report.get('InstalledItems'):
                # Check the name against items in the ManagedInstalls array
                for managed_install in managed_install_report.get('ManagedInstalls'):
                    # If we have a match, notify the user
                    if managed_install['name'] == installed_item:
                        send_installed_uptodate(managed_install['display_name'])


def process_warnings():
    '''
        Return number of warnings.
    '''

    # Get the latest version of ManagedInstallReport (if exists)
    managed_install_report = process_managed_install_report()

    # Return number of warning items
    return len(managed_install_report.get('Warnings', []))


def run_managedsoftwareupdate_auto():
    '''
        Run managedsoftwareupdate. Called with these flags it will show status over
        loginwindow, or if logged in postflight will do it's thing.
    '''

    # Command to run
    cmd_args = ['/usr/local/munki/managedsoftwareupdate', '--auto', '-m']

    # Run managedsoftwareupdate, in it's auto mode, logging if an issue is encountered
    try:
        subprocess.call(cmd_args, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError as err_msg:
        print(f"ERROR: {cmd_args} failed with: ", err_msg)
        sys.exit(1)


def run_managedsoftwareupdate_yolo():
    '''
        Run managedsoftwareupdate --checkonly then  --installonly.
    '''

    # Command to run
    cmd_args = ['/usr/local/munki/managedsoftwareupdate', '--checkonly']

    # Check 1st to cache installs, logging if an issue is encountered
    try:
        subprocess.call(cmd_args, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError as err_msg:
        print(f"ERROR: {cmd_args} failed with: ", err_msg)
        sys.exit(1)

    # Command to run
    cmd_args = ['/usr/local/munki/managedsoftwareupdate', '--installonly']

    # Install all items, including pending, logging if an issue is encountered
    try:
        subprocess.call(cmd_args, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError as err_msg:
        print(f"ERROR: {cmd_args} failed with: ", err_msg)
        sys.exit(1)


def send_installed_uptodate(item_display_name):
    '''
        Notify if item that install was requested for is up-to-date, check username again incase
        user logged out during execution.
    '''

    # The username of the logged in user
    username = (SCDynamicStoreCopyConsoleUser(None, None, None) or [None])[0]

    # If we have no value for the above, or we're at the loginwindow.. set username to None
    if username in ("", "loginwindow"):
        username = None

    # If we have the wanted notifier app installed, and we're logged in
    if os.path.exists(NOTIFIER_PATH) and username:
        #    item_name  - example: OracleJava8
        #    item_display_name - example: Oracle Java 8
        #    item_version - example: 1.8.111.14
        if DATAJAR_NOTIFIER:
            notifier_args = ['/usr/bin/su', '-l', username, '-c', f'"{NOTIFIER_PATH}" '
                                             f'--messageaction "{NOTIFIER_SENDER_ID}" '
                          f'--message "{NOTIFIER_MSG_UPTODATE % (item_display_name)}" '
                                                     f'--title "{NOTIFIER_MSG_TITLE}" '
                                                                      f'--type banner']
        else:
            notifier_args = ['/usr/bin/su', '-l', username, '-c', f'"{NOTIFIER_PATH}" '
                                                     f'-sender "{NOTIFIER_SENDER_ID}" '
                           f'-message "{NOTIFIER_MSG_UPTODATE % (item_display_name)}" '
                                                      f'-title "{NOTIFIER_MSG_TITLE}"']

        # Send notification
        subprocess.call(notifier_args, close_fds=True)


def update_client_manifest(jamjar_installs, jamjar_uninstalls):
    '''
        Update manifest, leaving only items that have not installed/uninstalled yet.
    '''

    # var declaration
    updated_client_manifest = {}

    # Get installs
    updated_client_manifest['managed_installs'] = jamjar_installs

    # Get uninstalls
    updated_client_manifest['managed_uninstalls'] = jamjar_uninstalls

    # Write to plist
    FoundationPlist.writePlist(updated_client_manifest,
                               f'{MANAGED_INSTALL_DIR}/manifests/{MANIFEST}')


def update_counts():
    '''
        Update counts for policy log.
    '''

    # Get items details of items in the manifest
    jamjar_installs = process_managed_installs()
    jamjar_uninstalls = process_managed_uninstalls()

    # Get integer values of pending items in the ManagedInstalls & uk.co.dataJAR.jamJAR plists
    pending_count = CFPreferencesGetAppIntegerValue('PendingUpdateCount', 'ManagedInstalls',
                                                    None)[0]

    # Get number of warning items
    warning_count = process_warnings()

    # Postflight policy text
    print(f"Postflight: Contains {len(jamjar_installs)} installs {jamjar_installs}, "
          f"{len(jamjar_uninstalls)} uninstalls {jamjar_uninstalls}, {pending_count} pending, "
          f"{warning_count} warnings")


if __name__ == "__main__":

    # Make sure we're root
    if os.geteuid() != 0:
        print('ERROR: This script must be run as root')
        sys.exit(1)

    # Try to locate jamf binary
    if not os.path.exists('/usr/local/jamf/bin/jamf'):
        print('ERROR: Cannot find jamf binary')
        sys.exit(1)

    # Import FoundationPlist from munki, exit if errors
    sys.path.append("/usr/local/munki")
    try:
        from munkilib import FoundationPlist
    except ImportError:
        print('ERROR: Cannot import FoundationPlist')
        sys.exit(1)

    # https://github.com/dataJAR/jamJAR/wiki/jamJAR-Preferences#datajar_notifier
    DATAJAR_NOTIFIER = CFPreferencesCopyAppValue('datajar_notifier', 'uk.co.dataJAR.jamJAR')
    if DATAJAR_NOTIFIER is None:
        DATAJAR_NOTIFIER = False

    # https://github.com/dataJAR/jamJAR/wiki/jamJAR-Preferences#notifier_msg_title
    NOTIFIER_MSG_TITLE = CFPreferencesCopyAppValue('notifier_msg_title', 'uk.co.dataJAR.jamJAR')
    if NOTIFIER_MSG_TITLE is None:
        NOTIFIER_MSG_TITLE = 'jamJAR'

    # https://github.com/dataJAR/jamJAR/wiki/jamJAR-Preferences#notifier_msg_uptodate
    NOTIFIER_MSG_UPTODATE = CFPreferencesCopyAppValue('notifier_msg_uptodate',
                                                      'uk.co.dataJAR.jamJAR')
    if NOTIFIER_MSG_UPTODATE is None:
        NOTIFIER_MSG_UPTODATE = 'Latest version of %s is installed.'

    # https://github.com/dataJAR/jamJAR/wiki/jamJAR-Preferences#notifier_path
    NOTIFIER_PATH = CFPreferencesCopyAppValue('notifier_path', 'uk.co.dataJAR.jamJAR')
    if NOTIFIER_PATH is None:
        NOTIFIER_PATH = ('/Library/Application Support/JAMF/bin/Management '
                         'Action.app/Contents/MacOS/Management Action')

    # https://github.com/dataJAR/jamJAR/wiki/jamJAR-Preferences#notifier_sender_id
    NOTIFIER_SENDER_ID = CFPreferencesCopyAppValue('notifier_sender_id', 'uk.co.dataJAR.jamJAR')
    if NOTIFIER_SENDER_ID is None:
        NOTIFIER_SENDER_ID = 'com.jamfsoftware.selfservice'

    # Get location of the Managed Installs directory, exit if not found
    MANAGED_INSTALL_DIR = CFPreferencesCopyAppValue('ManagedInstallDir', 'ManagedInstalls')
    if MANAGED_INSTALL_DIR is None:
        print('ERROR: Cannot get Managed Installs directory...')
        sys.exit(1)

    # Make sure a LocalOnlyManifest is specified, then grab the name
    MANIFEST = CFPreferencesCopyAppValue('LocalOnlyManifest', 'ManagedInstalls')

    # Var declaration
    CLIENT_MANIFEST = {}

    # If no LocalOnlyManifest, then look for CLIENT_MANIFEST
    if MANIFEST is None:
        print("ERROR: No LocalOnlyManifest declared...")
        sys.exit(1)
    # If LocalOnlyManifest is declared, but does not exist exit.
    elif MANIFEST is not None and not os.path.exists(f'{MANAGED_INSTALL_DIR}/manifests/{MANIFEST}'):
        print(f"LocalOnlyManifest ({MANIFEST}) declared, but is missing.. will create")
    else:
        # If LocalOnlyManifest exists, try to read it
        try:
            CLIENT_MANIFEST = FoundationPlist.readPlist(
                                                    f'{MANAGED_INSTALL_DIR}/manifests/{MANIFEST}')
        except FoundationPlist.NSPropertyListSerializationException:
            print("ERROR: Cannot read LocalOnlyManifest")
            sys.exit(1)

    # Gimme some main
    main()
