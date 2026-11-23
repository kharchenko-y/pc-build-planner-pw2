"""Input and compatibility rules shared by form handlers."""
import re

AMOUNT = re.compile(r"[0-9]{1,6}(?:\.[0-9]{1,2})?")
SOCKET = re.compile(r"[A-Z0-9][A-Z0-9 -]{0,19}")
RAM_TYPES = {"DDR3", "DDR4", "DDR5"}
COMPATIBILITY_CATEGORIES = {"CPU", "Motherboard", "RAM"}
COMPATIBLE = "CPU socket and RAM generation match the motherboard."

# The seven slots of a build, in the order a builder usually chooses them.
CATEGORY_ORDER = ["CPU", "Motherboard", "RAM", "GPU", "Storage", "PSU", "Case"]
CATEGORY_LABELS = {
    "CPU": "Processor", "Motherboard": "Motherboard", "RAM": "Memory", "GPU": "Graphics card",
    "Storage": "Storage", "PSU": "Power supply", "Case": "Case",
}
CHOOSE_LABELS = {
    "CPU": "Choose a processor", "Motherboard": "Choose a motherboard", "RAM": "Choose memory",
    "GPU": "Choose a graphics card", "Storage": "Choose storage", "PSU": "Choose a power supply", "Case": "Choose a case",
}
# A build holds one part of each type, except storage, which can hold several drives.
SINGLE_CATEGORIES = {"CPU", "Motherboard", "RAM", "GPU", "PSU", "Case"}
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


def max_quantity(category):
    """RAM kits can be doubled and drives repeated; other parts are single units."""
    return {"RAM": 2, "Storage": 4}.get(category, 1)


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


def _name(row, fallback):
    try:
        return row["name"]
    except (KeyError, IndexError):
        return fallback


def _picked(items):
    groups = {name: [] for name in COMPATIBILITY_CATEGORIES}
    for row in items:
        if row["category"] in groups:
            groups[row["category"]].append(row)
    return groups


def check_rows(items):
    """Describe both supported checks: state is ok, bad or pending."""
    groups = _picked(items)
    cpu, board, memory = (groups[name][0] if groups[name] else None for name in ("CPU", "Motherboard", "RAM"))
    rows = []

    if cpu and board and cpu["socket"] and board["socket"]:
        if cpu["socket"] == board["socket"]:
            rows.append({"label": "CPU socket", "state": "ok",
                         "detail": f"Processor and motherboard both use {board['socket']}."})
        else:
            rows.append({"label": "CPU socket", "state": "bad", "detail": (
                f"{_name(cpu, 'The CPU')} uses socket {cpu['socket']}, which does not match the "
                f"{board['socket']} socket on {_name(board, 'the motherboard')}. "
                f"Choose a processor with socket {board['socket']} or a motherboard with socket {cpu['socket']}."
            )})
    else:
        missing = " and ".join(label for label, part in (("a CPU", cpu), ("a motherboard", board)) if not part)
        rows.append({"label": "CPU socket", "state": "pending",
                     "detail": f"Choose {missing or 'parts with a known socket'} to compare sockets."})

    if memory and board and memory["ram_type"] and board["ram_type"]:
        if memory["ram_type"] == board["ram_type"]:
            rows.append({"label": "Memory type", "state": "ok",
                         "detail": f"Memory kit and motherboard both use {board['ram_type']}."})
        else:
            rows.append({"label": "Memory type", "state": "bad", "detail": (
                f"{_name(memory, 'The memory kit')} is {memory['ram_type']} memory, which does not match the "
                f"{board['ram_type']} slots on {_name(board, 'the motherboard')}. "
                f"Choose a {board['ram_type']} kit or a {memory['ram_type']} motherboard."
            )})
    else:
        missing = " and ".join(label for label, part in (("memory", memory), ("a motherboard", board)) if not part)
        rows.append({"label": "Memory type", "state": "pending",
                     "detail": f"Choose {missing or 'parts with a known memory type'} to compare memory."})
    return rows


def compatibility(items):
    """Return warnings and a short status based on the parts that are selected."""
    groups = _picked(items)
    if any(len(group) > 1 for group in groups.values()):
        return ["Remove duplicate CPU, motherboard or RAM selections before checking this build."], ""
    if not groups["Motherboard"]:
        return [], "Add a motherboard to check CPU socket and RAM generation."
    rows = check_rows(items)
    warnings = [row["detail"] for row in rows if row["state"] == "bad"]
    checks = sum(row["state"] != "pending" for row in rows)
    if checks == 2 and not warnings:
        return [], COMPATIBLE
    if checks < 2:
        return warnings, "Complete both checks by selecting a CPU and RAM with known specifications."
    return warnings, ""


def compatibility_state(items):
    """One word for badges: issue, ok or incomplete."""
    warnings, status = compatibility(items)
    return "issue" if warnings else ("ok" if status == COMPATIBLE else "incomplete")


def part_fit(part, items):
    """How a catalogue part relates to the parts already chosen in other slots."""
    chosen = {row["category"]: row for row in items if row["category"] in COMPATIBILITY_CATEGORIES}
    category = part["category"]
    board = chosen.get("Motherboard")
    if category == "CPU" and board and board["socket"] and part["socket"]:
        if part["socket"] == board["socket"]:
            return "ok", f"Fits your {board['socket']} motherboard"
        return "bad", f"Needs socket {part['socket']}, your motherboard has {board['socket']}"
    if category == "RAM" and board and board["ram_type"] and part["ram_type"]:
        if part["ram_type"] == board["ram_type"]:
            return "ok", f"Matches your {board['ram_type']} motherboard"
        return "bad", f"Your motherboard takes {board['ram_type']}"
    if category == "Motherboard":
        fits, conflicts = [], []
        cpu, memory = chosen.get("CPU"), chosen.get("RAM")
        if cpu and cpu["socket"] and part["socket"]:
            (fits if cpu["socket"] == part["socket"] else conflicts).append(
                f"{cpu['socket']} CPU" if cpu["socket"] == part["socket"] else f"your CPU needs {cpu['socket']}")
        if memory and memory["ram_type"] and part["ram_type"]:
            (fits if memory["ram_type"] == part["ram_type"] else conflicts).append(
                f"{memory['ram_type']} memory" if memory["ram_type"] == part["ram_type"]
                else f"your memory is {memory['ram_type']}")
        if conflicts:
            return "bad", "Does not fit: " + " and ".join(conflicts)
        if fits:
            return "ok", "Fits your " + " and ".join(fits)
    return None
