"""Code quality issue: duplicated logic."""

def total_for_a(items):
    total = 0
    for item in items:
        total += item["price"] * item["quantity"]
    return total


def total_for_b(products):
    total = 0
    for product in products:
        total += product["price"] * product["quantity"]
    return total
