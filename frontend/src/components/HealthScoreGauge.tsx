import { useEffect, useRef } from 'react';

interface HealthScoreGaugeProps {
  overall: number;
  latencyScore: number;
  errorScore: number;
  latencyDetails: string;
  errorDetails: string;
}

export default function HealthScoreGauge({
  overall,
  latencyScore,
  errorScore,
  latencyDetails,
  errorDetails
}: HealthScoreGaugeProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const size = 200;
    canvas.width = size * dpr;
    canvas.height = size * dpr;
    canvas.style.width = `${size}px`;
    canvas.style.height = `${size}px`;
    ctx.scale(dpr, dpr);

    const centerX = size / 2;
    const centerY = size / 2;
    const radius = 80;
    const lineWidth = 12;

    // Clear canvas
    ctx.clearRect(0, 0, size, size);

    // Background arc (gray)
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, 0.75 * Math.PI, 2.25 * Math.PI);
    ctx.strokeStyle = '#374151';
    ctx.lineWidth = lineWidth;
    ctx.lineCap = 'round';
    ctx.stroke();

    // Score arc (colored based on health)
    const scoreAngle = (overall / 100) * 1.5 * Math.PI;
    let color: string;
    if (overall >= 80) {
      color = '#10b981'; // green
    } else if (overall >= 50) {
      color = '#f59e0b'; // yellow
    } else {
      color = '#ef4444'; // red
    }

    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, 0.75 * Math.PI, 0.75 * Math.PI + scoreAngle);
    ctx.strokeStyle = color;
    ctx.lineWidth = lineWidth;
    ctx.lineCap = 'round';
    ctx.stroke();

    // Score text
    ctx.fillStyle = '#f3f4f6';
    ctx.font = 'bold 42px system-ui';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(overall.toString(), centerX, centerY - 10);

    // Label
    ctx.fillStyle = '#9ca3af';
    ctx.font = '14px system-ui';
    ctx.fillText('Health Score', centerX, centerY + 25);
  }, [overall]);

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-400';
    if (score >= 50) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getScoreBg = (score: number) => {
    if (score >= 80) return 'bg-green-900/30';
    if (score >= 50) return 'bg-yellow-900/30';
    return 'bg-red-900/30';
  };

  return (
    <div className="flex flex-col items-center">
      <canvas ref={canvasRef} />

      <div className="w-full mt-4 space-y-2">
        {/* Latency score */}
        <div className={`p-3 rounded-lg ${getScoreBg(latencyScore)}`}>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-300">Latency Score</span>
            <span className={`text-sm font-bold ${getScoreColor(latencyScore)}`}>
              {latencyScore}/100
            </span>
          </div>
          <p className="text-xs text-gray-500 mt-1">{latencyDetails}</p>
        </div>

        {/* Error score */}
        <div className={`p-3 rounded-lg ${getScoreBg(errorScore)}`}>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-300">Error Score</span>
            <span className={`text-sm font-bold ${getScoreColor(errorScore)}`}>
              {errorScore}/100
            </span>
          </div>
          <p className="text-xs text-gray-500 mt-1">{errorDetails}</p>
        </div>
      </div>
    </div>
  );
}
