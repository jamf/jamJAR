#!/usr/local/munki/python
'''
Copyright (c) 2019, dataJAR Ltd.  All rights reserved.

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
from __future__ import absolute_import
from __future__ import print_function
import os
import subprocess
# pylint: disable=no-name-in-module
from CoreFoundation import CFPreferencesCopyAppValue

def main():
    ''' Make sure that the jamJAR.log exists, & if it does... print the last line '''

    log_file_path = os.path.join(LOG_FILE_DIR, 'jamJAR.log')
    if os.path.exists(log_file_path):
        tail_log = subprocess.Popen(['/usr/bin/tail', '-1', log_file_path], stdout=subprocess.PIPE)
        last_line = tail_log.communicate()[0].rstrip()
        print('<result>%s</result>' % last_line)


if __name__ == "__main__":

    # Retrieve values for the below keys. If not set, set to defaults
    LOG_FILE_DIR = CFPreferencesCopyAppValue('log_file_dir', 'uk.co.dataJAR.jamJAR')
    if LOG_FILE_DIR is None:
        LOG_FILE_DIR = '/var/log/'

    # Gimme some main
    main()
