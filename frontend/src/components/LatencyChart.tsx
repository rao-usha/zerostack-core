import { useEffect, useRef } from 'react';

interface LatencyMetric {
  id: string;
  model_id: string;
  recorded_at: string;
  p50_ms: number;
  p95_ms: number;
  p99_ms: number;
  request_count: number;
  window_minutes: number;
}

interface LatencyChartProps {
  data: LatencyMetric[];
  threshold?: number; // SLA threshold for P95
}

export default function LatencyChart({ data, threshold }: LatencyChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const width = canvas.parentElement?.clientWidth || 500;
    const height = 200;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    ctx.scale(dpr, dpr);

    // Clear
    ctx.clearRect(0, 0, width, height);

    if (data.length === 0) {
      ctx.fillStyle = '#6b7280';
      ctx.font = '14px system-ui';
      ctx.textAlign = 'center';
      ctx.fillText('No latency data available', width / 2, height / 2);
      return;
    }

    // Chart area
    const padding = { top: 20, right: 20, bottom: 30, left: 60 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;

    // Calculate ranges
    const maxLatency = Math.max(
      ...data.flatMap(d => [d.p50_ms, d.p95_ms, d.p99_ms]),
      threshold || 0
    ) * 1.1;

    const xScale = (i: number) => padding.left + (i / (data.length - 1 || 1)) * chartWidth;
    const yScale = (v: number) => padding.top + chartHeight - (v / maxLatency) * chartHeight;

    // Draw grid lines
    ctx.strokeStyle = '#374151';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = padding.top + (i / 4) * chartHeight;
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(width - padding.right, y);
      ctx.stroke();

      // Y-axis labels
      const value = ((4 - i) / 4) * maxLatency;
      ctx.fillStyle = '#9ca3af';
      ctx.font = '10px system-ui';
      ctx.textAlign = 'right';
      ctx.fillText(`${value.toFixed(0)}ms`, padding.left - 5, y + 3);
    }

    // Draw threshold line
    if (threshold) {
      const thresholdY = yScale(threshold);
      ctx.beginPath();
      ctx.moveTo(padding.left, thresholdY);
      ctx.lineTo(width - padding.right, thresholdY);
      ctx.strokeStyle = '#ef4444';
      ctx.lineWidth = 2;
      ctx.setLineDash([5, 5]);
      ctx.stroke();
      ctx.setLineDash([]);

      // Threshold label
      ctx.fillStyle = '#ef4444';
      ctx.font = '10px system-ui';
      ctx.textAlign = 'left';
      ctx.fillText(`SLA: ${threshold}ms`, width - padding.right - 60, thresholdY - 5);
    }

    // Draw lines for each percentile
    const drawLine = (values: number[], color: string, _label: string) => {
      if (values.length < 2) return;

      ctx.beginPath();
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;

      values.forEach((v, i) => {
        const x = xScale(i);
        const y = yScale(v);
        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });
      ctx.stroke();
    };

    // P50 - lighter green
    drawLine(data.map(d => d.p50_ms), '#86efac', 'P50');

    // P95 - blue (main metric)
    drawLine(data.map(d => d.p95_ms), '#60a5fa', 'P95');

    // P99 - purple
    drawLine(data.map(d => d.p99_ms), '#c4b5fd', 'P99');

    // X-axis labels (show a few time points)
    if (data.length > 0) {
      ctx.fillStyle = '#9ca3af';
      ctx.font = '10px system-ui';
      ctx.textAlign = 'center';

      const labelIndices = data.length <= 6
        ? data.map((_, i) => i)
        : [0, Math.floor(data.length / 2), data.length - 1];

      labelIndices.forEach(i => {
        const d = new Date(data[i].recorded_at);
        const label = `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
        ctx.fillText(label, xScale(i), height - 10);
      });
    }

  }, [data, threshold]);

  return (
    <div className="relative">
      <canvas ref={canvasRef} />

      {/* Legend */}
      <div className="flex items-center justify-center gap-4 mt-3 text-xs">
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-0.5 bg-green-300"></div>
          <span className="text-gray-400">P50</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-0.5 bg-blue-400"></div>
          <span className="text-gray-400">P95</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-0.5 bg-purple-300"></div>
          <span className="text-gray-400">P99</span>
        </div>
        {threshold && (
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-0.5 bg-red-400" style={{ backgroundImage: 'repeating-linear-gradient(90deg, #ef4444 0, #ef4444 3px, transparent 3px, transparent 6px)' }}></div>
            <span className="text-gray-400">SLA</span>
          </div>
        )}
      </div>
    </div>
  );
}
