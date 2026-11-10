# Access Point Discovery

## Purpose

`discovery.py` locates access points compatible with the multicast discovery
protocol used by Intelbras devices and some Deliberant/Ubiquiti devices. It
sends requests on the local network and displays the devices that respond.

The script does not scan IP address ranges or search for Wi-Fi networks/SSIDs.
Discovery requires the device to be reachable over multicast and to respond to
one of the requests sent.

## Compatibility note

This script was created a long time ago and may not reflect current device
behavior. Firmware updates and new device implementations can change the
discovery protocol or response format, so some devices may not be detected or
their information may be parsed incorrectly.

## Requirements

- Python 3.
- A network interface connected to the access points' local network.
- UDP multicast allowed between the computer and the devices.

The script uses only Python's standard library; no additional dependencies
need to be installed.

## Running

From the directory, run:

```bash
python3 discovery.py
```

The program sends two UDP requests to multicast group `233.89.188.1` on port
`10001`, then waits for responses. Press `Ctrl+C` to stop it.

There are no command-line arguments or external configuration. The group,
port, and request codes are defined at the beginning of `discovery.py`.

## Output

For each recognized response, the script displays the manufacturer and product,
along with the source IP address, MAC address, version, and device-reported
port when provided. A device that responds to both discovery protocols can
appear twice, once for each response code; duplicate responses with the same
IP, MAC, and code are shown only once per run.

Incomplete or invalid responses are ignored and reported to standard error.
The shared zero-code response format, which carries model and version together
in a single field and does not provide a port or description, is also supported.
Manufacturer identification uses the model and description fields when
available, followed by the protocol code. Since Deliberant and Ubiquiti share
the zero code, the result may appear as
`Deliberant/Ubiquiti (shared protocol)`.

Example with a device responding to both discovery requests:

```text
Multicast discovery requests sent to 233.89.188.1:10001.
Waiting for responses; press Ctrl+C to stop.
Manufacturer: Intelbras | Product: AP 3000 AX
  IP: 192.168.1.47 | MAC: 00:1A:3F:0A:0A:01 | Version: v4.0.0 | Port: 443
Manufacturer: Deliberant/Ubiquiti (shared protocol) | Product: UAP-AC-LITE
  IP: 192.168.1.48 | MAC: 00:15:6D:1A:2B:3C | Version: 6.0.12
```

## Troubleshooting

- Make sure the computer and access points are on the appropriate local
  network and that UDP multicast is allowed.
- Check the computer's firewall rules, as well as client isolation or
  multicast filtering configured on the network.
- If no devices respond, confirm they support this discovery protocol; the
  script is not a substitute for a general network scan.
