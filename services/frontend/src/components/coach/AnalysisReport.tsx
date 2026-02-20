import { useState } from 'react';
import { GlowButton } from '../ui/GlowButton';
import { ProgressRing } from '../ui/ProgressRing';
import { getProgressAnalysis } from '../../api/client';
import { useSessionStorage } from '../../hooks/useSessionStorage';
import type { ProgressAnalysis } from '../../types/aiCoach';

export function AnalysisReport() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useSessionStorage<ProgressAnalysis | null>('coach_analysis', null);

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    setAnalysis(null);
    try {
      const result = await getProgressAnalysis();
      setAnalysis(result);
    } catch (err: any) {
      if (err?.response?.status === 403) {
        setError('Anthropic API key required. Please set your key in Settings.');
      } else {
        setError(err instanceof Error ? err.message : 'Failed to get analysis');
      }
    } finally {
      setLoading(false);
    }
  };

  if (error) {
    return (
      <div className="card">
        <div className="bg-danger/10 border border-danger/20 text-danger text-sm rounded-xl px-4 py-3 mb-4">
          {error}
        </div>
        <GlowButton variant="secondary" onClick={() => setError(null)}>Try Again</GlowButton>
      </div>
    );
  }

  if (analysis) {
    return (
      <div className="card space-y-5">
        {analysis.muscle_balance_score != null && (
          <div className="flex items-center gap-4">
            <ProgressRing value={analysis.muscle_balance_score} />
            <div>
              <h4 className="text-sm font-semibold text-chalk">Muscle Balance</h4>
              <p className="text-xs text-steel">Score out of 100</p>
            </div>
          </div>
        )}

        <div>
          <h3 className="text-sm font-semibold text-chalk mb-1">Summary</h3>
          <p className="text-sm text-steel">{analysis.summary}</p>
        </div>

        {analysis.strengths.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-chalk mb-1">Strengths</h4>
            <ul className="space-y-1">
              {analysis.strengths.map((s, idx) => (
                <li key={idx} className="text-xs text-steel flex gap-2">
                  <span className="text-success shrink-0">+</span>{s}
                </li>
              ))}
            </ul>
          </div>
        )}

        {analysis.areas_to_improve.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-chalk mb-1">Areas to Improve</h4>
            <ul className="space-y-1">
              {analysis.areas_to_improve.map((a, idx) => (
                <li key={idx} className="text-xs text-steel flex gap-2">
                  <span className="text-danger shrink-0">-</span>{a}
                </li>
              ))}
            </ul>
          </div>
        )}

        {analysis.recommendations.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-chalk mb-1">Recommendations</h4>
            <ul className="space-y-1">
              {analysis.recommendations.map((r, idx) => (
                <li key={idx} className="text-xs text-steel flex gap-2">
                  <span className="text-ember shrink-0">*</span>{r}
                </li>
              ))}
            </ul>
          </div>
        )}

        <GlowButton variant="secondary" onClick={() => setAnalysis(null)} className="w-full">
          Analyze Again
        </GlowButton>
      </div>
    );
  }

  return (
    <div className="card space-y-5">
      <p className="text-sm text-steel">
        Get an AI-powered analysis of your current workout routine, including strengths, areas to improve, and muscle balance assessment.
      </p>
      <ul className="space-y-1.5 text-sm text-steel">
        <li className="flex gap-2"><span className="text-success">+</span> Training strengths</li>
        <li className="flex gap-2"><span className="text-ember">*</span> Areas to improve</li>
        <li className="flex gap-2"><span className="text-ember">*</span> Muscle balance score</li>
        <li className="flex gap-2"><span className="text-ember">*</span> Actionable recommendations</li>
      </ul>
      <GlowButton onClick={handleAnalyze} disabled={loading} className="w-full">
        {loading ? 'Analyzing...' : 'Analyze My Routine'}
      </GlowButton>
    </div>
  );
}
