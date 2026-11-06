from datetime import datetime

def global_city_context(request):
    """
    Supplies ubiquitous civic data, emergency numbers, Lahore localities,
    and navigation taxonomies to all templates.
    """
    emergency_helplines = [
        {"name": "Rescue 1122", "code": "1122", "desc": "Emergency Medical, Fire & Rescue Service", "badge": "24/7 Life Safety"},
        {"name": "Lahore Police", "code": "15", "desc": "Capital City Police Emergency Response", "badge": "24/7 Law & Order"},
        {"name": "Edhi Ambulance", "code": "115", "desc": "Non-profit Ambulance & Welfare Service", "badge": "Ambulance"},
        {"name": "Traffic Police Helpline", "code": "1915", "desc": "City Traffic Police Lahore Road Inquiries", "badge": "Transit"},
        {"name": "WASA Complaint Cell", "code": "1334", "desc": "Water & Sanitation Drainage Emergencies", "badge": "Civic Utilities"},
        {"name": "LESCO Helpline", "code": "118", "desc": "Lahore Electric Supply Emergency Inquiries", "badge": "Power Grid"},
    ]

    city_localities = [
        {"name": "Gulberg", "slug": "gulberg", "zone": "Central & Commercial", "count": 142},
        {"name": "DHA (Defence)", "slug": "dha", "zone": "Eastern Suburbs", "count": 188},
        {"name": "Johar Town", "slug": "johar-town", "zone": "Western Commercial", "count": 115},
        {"name": "Walled City (Androon)", "slug": "walled-city", "zone": "Heritage Core", "count": 94},
        {"name": "Model Town", "slug": "model-town", "zone": "South-Central", "count": 68},
        {"name": "Mall Road & Civil Lines", "slug": "mall-road", "zone": "Colonial & Civic", "count": 76},
        {"name": "Lahore Cantt", "slug": "cantt", "zone": "Cantonment Sector", "count": 82},
        {"name": "Iqbal Town", "slug": "iqbal-town", "zone": "South-Western", "count": 55},
        {"name": "Bahria Town", "slug": "bahria-town", "zone": "Southern Gateway", "count": 63},
        {"name": "Faisal Town", "slug": "faisal-town", "zone": "Academic & Residential", "count": 41},
    ]

    top_categories = [
        {"title": "Tourist Places", "slug": "places", "icon": "bi-bank", "count": 48, "color": "emerald"},
        {"title": "Restaurants & Cafes", "slug": "restaurants", "icon": "bi-cup-hot", "count": 312, "color": "terracotta"},
        {"title": "Hospitals & 24/7 Care", "slug": "hospitals", "icon": "bi-hospital", "count": 64, "color": "danger"},
        {"title": "Education & Colleges", "slug": "education", "icon": "bi-mortarboard", "count": 89, "color": "primary"},
        {"title": "Lahore Jobs", "slug": "jobs", "icon": "bi-briefcase", "count": 156, "color": "info"},
        {"title": "Local Businesses", "slug": "businesses", "icon": "bi-shop", "count": 420, "color": "warning"},
        {"title": "Transport Guides", "slug": "transport", "icon": "bi-train-front", "count": 28, "color": "success"},
        {"title": "Local Events", "slug": "events", "icon": "bi-calendar-event", "count": 35, "color": "purple"},
        {"title": "City Updates & Smog", "slug": "updates", "icon": "bi-megaphone", "count": 18, "color": "dark"},
    ]

    return {
        'SITE_NAME': 'Lahore City Hub',
        'SITE_TAGLINE': 'Your Complete Guide to Lahore',
        'CURRENT_YEAR': datetime.now().year,
        'GLOBAL_EMERGENCY_HELPLINES': emergency_helplines,
        'GLOBAL_LOCALITIES': city_localities,
        'GLOBAL_CATEGORIES': top_categories,
        'CIVIC_SMOG_ADVISORY': {
            'level': 'Moderate (AQI 142)',
            'location': 'Gulberg & Mall Road',
            'recommendation': 'Sensitive groups should limit prolonged outdoor exertion.',
            'source': 'Punjab Environment Protection Agency (EPA)',
            'last_checked': 'Today, 09:30 AM PKT'
        }
    }
