"""Input and compatibility rules shared by form handlers."""
import re

AMOUNT = re.compile(r"[0-9]{1,6}(?:\.[0-9]{1,2})?")
SOCKET = re.compile(r"[A-Z0-9][A-Z0-9 -]{0,19}")
RAM_TYPES = {"DDR3", "DDR4", "DDR5"}
COMPATIBILITY_CATEGORIES = {"CPU", "Motherboard", "RAM"}
COMPATIBLE = "CPU socket and RAM generation match the motherboard."
MAX_SPECS = 120


def money_cents(raw):
    if not AMOUNT.fullmatch(raw):
        raise ValueError("Enter an amount from €0 to €100,000 with up to two decimal places.")
    whole, _, fraction = raw.partition(".")
    cents = int(whole) * 100 + int(fraction.ljust(2, "0"))
    if cents > 10_000_000:
        raise ValueError("Enter an amount from €0 to €100,000 with up to two decimal places.")
    return cents


def text_amount(cents):
    return f"{cents // 100}.{cents % 100:02d}"


def component_values(category, name, price, socket, ram_type):
    name = name.strip()
    socket = socket.strip().upper()
    ram_type = ram_type.strip().upper()
    if not 2 <= len(name) <= 80 or any(ord(char) < 32 for char in name):
        raise ValueError("Component name must contain 2–80 printable characters.")
    if category in {"CPU", "Motherboard"}:
        if not SOCKET.fullmatch(socket):
            raise ValueError("Enter a socket for CPUs and motherboards, such as AM5 or LGA1700.")
    elif socket:
        raise ValueError("Socket is used only for CPUs and motherboards.")
    if category in {"RAM", "Motherboard"}:
        if ram_type not in RAM_TYPES:
            raise ValueError("Select DDR3, DDR4 or DDR5 for RAM and motherboards.")
    elif ram_type:
        raise ValueError("Memory generation is used only for RAM and motherboards.")
    return name, money_cents(price), socket or None, ram_type or None


def clean_specs(raw):
    """Key specifications are one short line, with items separated by semicolons."""
    specs = " ".join(raw.split())
    if len(specs) > MAX_SPECS:
        raise ValueError(f"Key specifications must be {MAX_SPECS} characters or fewer.")
    return specs


def compatibility(items):
    """Return warnings and a short status based on the parts that are selected."""
    groups = {name: [] for name in COMPATIBILITY_CATEGORIES}
    for row in items:
        if row["category"] in groups:
            groups[row["category"]].append(row)
    if any(len(group) > 1 for group in groups.values()):
        return ["Remove duplicate CPU, motherboard or RAM selections before checking this build."], ""
    selected = {name: group[0] for name, group in groups.items() if group}
    board = selected.get("Motherboard")
    if board is None:
        return [], "Add a motherboard to check CPU socket and RAM generation."

    warnings = []
    checks = 0
    cpu = selected.get("CPU")
    memory = selected.get("RAM")
    if cpu and cpu["socket"] and board["socket"]:
        checks += 1
        if cpu["socket"] != board["socket"]:
            warnings.append(f"CPU socket {cpu['socket']} does not match motherboard socket {board['socket']}.")
    if memory and memory["ram_type"] and board["ram_type"]:
        checks += 1
        if memory["ram_type"] != board["ram_type"]:
            warnings.append(f"Memory {memory['ram_type']} does not match motherboard memory type {board['ram_type']}.")
    if checks == 2 and not warnings:
        return [], COMPATIBLE
    if checks < 2:
        return warnings, "Complete both checks by selecting a CPU and RAM with known specifications."
    return warnings, ""
