def validate_amount(amount):
    """Check if amount is positive number"""
    try:
        return float(amount) > 0
    except:
        return False

def format_money(amount):
    """Format as currency"""
    return f"${amount:.2f}" 