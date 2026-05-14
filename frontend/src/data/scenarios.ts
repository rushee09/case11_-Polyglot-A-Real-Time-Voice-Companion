export interface ScenarioTurn {
  turn_number: number;
  language: string;
  user_text: string;
  translation?: string;
  expected_behavior: string;
}

export interface Scenario {
  name: string;
  title: string;
  description: string;
  turns: ScenarioTurn[];
}

export const SCENARIOS: Scenario[] = [
  {
    name: "customer_support",
    title: "Scenario 1 — Customer Support: Order Status",
    description: "English → Hindi → English with order context preserved across language switches.",
    turns: [
      {
        turn_number: 1,
        language: "en",
        user_text: "Hi, I need to check the status of my order. The order ID is 4421.",
        expected_behavior: "Agent acknowledges in English and asks for verification.",
      },
      {
        turn_number: 2,
        language: "en",
        user_text: "Yes, the email on the account is rahul@example.com.",
        expected_behavior: "Agent confirms order is out for delivery in English.",
      },
      {
        turn_number: 3,
        language: "hi",
        user_text: "Theek hai, lekin delivery kal tak ho jaayegi kya?",
        translation: "OK, but will the delivery happen by tomorrow?",
        expected_behavior: "Agent switches to Hindi, retains order context, answers in Hindi.",
      },
      {
        turn_number: 4,
        language: "hi",
        user_text: "Aur agar nahi hua toh refund mil sakta hai?",
        translation: "And if not, can I get a refund?",
        expected_behavior: "Agent continues in Hindi and answers refund question using order context.",
      },
      {
        turn_number: 5,
        language: "en",
        user_text: "Actually let's switch back — can you email me the tracking link?",
        expected_behavior: "Agent switches back to English and remembers order/email context.",
      },
    ],
  },
  {
    name: "travel_planning",
    title: "Scenario 2 — Travel Planning: Hotel Booking",
    description: "Spanish → English with hotel options recalled across language switch.",
    turns: [
      {
        turn_number: 1,
        language: "es",
        user_text: "Hola, quiero reservar un hotel en Bangalore para el próximo fin de semana.",
        translation: "Hello, I want to book a hotel in Bangalore for next weekend.",
        expected_behavior: "Agent responds in Spanish.",
      },
      {
        turn_number: 2,
        language: "es",
        user_text: "Para dos personas, presupuesto de 5000 rupias por noche.",
        translation: "For two people, budget of 5000 rupees per night.",
        expected_behavior: "Agent suggests options in Spanish.",
      },
      {
        turn_number: 3,
        language: "en",
        user_text: "Sorry, my Spanish is rusty. Can we continue in English? Tell me again about the second option.",
        expected_behavior: "Agent switches to English and recalls the second hotel option.",
      },
      {
        turn_number: 4,
        language: "en",
        user_text: "Book it. Confirm the dates please.",
        expected_behavior: "Agent confirms booking details in English.",
      },
    ],
  },
  {
    name: "code_switching",
    title: "Scenario 3 — Code-Switching Within an Utterance",
    description: "Mixed Hindi-English handled gracefully with context maintained.",
    turns: [
      {
        turn_number: 1,
        language: "mixed",
        user_text: "Mujhe ek pizza order karna hai, but make it veg only please.",
        translation: "I want to order a pizza, but make it veg only please.",
        expected_behavior: "Agent handles mixed language gracefully and documents choice. May respond in Hinglish or English.",
      },
      {
        turn_number: 2,
        language: "en",
        user_text: "And add a coke too.",
        expected_behavior: "Agent remembers the veg pizza order and adds coke to the same order.",
      },
    ],
  },
  {
    name: "rapid_switching",
    title: "Scenario 4 — Rapid Language Switching",
    description: "English → Hindi → Spanish → English with city comparison using memory.",
    turns: [
      {
        turn_number: 1,
        language: "en",
        user_text: "What's the weather in Mumbai today?",
        expected_behavior: "Agent answers about Mumbai in English.",
      },
      {
        turn_number: 2,
        language: "hi",
        user_text: "Aur Delhi mein?",
        translation: "And in Delhi?",
        expected_behavior: "Agent understands this refers to weather and answers in Hindi.",
      },
      {
        turn_number: 3,
        language: "es",
        user_text: "¿Y en Chennai?",
        translation: "And in Chennai?",
        expected_behavior: "Agent understands this refers to weather and answers in Spanish.",
      },
      {
        turn_number: 4,
        language: "en",
        user_text: "Compare all three for me.",
        expected_behavior: "Agent compares Mumbai, Delhi, and Chennai in English using memory.",
      },
    ],
  },
];
