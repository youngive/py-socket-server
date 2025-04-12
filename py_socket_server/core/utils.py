tags_to_replace = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    "'": '&apos;',
    '"': '&quot;'
}

def replace_tag(tag: str) -> str:
    """Replaces special characters with XML entities"""
    return tags_to_replace.get(tag, tag)

def safe_tags_replace(s: str) -> str:
    """Escapes special characters in a string for safe use in XML"""
    if not isinstance(s, str):
        raise TypeError("Input must be a string")
    return ''.join([replace_tag(char) for char in s])