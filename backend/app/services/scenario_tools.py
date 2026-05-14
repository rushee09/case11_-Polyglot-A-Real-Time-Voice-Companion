import re
import json
from typing import Dict, Any, List, Optional

# ─── OpenAI-compatible tool schemas ─────────────────────────────────────────
# The LLM reads these schemas and decides when to call each tool.
# Tools are NOT pre-called by the backend; the LLM drives all tool invocations.

TOOL_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "lookup_order",
            "description": (
                "Look up the status, expected delivery time, tracking information, "
                "and refund policy for a customer order. Call this whenever the user "
                "mentions an order ID or asks about delivery, tracking, or a refund."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The numeric order ID (e.g. '4421')",
                    },
                    "email": {
                        "type": "string",
                        "description": "Customer email for account verification (optional)",
                    },
                },
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_hotels",
            "description": (
                "Search for available hotels in a city with optional budget and guest count filters. "
                "Use this when the user wants to find or book accommodation in a specific city."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name to search in (e.g. 'Bangalore')",
                    },
                    "budget": {
                        "type": "number",
                        "description": "Maximum budget per night in INR (optional)",
                    },
                    "people": {
                        "type": "integer",
                        "description": "Number of guests (optional)",
                    },
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": (
                "Get the current weather conditions for a city. Call this each time "
                "the user asks about weather in a specific city — including follow-up "
                "questions like 'and in Delhi?' or '¿Y en Chennai?'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Name of the city (e.g. 'Mumbai', 'Delhi', 'Chennai')",
                    },
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "plan_trip",
            "description": (
                "Generate a detailed day-by-day travel itinerary for a given destination. "
                "Call this when you have the destination, number of days, budget, and "
                "number of travelers. If any of these are missing, ask the user first."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {
                        "type": "string",
                        "description": "The destination country, region, or city (e.g. 'Georgia', 'Paris', 'Goa')",
                    },
                    "days": {
                        "type": "integer",
                        "description": "Total number of days for the trip",
                    },
                    "budget": {
                        "type": "string",
                        "description": "Budget description, e.g. '$1000 total', '₹50000 per person', 'mid-range', 'budget'",
                    },
                    "people": {
                        "type": "integer",
                        "description": "Number of travelers",
                    },
                },
                "required": ["destination", "days", "budget", "people"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "confirm_food_order",
            "description": (
                "Confirm and record a food order. Call this when the user places a "
                "food order, e.g. pizza, and specifies preferences or add-ons."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "item": {
                        "type": "string",
                        "description": "The food item being ordered (e.g. 'pizza')",
                    },
                    "preference": {
                        "type": "string",
                        "description": "Dietary preference, e.g. 'vegetarian' (optional)",
                    },
                    "add_on": {
                        "type": "string",
                        "description": "Any add-on items, e.g. 'coke' (optional)",
                    },
                },
                "required": ["item"],
            },
        },
    },
]


