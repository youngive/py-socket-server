tags_to_replace = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    "'": '&apos;',
    '"': '&quot;'
}

def replace_tag(tag):
    return tags_to_replace.get(tag, tag)

def safe_tags_replace(s):
    return ''.join(replace_tag(char) for char in s)