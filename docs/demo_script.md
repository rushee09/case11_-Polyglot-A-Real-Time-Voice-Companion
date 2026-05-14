# Demo Script — Polyglot Voice Companion

**Duration**: ~6 minutes | **Format**: Live demo with narration

---

## 0:00 — 0:45 | Setup & Hook

> "Most AI voice assistants break the moment you switch languages mid-sentence. Polyglot doesn't."

- Show the landing page — highlight 4 language badges
- Note: fully local, no API keys, no cloud

---

## 0:45 — 2:00 | Scenario 1: English → Hindi (Customer Support)

1. Select **Scenario 1 — Customer Support**
2. Type: *"Hi, I need help. My order number is 4421."*
3. Agent responds in English, memory panel shows `order_id: 4421`
4. Type: *"Theek hai, kya aap mujhe refund dila sakte hain?"* (Hindi)
5. Agent responds in Hindi — point out language badge switches, memory retained
6. Point to the pipeline status timeline — language detected → memory → LLM → TTS

---

## 2:00 — 3:00 | Scenario 2: Hinglish (Food Ordering)

1. Select **Scenario 2 — Food Ordering**
2. Type: *"Ek large pizza aur coke chahiye."* (Hindi)
3. Agent responds in Hindi with order details
4. Type: *"Can I pay online?"* (English)
5. Agent switches to English — show `language_switch` event in memory panel

---

## 3:00 — 3:45 | Scenario 3: Spanish (Hotel Booking)

1. Select **Scenario 3 — Hotel Booking**
2. Type: *"¿Tienen habitaciones disponibles en Bangalore?"*
3. Agent responds in Spanish with hotel options — memory shows `hotel_options`

---

## 3:45 — 4:30 | Voice Mode (if faster-whisper installed)

1. Switch to **Voice Mode** (mic button)
2. Say: *"I want to check the weather in Mumbai."*
3. Show: waveform animation → transcript appears → language detected → spoken response

---

## 4:30 — 5:15 | Scenario Test Page

1. Go to **Scenarios** page
2. Click **Run All Turns** on Scenario 4 (Multilingual Weather)
3. All 5 turns execute, responses shown inline — note language codes match each turn

---

## 5:15 — 5:45 | Logs Page

1. Copy session ID from agent page, paste in **Logs**
2. Show messages tab — turn-by-turn transcript with detected languages
3. Show switches tab — en→hi and hi→en events with confidence
4. Show latency tab — stage breakdown per turn, color coding

---

## 5:45 — 6:00 | Close

> "Polyglot runs entirely on your hardware. It remembers context, follows language switches, and responds in under one second on CPU."

Point to GitHub repo. Done.