def execute_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Dispatch a tool call by name and return its result as a plain dict."""
    if name == "lookup_order":
        return lookup_order(
            str(args.get("order_id", "")),
            args.get("email"),
        )
    if name == "search_hotels":
        return search_hotels(
            str(args.get("city", "")),
            args.get("budget"),
            args.get("people"),
        )
    if name == "get_weather":
        return get_weather(str(args.get("city", "")))
    if name == "confirm_food_order":
        return pizza_order_context(
            str(args.get("item", "pizza")),
            str(args.get("preference", "")),
            str(args.get("add_on", "")),
        )
    if name == "plan_trip":
        return plan_trip(
            str(args.get("destination", "")),
            int(args.get("days", 3)),
            str(args.get("budget", "mid-range")),
            int(args.get("people", 1)),
        )
    return {"error": f"Unknown tool: {name}"}


def lookup_order(order_id: str, email: Optional[str] = None) -> Dict[str, Any]:
    """Mock order lookup tool."""
    if str(order_id).strip() == "4421":
        result = {
            "found": True,
            "order_id": "4421",
            "email": "rahul@example.com",
            "status": "Out for delivery",
            "expected_delivery": "Tomorrow by 6 PM",
            "refund_policy": (
                "Refund can be requested if delivery misses the promised delivery window."
            ),
            "tracking_link_status": "Tracking link can be sent to the verified email.",
        }
        if email and email.strip().lower() == "rahul@example.com":
            result["email_verified"] = True
        else:
            result["email_verified"] = False
        return result
    return {"found": False, "error": "Order not found"}


def search_hotels(
    city: str, budget: Optional[float] = None, people: Optional[int] = None
) -> Dict[str, Any]:
    """Mock hotel search tool."""
    city_lower = city.lower() if city else ""
    if "bangalore" in city_lower or "bengaluru" in city_lower:
        options = [
            {
                "index": 1,
                "name": "Indiranagar Comfort Stay",
                "price_per_night": 4200,
                "currency": "INR",
                "location": "Indiranagar",
                "rating": 4.2,
            },
            {
                "index": 2,
                "name": "MG Road Business Inn",
                "price_per_night": 4800,
                "currency": "INR",
                "location": "MG Road",
                "rating": 4.5,
            },
            {
                "index": 3,
                "name": "Koramangala Studio Hotel",
                "price_per_night": 4500,
                "currency": "INR",
                "location": "Koramangala",
                "rating": 4.3,
            },
        ]
        if budget:
            options = [o for o in options if o["price_per_night"] <= budget]
        return {
            "found": True,
            "city": "Bangalore",
            "options": options,
            "budget": budget,
            "people": people,
        }
    return {"found": False, "error": "No hotels found for that city in demo data"}


def get_weather(city: str) -> Dict[str, Any]:
    """Mock weather tool."""
    weather_data = {
        "mumbai": {
            "city": "Mumbai",
            "temperature": "31°C",
            "condition": "Humid, coastal breeze",
            "humidity": "85%",
        },
        "delhi": {
            "city": "Delhi",
            "temperature": "34°C",
            "condition": "Dry and hot",
            "humidity": "40%",
        },
        "chennai": {
            "city": "Chennai",
            "temperature": "32°C",
            "condition": "Humid and breezy",
            "humidity": "80%",
        },
    }
    key = city.lower().strip()
    if key in weather_data:
        return {"found": True, **weather_data[key]}
    return {"found": False, "error": f"No weather data for {city}"}


def pizza_order_context(item: str = "pizza", preference: str = "vegetarian", add_on: str = "") -> Dict[str, Any]:
    """Mock pizza/food order context."""
    order = {"item": item, "preference": preference}
    if add_on:
        order["add_on"] = add_on
    return {"found": True, "order": order}


# ─── Destination knowledge base ──────────────────────────────────────────────

_DESTINATIONS: Dict[str, Any] = {
    "georgia": {
        "display_name": "Georgia (Country)",
        "capital": "Tbilisi",
        "currency": "Georgian Lari (GEL) — 1 USD ≈ 2.7 GEL",
        "language": "Georgian; English widely understood in tourist areas",
        "best_time": "May–June and September–October (warm, not crowded)",
        "visa": "Visa-free for most nationalities for up to 365 days",
        "highlights": [
            {
                "place": "Tbilisi",
                "description": "Charming Old Town (Kala), Narikala Fortress, sulphur bathhouses, Rustaveli Avenue, vibrant food & wine scene",
                "recommended_days": 2,
            },
            {
                "place": "Kazbegi (Stepantsminda)",
                "description": "Stunning Caucasus mountains, Gergeti Trinity Church perched at 2,170 m, hiking trails, snow-capped peaks",
                "recommended_days": 1,
            },
            {
                "place": "Signagi & Kakheti",
                "description": "Georgia's wine heartland — medieval walled town, traditional qvevri wine, Bodbe Monastery, rolling vineyards",
                "recommended_days": 1,
            },
            {
                "place": "Batumi",
                "description": "Subtropical Black Sea resort city, botanical gardens, Ali & Nino sculpture, lively boulevard and beaches",
                "recommended_days": 1,
            },
            {
                "place": "Vardzia",
                "description": "Magnificent 12th-century cave monastery carved into a cliff face, over 3,000 rooms and a church with original frescoes",
                "recommended_days": 1,
            },
        ],
        "food_must_try": ["Khinkali (dumplings)", "Khachapuri (cheese bread)", "Churchkhela", "Georgian wine", "Mtsvadi (grilled skewers)"],
        "transport": "Marshrutkas (shared minibuses) between cities are cheap (~$2–5). Taxis & Bolt app in cities.",
        "accommodation_range": "Hostel $15–25/night · Guesthouse $30–60/night · Boutique hotel $80–150/night",
    },
    "goa": {
        "display_name": "Goa, India",
        "capital": "Panaji",
        "currency": "Indian Rupee (INR)",
        "language": "Konkani, English, Hindi",
        "best_time": "November–February (dry season)",
        "visa": "Indian visa required for most international visitors",
        "highlights": [
            {"place": "North Goa (Calangute, Anjuna, Vagator)", "description": "Famous beaches, beach shacks, nightlife, flea markets", "recommended_days": 2},
            {"place": "South Goa (Palolem, Agonda)", "description": "Quieter, pristine beaches, kayaking, dolphin watching", "recommended_days": 2},
            {"place": "Panaji & Old Goa", "description": "Portuguese colonial architecture, Se Cathedral, spice plantations, casinos", "recommended_days": 1},
        ],
        "food_must_try": ["Fish curry rice", "Prawn balchão", "Bebinca", "Feni", "Sorpotel"],
        "transport": "Scooter rental ₹300–400/day; taxis widely available",
        "accommodation_range": "Budget beach hut ₹800–1500/night · Mid-range hotel ₹2500–5000/night · Resort ₹8000+/night",
    },
}


def _build_day_plan(highlights: List[Dict[str, Any]], days: int) -> List[Dict[str, Any]]:
    """Distribute highlights across available days."""
    itinerary = []
    day = 1
    for h in highlights:
        if day > days:
            break
        slots = min(h["recommended_days"], days - day + 1)
        if slots == 1:
            itinerary.append({"day": day, "place": h["place"], "focus": h["description"]})
        else:
            for s in range(slots):
                label = "Arrival & first impressions" if s == 0 else "Deeper exploration"
                itinerary.append({"day": day + s, "place": h["place"], "focus": label + " — " + h["description"]})
        day += slots
    # Fill remaining days with free/flex time at last destination
    while day <= days:
        last_place = itinerary[-1]["place"] if itinerary else "destination"
        itinerary.append({"day": day, "place": last_place, "focus": "Leisure, local markets, spontaneous exploration"})
        day += 1
    return itinerary


def plan_trip(destination: str, days: int, budget: str, people: int) -> Dict[str, Any]:
    """Generate a day-by-day travel itinerary for any destination."""
    dest_lower = destination.lower().strip()

    # Match against known destinations
    matched_key = next((k for k in _DESTINATIONS if k in dest_lower or dest_lower in k), None)

    if matched_key:
        d = _DESTINATIONS[matched_key]
        day_plan = _build_day_plan(d["highlights"], days)
        return {
            "found": True,
            "destination": d["display_name"],
            "days": days,
            "people": people,
            "budget": budget,
            "currency_info": d["currency"],
            "language_info": d["language"],
            "best_time_to_visit": d["best_time"],
            "visa_info": d["visa"],
            "day_by_day": day_plan,
            "must_try_food": d["food_must_try"],
            "transport_tip": d["transport"],
            "accommodation_range": d["accommodation_range"],
        }

    # Generic fallback for unknown destinations
    return {
        "found": True,
        "destination": destination,
        "days": days,
        "people": people,
        "budget": budget,
        "day_by_day": [
            {"day": i + 1, "place": destination, "focus": f"Day {i+1}: Explore local culture, attractions, and cuisine"}
            for i in range(days)
        ],
        "tips": [
            "Check visa and entry requirements before booking",
            "Book flights and accommodation well in advance",
            "Research local customs and currency",
        ],
    }


# ─── Entity extraction from text ────────────────────────────────────────────

def extract_entities_from_text(text: str, memory_entities: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract universal entities from any user message.
    Domain-specific data (hotel details, trip parameters, food items) is handled
    by the LLM's tool_cache — not extracted here.
    """
    updated = dict(memory_entities)

    # ── User name (English / Hindi / Spanish) ───────────────────────────────
    if not updated.get("user_name"):
        for pattern in [
            r"(?:my name is|i am|i'm|call me)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
            r"(?:mera naam|mujhe)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)",
            r"(?:me llamo|mi nombre es)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        ]:
            m = re.search(pattern, text)
            if m:
                updated["user_name"] = m.group(1).strip()
                break

    # ── Email ────────────────────────────────────────────────────────────────
    if not updated.get("email"):
        m = re.search(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", text.lower())
        if m:
            updated["email"] = m.group(0)

    # ── Reference / order ID (any 4-digit+ number near a keyword) ───────────
    if not updated.get("order_id"):
        m = re.search(
            r"\b(?:order|booking|reference|ref|id|number)[:\s#-]*(\d{4,})", text.lower()
        )
        if m:
            updated["order_id"] = m.group(1)
        else:
            # Fallback: lone 4–6 digit number (e.g. "order ID is 4421")
            m = re.search(r"\b(\d{4,6})\b", text)
            if m:
                updated["order_id"] = m.group(1)

    return updated


def build_tool_context(memory_entities: Dict[str, Any], scenario_name: Optional[str] = None) -> Dict[str, Any]:
    """Build tool context to inject into LLM prompt."""
    ctx: Dict[str, Any] = {}

    if memory_entities.get("order_id"):
        order_data = lookup_order(
            memory_entities["order_id"],
            memory_entities.get("email", ""),
        )
        if order_data.get("found"):
            ctx["order"] = order_data

    if memory_entities.get("hotel_city") and not memory_entities.get("hotel_options"):
        hotel_data = search_hotels(
            memory_entities["hotel_city"],
            memory_entities.get("hotel_budget"),
            memory_entities.get("hotel_people"),
        )
        if hotel_data.get("found"):
            ctx["hotels"] = hotel_data

    cities = memory_entities.get("weather_cities", [])
    if cities:
        weather_results = {}
        for city in cities:
            w = get_weather(city)
            if w.get("found"):
                weather_results[city] = w
        if weather_results:
            ctx["weather"] = weather_results

    food = memory_entities.get("food_order", {})
    if food:
        ctx["food_order"] = food

    return ctx
