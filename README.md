# Python Port-Knocker
Multiplatform TCP/UDP port-knocker, with profile file support.

This program accepts the needed arguments from the command-line (IPv4 address,
interval in ms, and multiple port:proto pairs), or an INI-like profile file
with multiple profiles, plus a parameter specifying which one to run. The
format of the profile file is as follows:

~~~~
[profile_name]
ipaddr = 1.2.3.4
interval = 500
ports = 111:TCP 222:TCP 333:UDP
~~~~
