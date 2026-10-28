"""Mixed: reflected XSS risk in a simple HTML response and poor input validation."""

def profile_html(display_name):
    # Unsafe if display_name is controlled by a user and inserted into a browser response.
    if display_name is None:
        display_name = ""
    return "<h1>Welcome " + display_name + "</h1>"
