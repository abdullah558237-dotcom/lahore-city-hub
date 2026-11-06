from django import template
from django.utils.safestring import mark_safe
import urllib.parse

register = template.Library()

@register.filter
def star_rating_html(rating_val):
    """
    Renders 5 Bootstrap star icons according to numeric rating (e.g. 4.8).
    """
    try:
        val = float(rating_val)
    except (ValueError, TypeError):
        val = 0.0

    full_stars = int(val)
    half_star = 1 if (val - full_stars) >= 0.5 else 0
    empty_stars = 5 - (full_stars + half_star)

    html = []
    for _ in range(full_stars):
        html.append('<i class="bi bi-star-fill text-warning"></i>')
    if half_star:
        html.append('<i class="bi bi-star-half text-warning"></i>')
    for _ in range(empty_stars):
        html.append('<i class="bi bi-star text-muted opacity-50"></i>')

    return mark_safe(''.join(html))

@register.filter
def format_pkr(value):
    """Formats numeric price into PKR representation with commas."""
    if value is None or value == "":
        return "Free"
    try:
        val = int(float(value))
        if val == 0:
            return "Free"
        return f"PKR {val:,}"
    except (ValueError, TypeError):
        return f"PKR {value}"

@register.filter
def whatsapp_link(phone_number, custom_text="Hello, I saw your listing on Lahore City Hub"):
    """Formats clean international WhatsApp click-to-chat URL."""
    if not phone_number:
        return "#"
    clean = "".join([c for c in str(phone_number) if c.isdigit()])
    if clean.startswith("0"):
        clean = "92" + clean[1:]
    msg = urllib.parse.quote(custom_text)
    return f"https://wa.me/{clean}?text={msg}"

@register.simple_tag
def active_nav(request, url_name):
    """Returns 'active' CSS class if current URL resolves to url_name."""
    try:
        from django.urls import resolve
        current_url_name = resolve(request.path_info).url_name
        if current_url_name == url_name:
            return 'active'
    except Exception:
        pass
    return ''
