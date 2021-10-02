#!/bin/bash

####################################################################################################
#
# Copyright (c) 2021, dataJAR Ltd.  All rights reserved.
#
#       Redistribution and use in source and binary forms, with or without
#       modification, are permitted provided that the following conditions are met:
#               * Redistributions of source code must retain the above copyright
#                 notice, this list of conditions and the following disclaimer.
#               * Redistributions in binary form must reproduce the above copyright
#                 notice, this list of conditions and the following disclaimer in the
#                 documentation and/or other materials provided with the distribution.
#               * Neither data JAR Ltd nor the
#                 names of its contributors may be used to endorse or promote products
#                 derived from this software without specific prior written permission.
#
#       THIS SOFTWARE IS PROVIDED BY DATA JAR LTD "AS IS" AND ANY
#       EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#       WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#       DISCLAIMED. IN NO EVENT SHALL DATA JAR LTD BE LIABLE FOR ANY
#       DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#       (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#       LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#       ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#       (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#       SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
####################################################################################################
#
# SUPPORT FOR THIS PROGRAM
#
#       This program is distributed "as is" by DATA JAR LTD.
#       For more information or support, please utilise the following resources:
#
#               http://www.datajar.co.uk
#
####################################################################################################
#
# DESCRIPTION
# Returns the last line of the Auto-Update log file
#
####################################################################################################
#
# CHANGE LOG
# 2.0 - 2021-10-02 - Rewritten in bash, to stop python prompts on macOS 12+
#
####################################################################################################

if [ -f "/Library/Preferences/uk.co.dataJAR.jamJAR.plist" ]
then
    logDir=$(/usr/bin/defaults read "/Library/Managed Preferences/uk.co.dataJAR.jamJAR.plist" log_file_dir 2> /dev/null)
    logFileName=$(/usr/bin/defaults read "/Library/Managed Preferences/uk.co.dataJAR.jamJAR.plist" log_file_name 2> /dev/null)
fi

if [ -f "/Library/Managed Preferences/uk.co.dataJAR.jamJAR.plist" ]
then
    logDir=$(/usr/bin/defaults read "/Library/Managed Preferences/uk.co.dataJAR.jamJAR.plist" log_file_dir 2> /dev/null)
    logFileName=$(/usr/bin/defaults read "/Library/Managed Preferences/uk.co.dataJAR.jamJAR.plist" log_file_name 2> /dev/null)
fi

if [ -z "${logDir-unset}" ]
then
    logDir="/var/log/"
fi

if [ -z "${logFileName-unset}" ]
then
    logFileName="jamJAR"
fi

if [[ "${logDir}" == */ ]]
then
    logFilePath="${logDir}""${logFileName}"".log"
else
    logFilePath="${logDir}""/""${logFileName}"".log"
fi

if [ -f "${logFilePath}" ]
then
    /bin/echo "<result>$(/usr/bin/tail -n -1 ${logFilePath})</result>"
else
    /bin/echo "<result></result>"
fi