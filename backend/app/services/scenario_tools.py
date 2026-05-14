import re
from typing import Dict, Any, Optional


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


# ─── Entity extraction from text ────────────────────────────────────────────

def extract_entities_from_text(text: str, memory_entities: Dict[str, Any]) -> Dict[str, Any]:
    """Rule-based entity extraction — updates memory entities dict in place."""
    text_lower = text.lower()
    updated = dict(memory_entities)

    # Order ID extraction
    if not updated.get("order_id"):
        match = re.search(r"\border\s*(?:id|number|#)?\s*[:\-]?\s*(\d{4,})", text_lower)
        if match:
            updated["order_id"] = match.group(1)
        # Also catch plain 4-digit numbers near "order"
        if not updated.get("order_id"):
            match2 = re.search(r"\b(4421|4422|4423)\b", text)
            if match2:
                updated["order_id"] = match2.group(1)

    # Email extraction
    if not updated.get("email"):
        match = re.search(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", text_lower)
        if match:
            updated["email"] = match.group(0)

    # Hotel city
    for city in ["bangalore", "bengaluru", "mumbai", "delhi", "goa", "chennai"]:
        if city in text_lower and not updated.get("hotel_city"):
            updated["hotel_city"] = city.capitalize()

    # Hotel budget
    if not updated.get("hotel_budget"):
        match = re.search(r"(\d{3,5})\s*(?:rupias|rupees|inr|rs\.?|₹)", text_lower)
        if match:
            updated["hotel_budget"] = float(match.group(1))

    # People count
    if not updated.get("hotel_people"):
        match = re.search(r"\b(one|two|three|four|1|2|3|4)\s+(?:person|people|persons|adults)", text_lower)
        if match:
            word = match.group(1)
            num_map = {"one": 1, "two": 2, "three": 3, "four": 4}
            updated["hotel_people"] = num_map.get(word, int(word) if word.isdigit() else 2)
        # Also check "dos personas" in Spanish
        if re.search(r"dos\s+personas", text_lower):
            updated["hotel_people"] = 2

    # Weather cities
    weather_cities = list(updated.get("weather_cities") or [])
    for city in ["mumbai", "delhi", "chennai", "bangalore", "kolkata"]:
        display = city.capitalize()
        if city in text_lower and display not in weather_cities:
            weather_cities.append(display)
    updated["weather_cities"] = weather_cities

    # Food order
    food = dict(updated.get("food_order") or {})
    if "pizza" in text_lower:
        food["item"] = "pizza"
    if any(w in text_lower for w in ["veg", "vegetarian", "veg only"]):
        food["preference"] = "vegetarian"
    if "coke" in text_lower or "cola" in text_lower:
        food["add_on"] = "coke"
    if food:
        updated["food_order"] = food

    # Hotel second option recall
    if updated.get("hotel_options") and not updated.get("selected_hotel_option"):
        if re.search(r"\bsecond\s+option\b|\boption\s+2\b|\b2nd\b", text_lower):
            updated["selected_hotel_option"] = 2

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
