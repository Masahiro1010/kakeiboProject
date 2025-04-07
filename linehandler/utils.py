import re

def parse_template_message(message):
    """
    例: 「弁当 2個」→ {'name': '弁当', 'quantity': 2}
    """
    match = re.match(r'^(.+?)\s*(\d+)\s*(個|本|枚|つ)?$', message.strip())
    if match:
        name = match.group(1)
        quantity = int(match.group(2))
        return {'name': name, 'quantity': quantity}
    return None