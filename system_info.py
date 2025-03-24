#!/usr/bin/env python3

# Copyright (C) 2025 Matt Doyle
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

import cpuinfo
import datetime
import json
import math
import os
import platform
import psutil
import time

from rich import box
from rich.progress_bar import ProgressBar
from rich.table import Table
from rich.text import Text
from richmonokai import MonokaiConsole, FOREGROUND, ATTRIBUTE
from typing import Any, Optional
from urllib.request import urlopen


def BytesToHuman(num_bytes: int):
    """Converts an integer number of bytes into a human-readable string."""

    current_unit_size = 1024
    units = ["B", "K", "M", "G", "T", "P", "E", "Z", "Y"]

    for i, unit in enumerate(units):
        next_unit_size = math.pow(1024, i + 1)

        if num_bytes < next_unit_size or unit == units[-1]:
            num_units = num_bytes / current_unit_size
            return f"{num_units:.1f}{unit}"

        current_unit_size = next_unit_size


def SafeGet(d: dict, k: str) -> str:
    return str(d.get(k, "????"))


def LoadOsRelease() -> dict[str, str]:
    results = {}
    os_release_path = "/etc/os-release"

    if os.path.exists(os_release_path):
        with open(os_release_path, "r") as f:
            for line in f:
                if "=" in line:
                    pieces = line.split("=")
                    results[pieces[0].strip('" \n')] = pieces[1].strip('" \n')

    return results


def main():

    # Set up the rich Console.
    console = MonokaiConsole()
    console.show_cursor(False)

    # Set up the rich Table.
    table = Table(box=box.SIMPLE_HEAD, show_header=False)
    table.add_column(header=Text("Property"), style=FOREGROUND.GREEN + ATTRIBUTE.BOLD)
    table.add_column(header="Value")
    table.add_column(header="Bar")

    # Collect all of the system details to be used.
    with console.Status("Loading..."):
        cpu_info = cpuinfo.get_cpu_info()
        vmem = psutil.virtual_memory()
        root_partition = psutil.disk_usage("/")
        if_addrs = psutil.net_if_addrs()
        os_release = LoadOsRelease()

    # CPU section.
    table.add_row("cpu:", SafeGet(cpu_info, "brand_raw"))
    core_count = SafeGet(cpu_info, "count")
    core_speed = SafeGet(cpu_info, "hz_actual_friendly")
    table.add_row("cores:", f"{core_count} x {core_speed}")
    table.add_row("arch:", SafeGet(cpu_info, "arch_string_raw"))
    model_file = "/proc/device-tree/model"
    if os.path.exists(model_file):
        with open(model_file, "r") as f:
            model = f.read().strip()
        table.add_row("model:", model)
    table.add_section()

    # Memory section.
    mem_used = BytesToHuman(vmem.used)
    mem_total = BytesToHuman(vmem.total)
    table.add_row("mem:", f"{mem_used} / {mem_total}  ({vmem.percent:.1f}%)")
    table.add_section()

    # Disk section.
    disk_used = BytesToHuman(root_partition.used)
    disk_total = BytesToHuman(root_partition.total)
    table.add_row(
        f"disk:", f"{disk_used} / {disk_total} ({root_partition.percent:.1f}%)"
    )
    table.add_section()

    # Network section.
    for interface, addrs in if_addrs.items():
        values = []
        for a in addrs:
            if a.family.value == 2:  # AF_INET
                values.append(f"{a.address} ({a.netmask})")
        labels = [f"{interface}:"] + [""] * (len(values) - 1)
        for label, value in zip(labels, values):
            table.add_row(label, value)
    table.add_section()

    # Geolocation section.
    ip_info = json.load(urlopen("http://ipinfo.io/json"))
    public_ip = SafeGet(ip_info, "ip")
    city = SafeGet(ip_info, "city")
    region = SafeGet(ip_info, "region")
    country = SafeGet(ip_info, "country")
    table.add_row("public ip:", public_ip)
    table.add_row("location: ", f"{city}, {region}, {country}")
    table.add_section()

    # OS section.
    table.add_row(
        "os:",
        f"{os_release['NAME']} {os_release['VERSION_ID']} ({os_release['VERSION_CODENAME']})",
    )
    table.add_section()

    # Python section.
    table.add_row("python:", platform.python_version())
    table.add_section()

    # Uptime section.
    now_seconds = int(time.time())
    boot_seconds = psutil.boot_time()
    delta = datetime.timedelta(seconds=(now_seconds - boot_seconds))
    table.add_row("uptime:", str(delta))
    table.add_section()

    console.print(table)


if __name__ == "__main__":
    main()
