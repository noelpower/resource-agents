#!/usr/bin/python

##
## Copyright (C) 2008 Red Hat, Inc. All Rights Reserved.
##
## The Following Agent Has Been Tested On:
##
##  Version            Firmware
## +-----------------+---------------------------+
##  WTI IPS-800-CE     v1.40h
##
#####

import sys, re, pexpect
sys.path.append("../lib/")
from fencing import *

def get_power_status(conn, options):
	try:
		conn.send("/S"+"\r\n")
		conn.log_expect(options, options["-c"], SHELL_TIMEOUT)
	except pexpect.EOF:
		fail(EC_CONNECTION_LOST)
	except pexpect.TIMEOUT:
		fail(EC_TIMED_OUT)
	
	plug_section = 0
	for line in conn.before.splitlines():
		if (plug_section == 2) and line.find("|") >= 0:
			plug_line = [x.strip().lower() for x in line.split("|")]
			if len(plug_line) < len(plug_header):
				plug_section = -1
				pass
			if options["-n"] == plug_line[plug_index]:
				return plug_line[status_index]
		elif (plug_section == 1):
			plug_section = 2
			pass
		elif (line.upper().startswith("PLUG")):
			plug_section = 1
			plug_header = [x.strip().lower() for x in line.split("|")]
			plug_index = plug_header.index("plug")
			status_index = plug_header.index("status")

	return "PROBLEM"

def set_power_status(conn, options):
	action = {
		'on' : "/on",
		'off': "/off"
	}[options["-o"]]

	try:
		conn.send(action + " " + options["-n"] + ",y\r\n")
		conn.log_expect(options, options["-c"], POWER_TIMEOUT)
	except pexcept.EOF:
		fail(EC_CONNECTION_LOST)
	except pexcept.TIMEOUT:
		fail(EC_TIMED_OUT)

def main():
	device_opt = [  "help", "version", "agent", "quiet", "verbose", "debug",
			"action", "ipaddr", "passwd", "passwd_script",
			"cmd_prompt", "port" ]

	options = check_input(device_opt, process_input(device_opt))

	## 
	## Fence agent specific defaults
	#####
	if 0 == options.has_key("-c"):
		options["-c"] = "IPS>"

	##
	## Login to system
	## @note: there is no username so we can't use fence_login()
	####
	try:
		conn = fspawn ('telnet ' + options["-a"])
		conn.log_expect(options, "Password: ", SHELL_TIMEOUT)
		conn.send(options["-p"]+"\r\n")
		conn.log_expect(options, options["-c"], SHELL_TIMEOUT)
	except pexpect.EOF:
		fail(EC_LOGIN_DENIED) 
	except pexpect.TIMEOUT:
		fail(EC_LOGIN_DENIED)

	##
	## Operate the fecing device
	######
	fence_action(conn, options, set_power_status, get_power_status)

	##
	## Logout from system
	######
	conn.send("/X,Y"+"\r\n")
	conn.close()

if __name__ == "__main__":
	main()