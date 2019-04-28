"""
Multiplatform TCP/UDP port-knocker, with profile file support.

This program accepts the needed arguments from the command-line (IPv4 address,
interval in ms, and multiple port:proto pairs), or an INI-like profile file
with multiple profiles, plus a parameter specifying which one to run. The
format of the profile file is as follows:

[profile_name]
ipaddr = 1.2.3.4
interval = 500
ports = 111:TCP 222:TCP 333:UDP
"""

import argparse
import configparser
import os
import select
import socket
import sys
import time

__author__ = "Dorian Bolivar"
__email__ = "dorian@dorianbolivar.com"
__license__ = "GNU GPLv3"
__version__ = "1.0"


def parse_params(args: list):
    desc_msg = "Multiplatform TCP/UDP port-knocker, with profile file support."
    usage_msg = os.path.basename(__file__) + " [-h | --help] (-f pfile -l profile | -a ipaddr -i interval -p port:proto [port:proto ...])"
    parser = argparse.ArgumentParser(description=desc_msg, usage=usage_msg)
    parser._optionals.title = 'valid arguments'

    parser.add_argument("-f", dest="pfile", type=argparse.FileType("r"), help="file with port-knocking profiles")
    parser.add_argument("-l", dest="profile", type=str, help="profile to run")
    parser.add_argument("-a", dest="ipaddr", type=valid_ip, help="IP address to knock (IPv4 dotted-quad)")
    parser.add_argument("-i", dest="interval", type=valid_interval, help="interval between knocks (milliseconds)")
    parser.add_argument("-p", dest="ports", metavar="PORT", type=valid_ports, nargs="+", help="ports to knock (with protocol)")

    args = parser.parse_args(args)

    # Check argument combination, overcoming argparse's limitations for mutual exclusions.
    if (args.pfile and (args.profile is None or args.ipaddr or args.interval or args.ports)) or \
        (args.pfile is None and (args.profile or args.ipaddr is None or args.interval is None or args.ports is None)):
        parser.print_help()
        exit(1)

    return(args)


def valid_ip(ipaddr):
    try:
        if len(ipaddr.split(".")) == 4:
            socket.inet_aton(ipaddr)
        else:
            raise argparse.ArgumentTypeError("invalid IP address")
    except socket.error:
        raise argparse.ArgumentTypeError("error creating socket")
    
    return(ipaddr)


def valid_interval(interval):
    try:
        if (float(interval) <= 0):
            raise argparse.ArgumentTypeError("interval must be greater than 0")
    except ValueError:
        raise argparse.ArgumentTypeError("invalid interval")

    return(float(interval) / 1000)


def valid_ports(port):
    try:
        port_proto = port.split(":")

        # Port 0 is valid, but not for this purpose.
        if (int(port_proto[0]) <= 0) or (int(port_proto[0]) > 65535):
            raise argparse.ArgumentTypeError("ports must be between 1 and 65535")
        elif (port_proto[1].upper() != "UDP") and (port_proto[1].upper() != "TCP"):
            raise argparse.ArgumentTypeError("protocol must be UDP or TCP")
    except (ValueError, IndexError):
        raise argparse.ArgumentTypeError("invalid port:protocol in list")

    return(port)


args = parse_params(sys.argv[1:])

if args.pfile:
    try:
        with open(args.pfile.name, args.pfile.mode) as fd_pfile:
            config = configparser.ConfigParser()
            config.read_file(fd_pfile)

            if args.profile:
                profile = config[args.profile]
            else:
                exit(1)
                profile = config["bandit"]
            
            ipaddr = valid_ip(profile["ipaddr"])
            interval = valid_interval(profile["interval"])
            ports = [valid_ports(i) for i in profile["ports"].split(" ")]
    except argparse.ArgumentTypeError as exc:
        print(args.pfile.name + ": error: " + args.profile + ": " + str(exc))
        exit(1)
else:
    ipaddr = args.ipaddr
    interval = args.interval
    ports = args.ports

for port in ports:
    port_proto = port.split(":")

    print("Knocking on port", port_proto[0], port_proto[1].upper(), "at", ipaddr)

    try:
        if (port_proto[1].upper() == "UDP"):
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setblocking(False)
            sock.sendto(bytes(0), (ipaddr, int(port_proto[0])))
        else:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setblocking(False)
            sock.connect_ex((ipaddr, int(port_proto[0])))
            select.select([sock], [sock], [sock], 0.2)
    except socket.error:
        print(os.path.basename(__file__) + ": error: socket creation")
        exit(2)

    sock.close()
    time.sleep(interval)
