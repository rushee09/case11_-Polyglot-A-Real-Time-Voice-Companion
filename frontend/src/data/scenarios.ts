// Type definitions for scenario data — content is served by the backend.
// Components should load scenarios via apiGetScenarios() from ../api/client.

export interface ScenarioTurn {
  turn_number: number;
  language: string;
  user_text: string;
  translation?: string | null;
  expected_behavior: string;
}

export interface Scenario {
  name: string;
  title: string;
  description: string;
  turns: ScenarioTurn[];
}

