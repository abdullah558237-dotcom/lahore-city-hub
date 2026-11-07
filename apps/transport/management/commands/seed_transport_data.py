import datetime
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from apps.core.models import Locality
from apps.transport.models import TransitMode, TransitRoute, TransitStation, TransitGuide


class Command(BaseCommand):
    help = "Seeds verified public transit routes, stations, and travel guides for Lahore."

    def handle(self, *args, **options):
        self.stdout.write("Seeding Lahore Transit Information...")

        loc_anarkali = Locality.objects.filter(slug='walled-city').first()
        loc_gulberg = Locality.objects.filter(slug='gulberg-3').first()

        # 1. Transit Modes
        mode_train, _ = TransitMode.objects.get_or_create(
            name="Orange Line Metro Train",
            defaults={
                'slug': 'orange-line-metro-train',
                'icon_class': 'bi-train-front',
                'description': 'Pakistan\'s first automated rapid transit rail system operating across 27.1 km with 26 stations.',
                'is_active': True,
            }
        )

        mode_brt, _ = TransitMode.objects.get_or_create(
            name="Metrobus BRT (Green Line)",
            defaults={
                'slug': 'metrobus-brt',
                'icon_class': 'bi-bus-front',
                'description': 'Dedicated elevated and at-grade bus rapid transit corridor running from Shahdara to Gajjumata.',
                'is_active': True,
            }
        )

        mode_feeder, _ = TransitMode.objects.get_or_create(
            name="Speedo Feeder Bus Network",
            defaults={
                'slug': 'speedo-feeder-buses',
                'icon_class': 'bi-bus-front-fill',
                'description': 'Urban feeder bus network connecting residential, university, and market zones to rapid transit lines.',
                'is_active': True,
            }
        )

        today = datetime.date(2026, 11, 1)

        # 2. Transit Routes
        route_olmt, _ = TransitRoute.objects.get_or_create(
            route_code="OLMT-01",
            defaults={
                'mode': mode_train,
                'route_name': "Orange Line Metro Train (Ali Town to Dera Gujran)",
                'slug': "orange-line-metro-train",
                'origin_station': "Ali Town",
                'destination_station': "Dera Gujran",
                'total_stations': 26,
                'total_distance_km': 27.10,
                'operating_schedule': "06:00 AM – 10:00 PM Daily",
                'frequency': "Every 5–8 minutes in peak hours; 10–12 minutes off-peak",
                'fare_info': "PKR 20 for up to 4 km; PKR 25 (4–8 km); PKR 30 (8–12 km); PKR 35 (12–16 km); PKR 40 (16+ km).",
                'description': "The Orange Line is an automated rapid transit line in Lahore, Punjab, Pakistan. It connects Ali Town in the south-west to Dera Gujran in the north-east, serving over 250,000 daily commuters across high-density residential and historical districts.",
                'operator': "Punjab Masstransit Authority (PMA)",
                'source_url': "https://pma.punjab.gov.pk/orange_line_metro_train",
                'last_updated_date': today,
                'is_active': True,
                'is_featured': True,
            }
        )

        route_mb, _ = TransitRoute.objects.get_or_create(
            route_code="MB-01",
            defaults={
                'mode': mode_brt,
                'route_name': "Lahore Metrobus Green Line (Shahdara to Gajjumata)",
                'slug': "lahore-metrobus-green-line",
                'origin_station': "Shahdara",
                'destination_station': "Gajjumata",
                'total_stations': 27,
                'total_distance_km': 27.00,
                'operating_schedule': "06:00 AM – 10:30 PM Daily",
                'frequency': "Every 3–5 minutes during peak hours; articulated articulated fleet",
                'fare_info': "Flat PKR 30 per trip regardless of distance travelled, payable via PMA Metro Card or single-ride RFID token.",
                'description': "The Lahore Metrobus Green Line is a 27 km dedicated bus rapid transit corridor running along the Ferozepur Road axis, crossing through major commercial centres, educational institutions, and healthcare complexes.",
                'operator': "Punjab Masstransit Authority (PMA)",
                'source_url': "https://pma.punjab.gov.pk/lahore_metrobus_system",
                'last_updated_date': today,
                'is_active': True,
                'is_featured': True,
            }
        )

        route_speedo, _ = TransitRoute.objects.get_or_create(
            route_code="FDR-01",
            defaults={
                'mode': mode_feeder,
                'route_name': "Speedo Feeder Bus Network (Integrated Feeder System)",
                'slug': "speedo-feeder-bus-network",
                'origin_station': "Railway Station Hub",
                'destination_station': "Green Town / Bagrian",
                'total_stations': 32,
                'total_distance_km': 18.50,
                'operating_schedule': "06:00 AM – 11:00 PM Daily",
                'frequency': "Every 10–15 minutes",
                'fare_info': "PKR 20 – 25 per trip. Automated discounted / free transfer available within 30 minutes when tapping with PMA Metro Smart Card.",
                'description': "Air-conditioned urban feeder buses integrated with the Metrobus and Orange Line networks, operated jointly by PMA and Daewoo Express across 30+ regional routes.",
                'operator': "Punjab Masstransit Authority (PMA) & Daewoo",
                'source_url': "https://pma.punjab.gov.pk/lahore_feeder_bus_routes",
                'last_updated_date': today,
                'is_active': True,
                'is_featured': False,
            }
        )

        # 3. Orange Line Stations
        olmt_stations_data = [
            (1, "Ali Town", "علی ٹاؤن", True, False, False, "Southern terminal point near Raiwind Road and Thokar junction."),
            (2, "Thokar Niaz Baig", "ٹھوکر نیاز بیگ", False, False, True, "Junction for M-2 Motorway buses and Multan Road traffic."),
            (3, "Canal View", "کینال ویو", False, False, False, "Near Canal View Housing and PCSIR Phase 2."),
            (4, "Hanjarwal", "ہنجروال", False, False, False, "Commercial stretch on Multan Road."),
            (5, "Wahdat Road", "وحدت روڈ", False, False, False, "Feeder bus access to Allama Iqbal Town and Wahdat Colony."),
            (6, "Awan Town", "اعوان ٹاؤن", False, False, False, "Residential access for Awan Town and Saidpur."),
            (7, "Sabzazar", "سبزہ زار", False, False, True, "Serving Sabzazar Scheme and commercial plazas."),
            (8, "Shahnoor", "شاہ نور", False, False, False, "Near historic Shahnoor Studios and Multan Road."),
            (9, "Salahuddin Road", "صلاح الدین روڈ", False, False, False, "Near Mansoora and Multan Road markets."),
            (10, "Bund Road", "بند روڈ", False, False, False, "Yateem Khana Chowk and Southern Ring Road junction."),
            (11, "Samanabad", "سمن آباد", False, False, False, "Major commercial and residential hub in Samanabad."),
            (12, "Gulshan-e-Ravi", "گلشن راوی", False, False, False, "Access to Gulshan-e-Ravi and Moon Market."),
            (13, "Chauburji", "چوبرجی", False, False, True, "Historic Mughal monument Chauburji; ramp into underground section."),
            (14, "Anarkali", "انارکلی", False, True, True, "Underground central hub; walking interchange to Metrobus MAO College station and Mall Road."),
            (15, "Central (GPO)", "سنٹرل جی پی او", False, True, True, "Underground station serving High Court, GPO, and Mall Road."),
            (16, "Lakshmi", "لکشمی", False, False, True, "Mcleod Road food street and historic cinema district."),
            (17, "Railway Station", "ریلوے اسٹیشن", False, False, True, "Direct pedestrian walkway interchange with Pakistan Railways Lahore Junction."),
            (18, "Sultanpura", "سلطان پورہ", False, False, False, "Serving Sultanpura and GT Road approaches."),
            (19, "UET", "یو ای ٹی", False, False, False, "University of Engineering and Technology main campus entrance."),
            (20, "Baghbanpura", "باغبانپورہ", False, False, False, "Historic market and GT Road bazaar."),
            (21, "Shalamar Gardens", "شالامار باغ", False, False, True, "UNESCO World Heritage Site Shalamar Gardens gate entrance."),
            (22, "Pakistan Mint", "پاکستان منٹ", False, False, False, "Official currency mint and residential colony."),
            (23, "Mahmood Booti", "محمود بوٹی", False, False, False, "Near Lahore Ring Road Interchange."),
            (24, "Salamatpura", "سلامت پورہ", False, False, False, "Dense GT Road commercial and residential node."),
            (25, "Islam Park", "اسلام پارک", False, False, False, "East Lahore residential community."),
            (26, "Dera Gujran", "ڈیرہ گجراں", True, False, False, "North-eastern terminal and train depot/maintenance yard."),
        ]

        for num, name, urdu, is_term, is_under, is_inter, landmarks in olmt_stations_data:
            TransitStation.objects.get_or_create(
                route=route_olmt,
                station_number=num,
                defaults={
                    'station_name': name,
                    'urdu_name': urdu,
                    'slug': slugify(f"olmt-{name}"),
                    'locality': loc_anarkali if "Anarkali" in name or "Central" in name else loc_gulberg,
                    'is_terminal': is_term,
                    'is_underground': is_under,
                    'is_interchange': is_inter,
                    'interchange_details': "Interchange with Metrobus Green Line via pedestrian subway" if name == "Anarkali" else ("Direct interchange with Pakistan Railways" if name == "Railway Station" else ""),
                    'nearby_landmarks': landmarks,
                    'has_wheelchair_access': True,
                    'has_parking': is_term,
                    'source_url': "https://pma.punjab.gov.pk/orange_line_metro_train",
                    'last_verified_date': today,
                }
            )

        # 4. Key Metrobus Stations
        metrobus_stations_data = [
            (1, "Shahdara", "شاہدرہ", True, False, True, "Northern terminal across Ravi River bridge; northern intercity bus transfer."),
            (4, "Azadi Chowk", "آزادی چوک", False, False, True, "Elevated station overlooking Minar-e-Pakistan, Badshahi Mosque, and Lahore Fort."),
            (5, "Bhatti Chowk", "بھٹی چوک", False, False, True, "Direct gate to Data Darbar shrine and historic Bhati Gate."),
            (6, "Katchery", "کچہری", False, False, False, "District Courts, Commissioner Office, and Old Campus."),
            (7, "Civil Secretariat", "سول سیکرٹریٹ", False, False, False, "Punjab Government Headquarters and Church Road."),
            (8, "MAO College", "ایم اے او کالج", False, False, True, "Walking connection to Anarkali Orange Line underground station."),
            (10, "Qartaba Chowk", "قرطبہ چوک", False, False, True, "Mozang, Lytton Road, and Jail Road junction."),
            (12, "Ichhra", "اچھرہ", False, False, False, "Major retail fabric market and Ferozepur Road bazaar."),
            (13, "Canal", "کینال", False, False, True, "Ferozepur Road and Canal Bank Road junction."),
            (15, "Kalma Chowk", "کلمہ چوک", False, False, True, "Main Boulevard Gulberg entrance and business centre."),
            (16, "Model Town", "ماڈل ٹاؤن", False, False, False, "Model Town commercial circle and Metro cash & carry."),
            (27, "Gajjumata", "گجومتہ", True, False, True, "Southern terminal depot on Ferozepur Road; Kasur road transfer."),
        ]

        for num, name, urdu, is_term, is_under, is_inter, landmarks in metrobus_stations_data:
            TransitStation.objects.get_or_create(
                route=route_mb,
                station_number=num,
                defaults={
                    'station_name': name,
                    'urdu_name': urdu,
                    'slug': slugify(f"metrobus-{name}"),
                    'locality': loc_gulberg if "Kalma" in name or "Canal" in name else loc_anarkali,
                    'is_terminal': is_term,
                    'is_underground': is_under,
                    'is_interchange': is_inter,
                    'interchange_details': "Walking interchange with Orange Line at Anarkali" if name == "MAO College" else "",
                    'nearby_landmarks': landmarks,
                    'has_wheelchair_access': True,
                    'has_parking': is_term,
                    'source_url': "https://pma.punjab.gov.pk/lahore_metrobus_system",
                    'last_verified_date': today,
                }
            )

        # 5. Travel Advice & Guides
        guides_data = [
            (
                "How to Buy and Use Metro Smart Cards & RFID Tokens",
                "smart_cards",
                route_olmt,
                "Complete guide to purchasing permanent reloadable Punjab Masstransit cards, refundable RFID tokens, vending machines, and mobile wallet top-ups.",
                """### Getting Started with Lahore Transit Tickets

Lahore's rapid transit systems (both the Orange Line Metro Train and Green Line Metrobus) operate on a 100% cashless, automated fare collection (AFC) system managed by the Punjab Masstransit Authority (PMA).

#### 1. Single-Journey RFID Tokens
- **Where to buy:** Available at automated Ticket Vending Machines (TVMs) and manned ticket counters located in the concourse of every station.
- **Deposit / Validity:** Valid only on the day of issuance at the issuing station.
- **How to use:** Tap the token on the turnstile sensor gate to enter. When exiting at your destination, **drop the token into the gate slot** to open the turnstile.

#### 2. Punjab Masstransit Smart Card
- **Cost:** PKR 130 one-time card fee.
- **Where to purchase:** Available at customer service counters across all Orange Line and Metrobus stations.
- **Recharge:** Can be topped up at TVMs or counters in increments of PKR 50, 100, 200, 500, or 1000.
- **Transfer discount:** Using a smart card entitles passengers to automated discounted inter-modal transfers between Orange Line, Metrobus, and Speedo feeder buses when tapped within 30 minutes.
- **Tap protocol:** You must **tap in** upon entering and **tap out** upon exiting. Distance-based fares are deducted at the exit turnstile.
                """,
                "bi-credit-card-2-front",
                today,
                True,
                1
            ),
            (
                "Interchange Guide: Switching between Orange Line & Metrobus",
                "interchange",
                route_olmt,
                "Step-by-step instructions for pedestrian interchange between Anarkali Underground Station (Orange Line) and MAO College (Metrobus).",
                """### Transferring Between Rapid Transit Corridors

Lahore commuters frequently need to travel between the North-South corridor (Ferozepur Road / Metrobus) and the East-West corridor (Multan Road to GT Road / Orange Line).

#### Primary Interchange: Anarkali ↔ MAO College
- **Orange Line Station:** Anarkali (Station #14, Underground).
- **Metrobus Station:** MAO College (Station #8, At-grade).
- **Distance:** Approximately 350 meters on foot.
- **Connecting Path:** Follow the marked directional signage inside Anarkali Station towards Exit 1. A paved sidewalk connects directly along Lower Mall past MAO College main gate.
- **Transfer Window:** If you use a Punjab Masstransit Smart Card, your feeder/connecting ride receives an integrated transfer discount when tapped within 30 minutes of exiting the previous station.

#### Secondary Interchange: Railway Station
- The **Orange Line Railway Station stop (#17)** features direct covered pedestrian walkways connecting to the **Pakistan Railways Lahore Junction** platforms for nationwide intercity rail journeys.
                """,
                "bi-arrow-left-right",
                today,
                True,
                2
            ),
            (
                "Women, Senior Citizens & Accessible Travel in Lahore",
                "accessibility",
                route_olmt,
                "Dedicated ladies compartments, priority seating, elevators, tactile paving, and security provisions for vulnerable commuters.",
                """### Inclusive and Safe Commuting

The Punjab Masstransit Authority enforces strict safety and accessibility standards across all stations and trains in Lahore.

#### Ladies Reserved Sections
- **Orange Line:** The front carriage of every train set is designated exclusively for women and accompanied young children during all operating hours.
- **Metrobus:** The front half of every articulated bus has separate female-only entrance doors and seating. Male passengers entering these reserved zones are subject to fines by transit marshals.

#### Wheelchair & Special Needs Accessibility
- **Elevators & Escalators:** All elevated and underground stations are equipped with operational elevators connecting street level to concourse and platform levels.
- **Tactile Paving:** Continuous yellow tactile guidance pathways run from station entrances through turnstiles and directly to train/bus boarding doors.
- **Priority Seating:** Clearly labeled priority seats in every train carriage and bus for pregnant women, elderly passengers, and persons with disabilities.

#### Security & Surveillance
- Stations feature 24/7 CCTV surveillance, baggage scanning x-ray machines, and walk-through metal detectors monitored by the Punjab Police Transit Wing and private security personnel.
                """,
                "bi-person-heart",
                today,
                True,
                3
            ),
            (
                "Platform Safety, Luggage Rules & Transit Fines",
                "rules_safety",
                route_mb,
                "Essential passenger safety rules, platform screen doors, baggage limits, and prohibited items on Lahore rapid transit.",
                """### Platform Rules & Safety Regulations

To ensure smooth travel for over 400,000 daily passengers, all commuters must adhere to the official PMA transit code:

#### Key Rules to Remember:
1. **Stand Behind the Yellow Line:** On all platforms, passengers must remain behind the yellow warning line until the train or bus comes to a complete halt and doors open.
2. **Platform Screen Doors:** Orange Line underground stations feature automatic full-height screen doors that open synchronously with train doors. Never lean against or force doors open.
3. **No Food or Drinks:** Eating, drinking, chewing betel leaf (paan), and smoking or vaping are strictly prohibited inside stations and carriages.
4. **Baggage Allowance:** Passengers may carry personal hand luggage up to 15 kg. Hazardous materials, flammable liquids, open liquids, and commercial cargo are barred at security checkpoints.
5. **Emergency Stop:** Every platform and train carriage contains red emergency push-buttons and inter-com links to the driver/station master. Misuse is punishable by law.
                """,
                "bi-shield-check",
                today,
                False,
                4
            ),
            (
                "Peak Hours, Timing Advice & Speedo Feeder Routes",
                "commuter_tips",
                route_speedo,
                "Avoid peak congestion, understand feeder bus timetables, and plan multimodal journeys across suburban Lahore.",
                """### Commuter Advice & Navigating Rush Hours

#### Understanding Peak Hours in Lahore:
- **Morning Peak:** 07:30 AM – 09:30 AM (School, college, and civil secretariat rush).
- **Evening Peak:** 04:30 PM – 07:30 PM (Office closing and commercial bazaar traffic).
- **Tip:** If traveling with heavy bags or senior family members, travel between 10:30 AM and 03:30 PM for a much quieter experience with open seating.

#### Operating Timetable:
- **Orange Line:** 06:00 AM – 10:00 PM Daily (First train departs terminals at 06:00 AM; last train departs at 10:00 PM sharp).
- **Metrobus:** 06:00 AM – 10:30 PM Daily.
- **Speedo Buses:** 06:00 AM – 11:00 PM Daily.

#### Official Helplines:
- **PMA Transit Helpline:** `042-111-222-627`
- **Rescue 1122:** For medical or platform emergencies
                """,
                "bi-clock-history",
                today,
                False,
                5
            ),
        ]

        for title, cat, route, summary, content, icon, vdate, feat, order in guides_data:
            TransitGuide.objects.get_or_create(
                slug=slugify(title),
                defaults={
                    'title': title,
                    'category': cat,
                    'route': route,
                    'summary': summary,
                    'content': content,
                    'icon_class': icon,
                    'source_url': "https://pma.punjab.gov.pk",
                    'last_verified_date': vdate,
                    'is_published': True,
                    'is_featured': feat,
                    'display_order': order,
                }
            )

        self.stdout.write(self.style.SUCCESS("Successfully seeded Lahore transit information!"))
