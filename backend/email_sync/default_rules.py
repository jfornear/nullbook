DEFAULT_RULES = [
    {
        "name": "Receipt emails",
        "from_pattern": "receipt|invoice|order",
        "action": "process_receipt",
        "priority": 10,
    },
    {
        "name": "Amazon orders",
        "from_pattern": "auto-confirm@amazon|ship-confirm@amazon",
        "action": "process_receipt",
        "priority": 20,
    },
    {
        "name": "Uber receipts",
        "from_pattern": "uber.com",
        "action": "process_receipt",
        "priority": 20,
    },
    {
        "name": "DoorDash",
        "from_pattern": "doordash.com",
        "action": "process_receipt",
        "priority": 20,
    },
    {
        "name": "Venmo",
        "from_pattern": "venmo.com",
        "action": "process_receipt",
        "priority": 15,
    },
    {
        "name": "PayPal",
        "from_pattern": "paypal.com",
        "action": "process_receipt",
        "priority": 15,
    },
    {
        "name": "Bank statements",
        "subject_pattern": "statement|bill",
        "action": "process_receipt",
        "priority": 5,
    },
]
