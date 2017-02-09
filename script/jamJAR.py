#!/usr/bin/python
'''
Copyright (c) 2017, dataJAR Ltd.  All rights reserved.

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
            https://github.com/dataJAR/jamJAR

DESCRIPTION

I have a jamf, I have a munki... Uh!.. jamJAR
'''

# Standard imports
import os
import subprocess
import sys
# pylint: disable=no-name-in-module
from CoreFoundation import CFPreferencesCopyAppValue, \
                           CFPreferencesGetAppIntegerValue
# pylint: disable=no-name-in-module
from SystemConfiguration import SCDynamicStoreCopyConsoleUser

def main():
    ''' Check paramters & update manifest as needed, send alert if ran via Self Service &
        uptodate. Force install if wanted. '''

    # Some vars for tings & junk
    jamjar_installs = []
    jamjar_uninstalls = []
    user_name = ''
    warning_count = 0
    yolo_mode = ''

    # Get items in the LocalOnlyManifests managed_installs array
    if CLIENT_MANIFEST.get('managed_installs'):
        for items in CLIENT_MANIFEST.get('managed_installs'):
            jamjar_installs.append(items)
    if CLIENT_MANIFEST.get('managed_uninstalls'):
        for items in CLIENT_MANIFEST.get('managed_uninstalls'):
            jamjar_uninstalls.append(items)

    # Processes parameters
    user_name, jamjar_installs, jamjar_uninstalls, yolo_mode = process_parameters( \
                         user_name, jamjar_installs, jamjar_uninstalls, yolo_mode)

    # Remove any duplicate entries in jamjar_installs & jamjar_uninstalls
    jamjar_installs = list(set(jamjar_installs))
    jamjar_uninstalls = list(set(jamjar_uninstalls))
    warning_count = process_warnings(warning_count)

    # Get integer values of pending items in the ManagedInstalls & uk.co.dataJAR.jamJAR plists
    pending_count = CFPreferencesGetAppIntegerValue('PendingUpdateCount', \
                                                     'ManagedInstalls', None)[0]
    # Update manifest
    update_client_manifest(jamjar_installs, jamjar_uninstalls)

    # Preflight policy text
    print 'Preflight: Contains %s installs %s, %s uninstalls %s, %s pending, %s warnings' \
     % (len(jamjar_installs), jamjar_installs, len(jamjar_uninstalls), jamjar_uninstalls, \
                                                            pending_count, warning_count)

    # Run managedsoftwareupdate
    if yolo_mode == 'ENGAGE':
        print 'WARNING: YOLO mode engaged'
        run_managedsoftwareupdate_yolo()
    else:
        run_managedsoftwareupdate_auto()

    # If running under Self Service, then USERNAME is None but we'll have a USER
    if not os.environ.get('USERNAME') and os.environ.get('USER'):
        # Give feedback that items are uptodate
        process_uptodate()

    # Update counts after installs
    update_counts()

def update_counts():
    ''' Update counts for policy log '''

    # Some vars for tings & junk
    jamjar_installs = []
    jamjar_uninstalls = []
    warning_count = 0

    # Get items in the LocalOnlyManifests managed_installs array
    if CLIENT_MANIFEST.get('managed_installs'):
        for items in CLIENT_MANIFEST.get('managed_installs'):
            jamjar_installs.append(items)
    if CLIENT_MANIFEST.get('managed_uninstalls'):
        for items in CLIENT_MANIFEST.get('managed_uninstalls'):
            jamjar_uninstalls.append(items)

    # Get integer values of pending items in the ManagedInstalls & uk.co.dataJAR.jamJAR plists
    pending_count = CFPreferencesGetAppIntegerValue('PendingUpdateCount', 'ManagedInstalls', \
                                                                                    None)[0]
    # Check if ManagedInstallReport exists
    install_report_plist = '%s/ManagedInstallReport.plist' % MANAGED_INSTALL_DIR
    if not os.path.exists(install_report_plist):
        print 'ManagedInstallReport is missing'
    else:
        managed_install_report = {}
        managed_install_report = FoundationPlist.readPlist(install_report_plist)

    # Print & count warnings
    for warnings in managed_install_report.get('Warnings'):
        print 'Warning: %s' % warnings
        warning_count += 1

    # Postflight policy text
    print 'Postflight: Contains %s installs %s, %s uninstalls %s, %s pending, %s warnings' \
      % (len(jamjar_installs), jamjar_installs, len(jamjar_uninstalls), jamjar_uninstalls, \
                                                             pending_count, warning_count)

