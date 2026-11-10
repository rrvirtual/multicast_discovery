#!/usr/bin/env python3

"""Discover devices compatible with the local multicast protocol."""

import socket
import struct
import sys
from typing import Dict, Tuple

MCAST_GRP = "233.89.188.1"
MCAST_PORT = 10001

DATA_ITB = struct.pack("!4B", 0x49, 0x54, 0x42, 0x53)
DATA_DLB = struct.pack("!4B", 0x00, 0x00, 0x00, 0x00)
data_itb = DATA_ITB
data_dlb = DATA_DLB


def _read(data: bytes, offset: int, size: int, field: str) -> Tuple[bytes, int]:
    end = offset + size
    if end > len(data):
        raise ValueError("incomplete response while reading {}".format(field))
    return data[offset:end], end


def _read_length_prefixed_text(
    data: bytes, offset: int, field: str ) -> Tuple[str, int]:
    raw_length, offset = _read(data, offset, 2, "{} length".format(field))
    length = int.from_bytes(raw_length, byteorder="big")
    raw_text, offset = _read(data, offset, length, field)
    return raw_text.decode("utf-8", errors="replace").strip("\x00 "), offset


def _format_mac(raw_mac: bytes) -> str:
    return ":".join("{:02X}".format(part) for part in raw_mac)


def _identify_manufacturer(code: bytes, model: str, description: str) -> str:
    identity = "{} {}".format(model, description).casefold()
    if "intelbras" in identity:
        return "Intelbras"
    if "deliberant" in identity:
        return "Deliberant"
    if "ubiquiti" in identity or "ubnt" in identity:
        return "Ubiquiti"
    if code == b"IB" or code == DATA_ITB:
        return "Intelbras"
    if code in (b"\x00\x00", DATA_DLB):
        return "Deliberant/Ubiquiti (shared protocol)"
    return "Unidentified"


def parse_device_response(data: bytes) -> Dict[str, object]:
    offset = 0
    code, offset = _read(data, offset, 2, "code")
    raw_mac, offset = _read(data, offset, 6, "MAC")
    raw_mac_source, offset = _read(data, offset, 6, "MAC de origem")

    if code == b"\x00\x00":
        identity, offset = _read_length_prefixed_text(data, offset, "identity")
        model, separator, version_suffix = identity.partition(".v")
        version = "v{}".format(version_suffix) if separator else ""
        if not separator:
            model = identity
        manufacturer = _identify_manufacturer(code, model, "")
        return {
            "cod": code.hex(),
            "mac": _format_mac(raw_mac),
            "mac_source": _format_mac(raw_mac_source),
            "model": model,
            "product": model or "Product not provided",
            "manufacturer": manufacturer,
            "version": version,
            "port": None,
            "description": "",
        }

    model, offset = _read_length_prefixed_text(data, offset, "model")
    version, offset = _read_length_prefixed_text(data, offset, "version")

    raw_port, offset = _read(data, offset, 2, "port")
    port = int.from_bytes(raw_port, byteorder="big")

    raw_description_length, offset = _read(data, offset, 2, "description length")
    description_length = int.from_bytes(raw_description_length, byteorder="big")
    raw_description, offset = _read(data, offset, description_length, "description")
    description = raw_description.decode("utf-8", errors="replace").strip("\x00 ")

    manufacturer = _identify_manufacturer(code, model, description)
    product = model or description or "Product not provided"
    return {
        "cod": code.hex(),
        "mac": _format_mac(raw_mac),
        "mac_source": _format_mac(raw_mac_source),
        "model": model,
        "product": product,
        "manufacturer": manufacturer,
        "version": version,
        "port": port,
        "description": description,
    }


def binaryToDevice(data: bytes) -> Dict[str, object]:
    """Compatibility for scripts that imported the legacy name."""
    return parse_device_response(data)


def _format_device(address: Tuple[str, int], device: Dict[str, object]) -> str:
    details = [
        "IP: {}".format(address[0]),
        "MAC: {}".format(device["mac"]),
        "Version: {}".format(device["version"] or "not provided"),
    ]
    if device["port"] is not None:
        details.append("Port: {}".format(device["port"]))
    return (
        "Manufacturer: {manufacturer} | Product: {product}\n"
        "  {details}"
    ).format(
        manufacturer=device["manufacturer"],
        product=device["product"],
        details=" | ".join(details),
    )


def main() -> None:
    seen = set()
    probes = (DATA_ITB, DATA_DLB)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
        sock.settimeout(1.0)
        for probe in probes:
            sock.sendto(probe, (MCAST_GRP, MCAST_PORT))

        print(
            "Multicast discovery requests sent to {}:{}.".format(
                MCAST_GRP, MCAST_PORT
            )
        )
        print("Waiting for responses; press Ctrl+C to stop.")

        while True:
            try:
                data, address = sock.recvfrom(1024)
            except socket.timeout:
                continue
            except OSError as error:
                print("Error receiving multicast response: {}".format(error), file=sys.stderr)
                raise

            try:
                device = parse_device_response(data)
            except ValueError as error:
                print(
                    "Invalid response from {}:{}: {}".format(
                        address[0], address[1], error
                    ),
                    file=sys.stderr,
                )
                continue

            key = (address[0], device["mac"], device["cod"])
            if key in seen:
                continue
            seen.add(key)
            print(_format_device(address, device), flush=True)


def run() -> None:
    try:
        main()
    except KeyboardInterrupt:
        print("\nDiscovery stopped.")


if __name__ == "__main__":
    run()
