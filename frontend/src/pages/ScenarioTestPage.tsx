import { useState, useEffect } from "react";
import { v4 as uuidv4 } from "uuid";
import type { Scenario, ScenarioTurn } from "../data/scenarios";
import ScenarioCard from "../components/ScenarioCard";
import { apiChat, apiGetScenarios } from "../api/client";

type Results = Record<number, { response?: string; loading?: boolean; error?: string }>;

export default function ScenarioTestPage() {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  // One stable session per scenario name — keyed after load
  const [sessionIds, setSessionIds] = useState<Record<string, string>>({});
  const [allResults, setAllResults] = useState<Record<string, Results>>({});

  useEffect(() => {
    apiGetScenarios()
      .then((data) => {
        const loaded = data as Scenario[];
        setScenarios(loaded);
        // Initialise one session per scenario when the list arrives
        setSessionIds((prev) => {
          const next = { ...prev };
          for (const s of loaded) {
            if (!next[s.name]) next[s.name] = uuidv4();
          }
          return next;
        });
      })
      .catch(() => null);
  }, []);

  function setResult(
    scenarioName: string,
    turnNum: number,
    update: Partial<Results[number]>
  ) {
    setAllResults((prev) => ({
      ...prev,
      [scenarioName]: {
        ...(prev[scenarioName] ?? {}),
        [turnNum]: {
          ...(prev[scenarioName]?.[turnNum] ?? {}),
          ...update,
        },
      },
    }));
  }

  async function handleSendTurn(scenarioName: string, turn: ScenarioTurn) {
    const sessionId = sessionIds[scenarioName];
    setResult(scenarioName, turn.turn_number, { loading: true, error: undefined });
    try {
      const resp = await apiChat(turn.user_text, sessionId, scenarioName);
      setResult(scenarioName, turn.turn_number, {
        response: resp.assistant_response,
        loading: false,
      });
    } catch (e) {
      setResult(scenarioName, turn.turn_number, {
        error: (e as Error).message,
        loading: false,
      });
    }
  }

  async function runAllTurns(scenarioName: string) {
    const scenario = scenarios.find((s) => s.name === scenarioName);
    if (!scenario) return;
    for (const turn of scenario.turns) {
      await handleSendTurn(scenarioName, turn);
      await new Promise((r) => setTimeout(r, 300));
    }
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-6 space-y-6">
      <div>
        <h1 className="text-xl font-bold mb-1">Scenario Tests</h1>
        <p className="text-sm text-white/40">
          Run evaluation scenarios against the agent. Each scenario has its own isolated session.
          Send turns individually or run all at once.
        </p>
      </div>

      <div className="grid gap-6">
        {scenarios.map((scenario) => (
          <div key={scenario.name} className="space-y-2">
            <div className="flex items-center justify-between">
              <div />
              <button
                onClick={() => runAllTurns(scenario.name)}
                className="btn-secondary text-xs py-1"
              >
                ▶▶ Run All Turns
              </button>
            </div>
            <ScenarioCard
              scenario={scenario}
              onSendTurn={(turn) => handleSendTurn(scenario.name, turn)}
              results={allResults[scenario.name] ?? {}}
              sessionId={sessionIds[scenario.name]}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