# pylint: disable=too-many-branches
def process_parameters(user_name, jamjar_installs, jamjar_uninstalls, yolo_mode):
    ''' Try & get parameters $4, $5, $6, $7, $8 & assign '''

    if sys.argv[4] == '':
        add_to_installs = None
    else:
        add_to_installs = sys.argv[4]
        jamjar_installs.append(add_to_installs)
        print 'Adding %s to installs' % add_to_installs

    if sys.argv[5] == '':
        remove_from_installs = None
    else:
        remove_from_installs = sys.argv[5]
        try:
            jamjar_installs.remove(remove_from_installs)
            print 'Removed %s from installs' % remove_from_installs
        except ValueError:
            print '%s not in installs' % remove_from_installs

    if sys.argv[6] == '':
        add_to_uninstalls = None
    else:
        add_to_uninstalls = sys.argv[6]
        jamjar_uninstalls.append(add_to_uninstalls)
        print 'Adding %s to uninstalls' % add_to_uninstalls

    if sys.argv[7] == '':
        remove_from_uninstalls = None
    else:
        remove_from_uninstalls = sys.argv[7]
        try:
            jamjar_uninstalls.remove(remove_from_uninstalls)
            print 'Removed %s from uninstalls' % remove_from_uninstalls
        except ValueError:
            print '%s not in uninstalls' % remove_from_uninstalls

    if sys.argv[8] != 'ENGAGE':
        yolo_mode = None
    else:
        yolo_mode = sys.argv[8]

    # Check that we have some values passed to the paremeters.. exit if not
    if add_to_installs is None and remove_from_installs is None and add_to_uninstalls is None \
                                     and remove_from_uninstalls is None and yolo_mode is None:
        print 'Nothing assigned to $4, $5, $6. $7 or $8... exiting...'
        sys.exit(1)

    return user_name, jamjar_installs, jamjar_uninstalls, yolo_mode


def update_client_manifest(jamjar_installs, jamjar_uninstalls):
    ''' Update manifest'''

    updated_client_manifest = {}
    updated_client_manifest['managed_installs'] = jamjar_installs
    updated_client_manifest['managed_uninstalls'] = jamjar_uninstalls
    FoundationPlist.writePlist(updated_client_manifest, '%s/manifests/%s' % \
                                           (MANAGED_INSTALL_DIR, MANIFEST))

def run_managedsoftwareupdate_yolo():
    ''' Run managedsoftwareupdate --checkonly then  --installonly '''

    # Check 1st to cache installs
    cmd = ['/usr/local/munki/managedsoftwareupdate', '--checkonly']
    try:
        subprocess.call(cmd, stdout=open(os.devnull, 'wb'))
    # pylint: disable=bare-except
    except:
        print 'There was an error running managedsoftwareupdate --installonly'
        sys.exit(1)

    # Install all items, including pending
    cmd = ['/usr/local/munki/managedsoftwareupdate', '--installonly']
    try:
        subprocess.call(cmd, stdout=open(os.devnull, 'wb'))
    # pylint: disable=bare-except
    except:
        print 'There was an error running managedsoftwareupdate --installonly'
        sys.exit(1)


def run_managedsoftwareupdate_auto():
    ''' Run managedsoftwareupdate. Called with these flags it will show status over
        loginwindow, or if logged in postflight will do it's thing '''

    cmd = ['/usr/local/munki/managedsoftwareupdate', '--auto', '-m']
    try:
        subprocess.call(cmd, stdout=open(os.devnull, 'wb'))
    # pylint: disable=bare-except
    except:
        print 'There was an error running managedsoftwareupdate --auto -m'
        sys.exit(1)


def process_warnings(warning_count):
    ''' Print any warnings '''

    # Check if ManagedInstallReport exists
    install_report_plist = '%s/ManagedInstallReport.plist' % MANAGED_INSTALL_DIR
    if not os.path.exists(install_report_plist):
        print 'ManagedInstallReport is missing'
    else:
        managed_install_report = {}
        managed_install_report = FoundationPlist.readPlist(install_report_plist)

    # Print & count warnings
    # pylint: disable=unused-variable
    for warnings in managed_install_report.get('Warnings'):
        warning_count += 1

    return warning_count


def process_uptodate():
    ''' Give feedback that items are uptodate '''

    # Check if ManagedInstallReport exists
    install_report_plist = '%s/ManagedInstallReport.plist' % MANAGED_INSTALL_DIR
    if os.path.exists(install_report_plist):
        managed_install_report = {}
        managed_install_report = FoundationPlist.readPlist(install_report_plist)
        # If an item has updated, & Munki doesn't have a newer item,
        # it will be added to InstalledItems
        if managed_install_report.get('InstalledItems'):
            for installed_item in managed_install_report.get('InstalledItems'):
                for item in managed_install_report.get('ManagedInstalls'):
                    if item['name'] == installed_item:
                        send_installed_uptodate(item['display_name'])


