"""Code quality issue: mutable default argument."""

def add_tag(tag, tags=[]):
    tags.append(tag)
    return tags
