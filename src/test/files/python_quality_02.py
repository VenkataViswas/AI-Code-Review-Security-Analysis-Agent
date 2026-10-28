"""Code quality issue: overly long function with many responsibilities."""

def process_order(order, customer, inventory, payment, emailer, logger):
    logger.info("Starting order")
    if not order:
        logger.error("Missing order")
        return None
    subtotal = 0
    for item in order:
        if item["quantity"] <= 0:
            logger.warning("Invalid quantity")
            return None
        subtotal += item["price"] * item["quantity"]
    tax = subtotal * 0.1
    total = subtotal + tax
    if customer.get("discount"):
        total -= total * customer["discount"]
    if inventory.available(order):
        inventory.reserve(order)
        if payment.charge(customer, total):
            emailer.send_receipt(customer, total)
            logger.info("Order completed")
            return {"subtotal": subtotal, "tax": tax, "total": total}
        logger.error("Payment failed")
        inventory.release(order)
        return None
    logger.error("Inventory unavailable")
    return None