def send_installed_uptodate(item_display_name):
    ''' Notify if item that install was requested for is uptodate, check username again incase
        user logged out during execution '''

    username = (SCDynamicStoreCopyConsoleUser(None, None, None) or [None])[0]
    if os.path.exists(NOTIFIER_PATH) and username:
        #    item_name  - example: OracleJava8
        #    item_display_name - example: Oracle Java 8
        #    item_version - example: 1.8.111.14
        notifier_args = ['su', '-l', username, '-c', '"{0}" -sender "{1}" -message "{2}" \
                                 -title "{3}"'.format(NOTIFIER_PATH, NOTIFIER_SENDER_ID, \
         NOTIFIER_MSG_UPTODATE % (item_display_name), NOTIFIER_MSG_TITLE,)]
        # Send notification
        subprocess.call(notifier_args, close_fds=True)

if __name__ == "__main__":

    # Make sure we're root
    if os.geteuid() != 0:
        print 'Error: This script must be run as root'
        sys.exit(1)

    # Retrieve values for the below keys. If not set, set to defaults
    LOG_FILE_DIR = CFPreferencesCopyAppValue('log_file_dir', 'uk.co.dataJAR.jamJAR')
    if LOG_FILE_DIR is None:
        LOG_FILE_DIR = '/var/log/'
    NOTIFIER_MSG_UPTODATE = CFPreferencesCopyAppValue('notifier_msg_uptodate', \
                                                         'uk.co.dataJAR.jamJAR')
    if NOTIFIER_MSG_UPTODATE is None:
        NOTIFIER_MSG_UPTODATE = 'Latest version of %s is installed.'
    NOTIFIER_MSG_TITLE = CFPreferencesCopyAppValue('notifier_msg_title', \
                                                'uk.co.dataJAR.jamJAR')
    if NOTIFIER_MSG_TITLE is None:
        NOTIFIER_MSG_TITLE = 'jamJAR'
    NOTIFIER_PATH = CFPreferencesCopyAppValue('notifier_path', 'uk.co.dataJAR.jamJAR')
    if NOTIFIER_PATH is None:
        # pylint: disable=line-too-long
        NOTIFIER_PATH = '/Library/Application Support/JAMF/bin/Management Action.app/Contents/MacOS/Management Action'
    NOTIFIER_SENDER_ID = CFPreferencesCopyAppValue('notifier_sender_id', 'uk.co.dataJAR.jamJAR')
    if NOTIFIER_SENDER_ID is None:
        NOTIFIER_SENDER_ID = 'com.jamfsoftware.selfservice'

    # Exit if cannot find /usr/local/munki, if found import modules
    if not os.path.exists('/usr/local/munki'):
        print 'Cannot find /usr/local/munki'
        sys.exit(1)
    else:
        sys.path.append("/usr/local/munki")
        # pylint: disable=import-error
        from munkilib import FoundationPlist

    # Get location of the Managed Installs directory, exit if not found
    MANAGED_INSTALL_DIR = CFPreferencesCopyAppValue('ManagedInstallDir', 'ManagedInstalls')
    if MANAGED_INSTALL_DIR is None:
        print 'Cannot get Managed Installs directory...'
        sys.exit(1)

    # Make sure a LocalOnlyManifest is specified, then grab the name
    # pylint: disable=no-member
    MANIFEST = CFPreferencesCopyAppValue('LocalOnlyManifest', 'ManagedInstalls')
    # Some vars for tings & junk
    CLIENT_MANIFEST = {}

    # If no LocalOnlyManifest, then look for CLIENT_MANIFEST
    if MANIFEST is None:
        print 'Error: No LocalOnlyManifest declared...'
        sys.exit(1)
    # If LocalOnlyManifest is declared, but does not exist exit.
    elif MANIFEST is not None and not os.path.exists('%s/manifests/%s' % \
                                       (MANAGED_INSTALL_DIR, MANIFEST)):
        print 'LocalOnlyManifest (%s) declared, but is missing' % MANIFEST
    else:
        # If LocalOnlyManifest exists, try to read it
        try:
            CLIENT_MANIFEST = FoundationPlist.readPlist('%s/manifests/%s' % \
                                           (MANAGED_INSTALL_DIR, MANIFEST))
        # pylint: disable=bare-except
        except:
            print 'Cannot read LocalOnlyManifest'

    # Gimme some main
    main()
