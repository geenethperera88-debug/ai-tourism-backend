from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json, os
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import smtplib
from email.message import EmailMessage
from reportlab.platypus import Image
from reportlab.lib.units import inch
import qrcode

app = Flask(__name__)
CORS(app)

USERS_FILE = "users.json"
TRIPS_FILE = "saved_trips.json"
BOOKINGS_FILE = "bookings.json"
DEST_FILE = "destinations_admin.json"
HOTEL_FILE = "admin_hotels.json"
AVAILABILITY_FILE = "hotel_availability.json"

GMAIL_USER = "yourgmail@gmail.com"
GMAIL_APP_PASSWORD = "your_app_password"
WEBSITE_URL = "http://localhost:5176"


def read_json(file):
    if not os.path.exists(file):
        return []
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def write_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def format_lkr(value):
    try:
        return f"LKR {int(float(value or 0)):,}"
    except:
        return "LKR 0"

def generate_pdf(booking):
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    )
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.enums import TA_CENTER
    import qrcode
    import os

    def money(value):
        try:
            return f"LKR {int(float(value or 0)):,}"
        except:
            return "LKR 0"

    filename = f"booking_{booking['booking_ref']}.pdf"
    qr_file = f"qr_{booking['booking_ref']}.png"

    website_url = "http://localhost:5176"
    logo_path = "assets/logo.png"

    qr = qrcode.make(f"{website_url}/my-trips")
    qr.save(qr_file)

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=32,
        bottomMargin=32,
    )

    styles = getSampleStyleSheet()

    title = ParagraphStyle(
        "title",
        parent=styles["Title"],
        fontSize=30,
        leading=36,
        textColor=colors.white,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    )

    subtitle = ParagraphStyle(
        "subtitle",
        parent=styles["Normal"],
        fontSize=11,
        leading=16,
        textColor=colors.HexColor("#bfdbfe"),
        alignment=TA_CENTER,
    )

    blueLabel = ParagraphStyle(
        "blueLabel",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#38bdf8"),
        fontName="Helvetica-Bold",
    )

    whiteText = ParagraphStyle(
        "whiteText",
        parent=styles["Normal"],
        fontSize=10,
        leading=15,
        textColor=colors.HexColor("#e2e8f0"),
    )

    darkText = ParagraphStyle(
        "darkText",
        parent=styles["Normal"],
        fontSize=10,
        leading=15,
        textColor=colors.HexColor("#0f172a"),
    )

    amountText = ParagraphStyle(
        "amountText",
        parent=styles["Normal"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#020617"),
        fontName="Helvetica-Bold",
    )

    sectionTitle = ParagraphStyle(
        "sectionTitle",
        parent=styles["Heading2"],
        fontSize=17,
        leading=22,
        textColor=colors.HexColor("#38bdf8"),
        fontName="Helvetica-Bold",
    )

    story = []

    # HEADER
    logo = Image(logo_path, width=0.9 * inch, height=0.36 * inch) if os.path.exists(logo_path) else ""

    header = Table(
        [
            [logo],
            [Paragraph("Plan&Go", title)],
            [Paragraph("Premium Travel Experience", sectionTitle)],
            [Paragraph("AI-powered Sri Lanka travel planning confirmation", subtitle)],
        ],
        colWidths=[6.55 * inch],
    )

    header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#020617")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#0ea5e9")),
        ("LINEBELOW", (0, -1), (-1, -1), 2.5, colors.HexColor("#38bdf8")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("PADDING", (0, 0), (-1, -1), 13),
    ]))

    story.append(header)
    story.append(Spacer(1, 16))

    # HOTEL DETAILS
    hotelCard = Table(
        [[
            Paragraph(
                f"""
                <font color="#38bdf8"><b>CONFIRMED HOTEL</b></font><br/><br/>
                <font size="16"><b>{booking.get("hotel", "Selected Hotel")}</b></font><br/><br/>
                Destination: {booking.get("destination", "Sri Lanka")}<br/>
                Booking Ref: {booking.get("booking_ref", "Confirmed")}<br/>
                Status: Confirmed
                """,
                whiteText,
            ),
            Paragraph(
                f"""
                <font color="#38bdf8"><b>STAY DETAILS</b></font><br/><br/>
                Check-in: {booking.get("date", "Flexible")} • 11:00 AM<br/>
                Check-out: {booking.get("checkoutDate", "Flexible")} • 11:00 AM<br/>
                Nights: {booking.get("nights", 1)}<br/>
                Travelers: {booking.get("travelers", 1)}
                """,
                whiteText,
            ),
        ]],
        colWidths=[3.25 * inch, 3.3 * inch],
    )

    hotelCard.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0f172a")),
        ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#1e293b")),
        ("LINEBELOW", (0, -1), (-1, -1), 2, colors.HexColor("#38bdf8")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#334155")),
        ("PADDING", (0, 0), (-1, -1), 15),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    story.append(hotelCard)
    story.append(Spacer(1, 18))

    # BUDGET VALUES
    budgetInfo = booking.get("budgetInfo", {}) or {}

    hotelPaid = money(booking.get("hotelTotal"))
    fullBudget = money(booking.get("tripBudget"))
    transport = money(budgetInfo.get("transport"))
    food = money(budgetInfo.get("food"))
    activities = money(budgetInfo.get("activities"))

    # FULL BUDGET HERO
    budgetHero = Table(
        [
            [Paragraph("FULL TRIP BUDGET", blueLabel)],
            [Paragraph(fullBudget, amountText)],
            [Paragraph("Complete estimated cost for hotel, food, activities and transport.", darkText)],
        ],
        colWidths=[6.55 * inch],
    )

    budgetHero.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#e0f2fe")),
        ("BOX", (0, 0), (-1, -1), 1.2, colors.HexColor("#38bdf8")),
        ("PADDING", (0, 0), (-1, -1), 14),
    ]))

    story.append(budgetHero)
    story.append(Spacer(1, 12))

    # SMALL BUDGET CARDS
    budgetCards = Table(
        [
            [
                Table([
                    [Paragraph("HOTEL PAID", blueLabel)],
                    [Paragraph(hotelPaid, amountText)],
                    [Paragraph("✓ Confirmed hotel payment", darkText)],
                ]),
                Table([
                    [Paragraph("TRANSPORT", blueLabel)],
                    [Paragraph(transport, amountText)],
                    [Paragraph("Estimated travel guidance", darkText)],
                ]),
            ],
            [
                Table([
                    [Paragraph("FOOD", blueLabel)],
                    [Paragraph(food, amountText)],
                    [Paragraph("Meal budget guidance", darkText)],
                ]),
                Table([
                    [Paragraph("ACTIVITIES", blueLabel)],
                    [Paragraph(activities, amountText)],
                    [Paragraph("Experience budget guidance", darkText)],
                ]),
            ],
        ],
        colWidths=[3.25 * inch, 3.3 * inch],
    )

    budgetCards.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("PADDING", (0, 0), (-1, -1), 13),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    story.append(budgetCards)
    story.append(Spacer(1, 20))

    # ITINERARY
    story.append(Paragraph("Night-by-Night Itinerary", sectionTitle))
    story.append(Spacer(1, 6))

    rows = []
    itinerary = booking.get("itinerary", []) or []

    if not itinerary:
        rows.append([
            Paragraph("<b>Night 1</b>", darkText),
            Paragraph("Plan details not available.", darkText),
        ])
    else:
        for index, item in enumerate(itinerary, start=1):
            plan = item.get("plan", "") if isinstance(item, dict) else str(item)
            rows.append([
                Paragraph(f"<b>Night {index}</b>", darkText),
                Paragraph(plan, darkText),
            ])

    itineraryTable = Table(rows, colWidths=[1.1 * inch, 5.45 * inch])
    itineraryTable.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e0f2fe")),
        ("BACKGROUND", (1, 0), (1, -1), colors.HexColor("#f8fafc")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("PADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    story.append(itineraryTable)
    story.append(Spacer(1, 20))

    # FOOD + ACTIVITIES
    foodItems = booking.get("food", []) or ["Local restaurant"]
    activityItems = booking.get("activities", []) or ["City tour", "Explore"]

    foodText = "<br/>".join([f"• {x}" for x in foodItems])
    activityText = "<br/>".join([f"• {x}" for x in activityItems])

    faTable = Table(
        [[
            Paragraph(
                f"<font color='#38bdf8'><b>FOOD SUGGESTIONS</b></font><br/><br/>{foodText}",
                whiteText,
            ),
            Paragraph(
                f"<font color='#38bdf8'><b>ACTIVITIES</b></font><br/><br/>{activityText}",
                whiteText,
            ),
        ]],
        colWidths=[3.25 * inch, 3.3 * inch],
    )

    faTable.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0f172a")),
        ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#1e293b")),
        ("LINEBELOW", (0, -1), (-1, -1), 2, colors.HexColor("#38bdf8")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#334155")),
        ("PADDING", (0, 0), (-1, -1), 15),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    story.append(faTable)
    story.append(Spacer(1, 18))

    # FOOTER
    qrImg = Image(qr_file, width=0.95 * inch, height=0.95 * inch)

    footer = Table(
        [[
            Paragraph(
                f"""
                <b>Plan&Go AI Travel Planner</b><br/>
                Website: {website_url}<br/>
                Scan QR code to return to your travel dashboard.
                """,
                darkText,
            ),
            qrImg,
        ]],
        colWidths=[5.25 * inch, 1.3 * inch],
    )

    footer.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eff6ff")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#93c5fd")),
        ("PADDING", (0, 0), (-1, -1), 12),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    story.append(footer)

    doc.build(story)

    if os.path.exists(qr_file):
        os.remove(qr_file)

    return filename


def safe_money(value):
    try:
        return int(float(value or 0))
    except:
        return 0


def safe_money(value):
    try:
        return int(float(value or 0))
    except:
        return 0
def send_email(to_email, pdf_file):
    if GMAIL_USER == "yourgmail@gmail.com" or GMAIL_APP_PASSWORD == "your_app_password":
        print("Email skipped: Gmail credentials not configured.")
        return

    msg = EmailMessage()
    msg["Subject"] = "Your Plan&Go Booking Confirmation"
    msg["From"] = GMAIL_USER
    msg["To"] = to_email
    msg.set_content("Your booking is confirmed. Please find your PDF booking confirmation attached.")

    with open(pdf_file, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="pdf",
            filename=os.path.basename(pdf_file),
        )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        smtp.send_message(msg)

@app.route("/generate-plan", methods=["POST"])
def generate_plan():
    data = request.json or {}

    destination = data.get("destination", "")
    nights = int(data.get("nights") or data.get("duration") or 1)
    travelers = int(data.get("travelers") or 1)

    destinations = read_json(DEST_FILE)
    dest = next((d for d in destinations if d.get("name") == destination), None)

    activities = dest.get("activities", []) if dest else ["City tour", "Explore"]
    food = dest.get("food", []) if dest else ["Local restaurant"]

    hotels = read_json(HOTEL_FILE)
    hotels = [h for h in hotels if h.get("destination") == destination]

    selectedHotel = hotels[0] if hotels else {
        "name": "Default Hotel",
        "destination": destination,
        "pricePerNight": 20000,
        "image": "",
        "description": "Default hotel for your travel plan."
    }

    itinerary = []
    for i in range(nights):
        itinerary.append({
            "day": i + 1,
            "plan": f"Day {i + 1}: Explore {destination}, enjoy activities and local food."
        })

    hotel_cost = int(selectedHotel.get("pricePerNight", 20000)) * nights
    food_cost = 5000 * nights * travelers
    activity_cost = 3000 * nights
    transport_cost = 10000
    estimate = hotel_cost + food_cost + activity_cost + transport_cost

    return jsonify({
        "destination": destination,
        "nights": nights,
        "duration": nights,
        "activities": activities,
        "food": food,
        "itinerary": itinerary,
        "hotels": hotels,
        "selectedHotel": selectedHotel,
        "budgetInfo": {
            "hotel": hotel_cost,
            "food": food_cost,
            "activities": activity_cost,
            "transport": transport_cost,
            "estimate": estimate
        }
    })


@app.route("/book", methods=["POST"])
def book():
    data = request.json or {}
    bookings = read_json(BOOKINGS_FILE)

    booking = {
        "id": len(bookings) + 1,
        "booking_ref": f"PG-{datetime.now().strftime('%Y%m%d')}-{len(bookings) + 1:04d}",
        "user": data.get("user"),
        "destination": data.get("destination"),
        "hotel": data.get("hotel"),
        "hotelImage": data.get("hotelImage"),
        "hotelDescription": data.get("hotelDescription"),
        "date": data.get("date"),
        "checkoutDate": data.get("checkoutDate"),
        "checkInTime": data.get("checkInTime", "11:00 AM"),
        "checkOutTime": data.get("checkOutTime", "11:00 AM"),
        "nights": data.get("nights"),
        "travelers": data.get("travelers"),
        "total": data.get("total"),
        "hotelTotal": data.get("hotelTotal"),
        "tripBudget": data.get("tripBudget"),
        "transport": data.get("transport"),
        "budgetLevel": data.get("budgetLevel"),
        "hotelCategory": data.get("hotelCategory"),
        "interest": data.get("interest"),
        "itinerary": data.get("itinerary", []),
        "food": data.get("food", []),
        "activities": data.get("activities", []),
        "budgetInfo": data.get("budgetInfo", {}),
        "fullPlan": data.get("fullPlan", {}),
        "status": "confirmed",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    bookings.append(booking)
    write_json(BOOKINGS_FILE, bookings)

    try:
        pdf_file = generate_pdf(booking)
        send_email(booking["user"], pdf_file)
    except Exception as e:
        print("PDF/email error:", e)

    return jsonify({
        "success": True,
        "booking": booking
    })


@app.route("/download/<booking_ref>", methods=["GET"])
def download_pdf(booking_ref):
    filename = f"booking_{booking_ref}.pdf"

    if not os.path.exists(filename):
        bookings = read_json(BOOKINGS_FILE)
        booking = next((b for b in bookings if b.get("booking_ref") == booking_ref), None)

        if not booking:
            return jsonify({"success": False, "message": "Booking not found"}), 404

        generate_pdf(booking)

    return send_file(filename, as_attachment=True)


@app.route("/my-bookings", methods=["GET"])
def my_bookings():
    user = request.args.get("user")
    bookings = read_json(BOOKINGS_FILE)
    return jsonify([b for b in bookings if b.get("user") == user])


@app.route("/save-trip", methods=["POST"])
def save_trip():
    data = request.json or {}
    trips = read_json(TRIPS_FILE)

    data["id"] = len(trips) + 1
    data["saved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    trips.append(data)
    write_json(TRIPS_FILE, trips)

    return jsonify({"success": True, "trip": data})


@app.route("/my-trips", methods=["GET"])
def my_trips():
    user = request.args.get("user")
    trips = read_json(TRIPS_FILE)
    return jsonify([t for t in trips if t.get("user") == user])


@app.route("/delete-trip/<int:id>", methods=["DELETE"])
def delete_trip(id):
    trips = read_json(TRIPS_FILE)
    trips = [t for t in trips if t.get("id") != id]
    write_json(TRIPS_FILE, trips)
    return jsonify({"success": True})


@app.route("/login", methods=["POST"])
def login():
    data = request.json or {}
    email = data.get("email", "")
    password = data.get("password", "")

    if email == "admin" and password == "admin123":
        return jsonify({
            "success": True,
            "user": {
                "id": 0,
                "name": "Admin",
                "email": "admin",
                "role": "admin"
            }
        })

    users = read_json(USERS_FILE)

    for user in users:
        if user.get("email") == email and user.get("password") == password:
            return jsonify({"success": True, "user": user})

    return jsonify({"success": False, "message": "Invalid email or password"}), 401


@app.route("/signup", methods=["POST"])
def signup():
    data = request.json or {}

    name = data.get("name", "")
    email = data.get("email", "")
    password = data.get("password", "")

    if not name or not email or not password:
        return jsonify({"success": False, "message": "All fields are required"}), 400

    users = read_json(USERS_FILE)

    for user in users:
        if user.get("email") == email:
            return jsonify({"success": False, "message": "Email already registered"}), 400

    new_user = {
        "id": len(users) + 1,
        "name": name,
        "email": email,
        "password": password,
        "role": "user",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    users.append(new_user)
    write_json(USERS_FILE, users)

    return jsonify({"success": True, "user": new_user})


@app.route("/admin/destinations", methods=["GET"])
def admin_destinations():
    return jsonify(read_json(DEST_FILE))


@app.route("/admin/add-destination", methods=["POST"])
def admin_add_destination():
    data = request.json or {}
    destinations = read_json(DEST_FILE)

    new_destination = {
        "id": len(destinations) + 1,
        "name": data.get("name", ""),
        "image": data.get("image", ""),
        "shortDescription": data.get("shortDescription", ""),
        "description": data.get("description", ""),
        "category": data.get("category", "Nature"),
        "bestTime": data.get("bestTime", ""),
        "location": data.get("location", ""),
        "activities": data.get("activities", []),
        "food": data.get("food", []),
        "map": data.get("map", ""),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    destinations.append(new_destination)
    write_json(DEST_FILE, destinations)

    return jsonify({"success": True, "destination": new_destination})


@app.route("/admin/delete-destination/<int:id>", methods=["DELETE"])
def admin_delete_destination(id):
    destinations = read_json(DEST_FILE)
    destinations = [d for d in destinations if d.get("id") != id]
    write_json(DEST_FILE, destinations)
    return jsonify({"success": True})


@app.route("/admin/hotels", methods=["GET"])
def admin_hotels():
    return jsonify(read_json(HOTEL_FILE))


@app.route("/admin/add-hotel", methods=["POST"])
def admin_add_hotel():
    data = request.json or {}
    hotels = read_json(HOTEL_FILE)

    price = int(data.get("pricePerNight") or 0)

    new_hotel = {
        "id": len(hotels) + 1,
        "name": data.get("name", ""),
        "destination": data.get("destination", ""),
        "category": data.get("category", "Medium"),
        "pricePerNight": price,
        "price": price,
        "price_per_night": price,
        "image": data.get("image", ""),
        "description": data.get("description", ""),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "owner": data.get("owner"),
    }

    hotels.append(new_hotel)
    write_json(HOTEL_FILE, hotels)

    return jsonify({"success": True, "hotel": new_hotel})


@app.route("/admin/delete-hotel/<int:id>", methods=["DELETE"])
def admin_delete_hotel(id):
    hotels = read_json(HOTEL_FILE)
    hotels = [h for h in hotels if h.get("id") != id]
    write_json(HOTEL_FILE, hotels)
    return jsonify({"success": True})


@app.route("/admin/users", methods=["GET"])
def admin_users():
    return jsonify(read_json(USERS_FILE))


@app.route("/admin/trips", methods=["GET"])
def admin_trips():
    return jsonify(read_json(TRIPS_FILE))


@app.route("/admin/bookings", methods=["GET"])
def admin_bookings():
    owner = request.args.get("owner")
    bookings = read_json(BOOKINGS_FILE)

    if owner:
        hotels = read_json(HOTEL_FILE)
        owner_hotels = [
            h.get("name") for h in hotels
            if h.get("owner") == owner
        ]

        bookings = [
            b for b in bookings
            if b.get("hotel") in owner_hotels
        ]

    return jsonify(bookings)


@app.route("/admin/create-staff", methods=["POST"])
def create_staff():
    data = request.json or {}
    users = read_json(USERS_FILE)

    name = data.get("name", "")
    email = data.get("email", "")
    password = data.get("password", "")

    if not name or not email or not password:
        return jsonify({
            "success": False,
            "message": "All fields required"
        }), 400

    # check if email already exists
    for u in users:
        if u.get("email") == email:
            return jsonify({
                "success": False,
                "message": "Email already exists"
            }), 400

    staff = {
        "id": len(users) + 1,
        "name": name,
        "email": email,
        "password": password,
        "role": "staff"
    }

    users.append(staff)
    write_json(USERS_FILE, users)

    return jsonify({
        "success": True,
        "staff": staff
    })

@app.route("/hotel-availability", methods=["GET"])
def get_hotel_availability():
    hotel_id = request.args.get("hotelId")
    data = read_json(AVAILABILITY_FILE)

    if hotel_id:
        data = [a for a in data if str(a.get("hotelId")) == str(hotel_id)]

    return jsonify(data)


@app.route("/set-hotel-availability", methods=["POST"])
def set_hotel_availability():
    data = request.json or {}
    availability = read_json(AVAILABILITY_FILE)

    hotel_id = data.get("hotelId")
    dates = data.get("dates", [])

    if not hotel_id or not isinstance(dates, list):
        return jsonify({"success": False, "message": "Hotel ID and dates are required"}), 400

    availability = [a for a in availability if str(a.get("hotelId")) != str(hotel_id)]

    availability.append({
        "hotelId": hotel_id,
        "hotelName": data.get("hotelName", ""),
        "owner": data.get("owner", ""),
        "dates": dates,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    })

    write_json(AVAILABILITY_FILE, availability)

    return jsonify({"success": True})

@app.route("/admin/create-admin", methods=["POST"])
def create_admin():
    data = request.json or {}
    users = read_json(USERS_FILE)

    email = data.get("email", "")
    password = data.get("password", "")

    if not email or not password:
        return jsonify({
            "success": False,
            "message": "Email and password required"
        }), 400

    for u in users:
        if u.get("email") == email:
            return jsonify({
                "success": False,
                "message": "Email already exists"
            }), 400

    new_user = {
        "id": len(users) + 1,
        "name": "Admin",
        "email": email,
        "password": password,
        "role": "admin",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    users.append(new_user)
    write_json(USERS_FILE, users)

    return jsonify({
        "success": True,
        "user": new_user
    })

@app.route("/admin/accounts", methods=["GET"])
def get_accounts():
    users = read_json(USERS_FILE)

    return jsonify([
        {
            "id": u.get("id"),
            "name": u.get("name", "No Name"),
            "email": u.get("email", ""),
            "role": u.get("role", "user")
        }
        for u in users
    ])

@app.route("/admin/delete-account/<int:id>", methods=["DELETE"])
def delete_account(id):
    users = read_json(USERS_FILE)

    new_users = [u for u in users if u.get("id") != id]

    if len(new_users) == len(users):
        return jsonify({
            "success": False,
            "message": "Account not found"
        }), 404

    write_json(USERS_FILE, new_users)

    return jsonify({
        "success": True,
        "message": "Account deleted"
    })


if __name__ == "__main__":
    app.run(debug=True)
