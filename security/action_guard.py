DANGEROUS_KEYWORDS = [
    "delete all",
    "remove everything",
    "wipe",
    "format",
    "rm -rf",
    "erase disk"
]

def is_dangerous(command: str) -> bool:
    command = command.lower()
    return any(keyword in command for keyword in DANGEROUS_KEYWORDS)