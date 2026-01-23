import { useEffect, useRef } from 'react';

interface ErrorMetric {
  id: string;
  model_id: string;
  recorded_at: string;
  total_requests: number;
  error_count: number;
  error_rate: number;
  error_types: Record<string, number>;
  window_minutes: number;
}

interface ErrorRateChartProps {
  data: ErrorMetric[];
  threshold?: number; // SLA threshold for error rate %
}

export default function ErrorRateChart({ data, threshold }: ErrorRateChartProps) {
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
      ctx.fillText('No error data available', width / 2, height / 2);
      return;
    }

    // Chart area
    const padding = { top: 20, right: 20, bottom: 30, left: 60 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;

    // Calculate range (max of data or 5%, whichever is larger)
    const maxRate = Math.max(
      Math.max(...data.map(d => d.error_rate)),
      threshold || 0,
      5
    ) * 1.1;

    const xScale = (i: number) => padding.left + (i / (data.length - 1 || 1)) * chartWidth;
    const yScale = (v: number) => padding.top + chartHeight - (v / maxRate) * chartHeight;

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
      const value = ((4 - i) / 4) * maxRate;
      ctx.fillStyle = '#9ca3af';
      ctx.font = '10px system-ui';
      ctx.textAlign = 'right';
      ctx.fillText(`${value.toFixed(1)}%`, padding.left - 5, y + 3);
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
      ctx.fillText(`SLA: ${threshold}%`, width - padding.right - 55, thresholdY - 5);
    }

    // Draw area fill
    if (data.length >= 2) {
      ctx.beginPath();
      ctx.moveTo(xScale(0), yScale(0));

      data.forEach((d, i) => {
        ctx.lineTo(xScale(i), yScale(d.error_rate));
      });

      ctx.lineTo(xScale(data.length - 1), yScale(0));
      ctx.closePath();

      // Gradient fill
      const gradient = ctx.createLinearGradient(0, padding.top, 0, height - padding.bottom);
      gradient.addColorStop(0, 'rgba(239, 68, 68, 0.3)');
      gradient.addColorStop(1, 'rgba(239, 68, 68, 0.05)');
      ctx.fillStyle = gradient;
      ctx.fill();
    }

    // Draw line
    if (data.length >= 2) {
      ctx.beginPath();
      ctx.strokeStyle = '#ef4444';
      ctx.lineWidth = 2;

      data.forEach((d, i) => {
        const x = xScale(i);
        const y = yScale(d.error_rate);
        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });
      ctx.stroke();
    }

    // Draw dots for data points
    data.forEach((d, i) => {
      const x = xScale(i);
      const y = yScale(d.error_rate);

      ctx.beginPath();
      ctx.arc(x, y, 3, 0, Math.PI * 2);
      ctx.fillStyle = d.error_rate > (threshold || Infinity) ? '#ef4444' : '#f87171';
      ctx.fill();
    });

    // X-axis labels
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

  // Calculate summary stats
  const avgErrorRate = data.length > 0
    ? data.reduce((sum, d) => sum + d.error_rate, 0) / data.length
    : 0;

  const totalErrors = data.reduce((sum, d) => sum + d.error_count, 0);
  const totalRequests = data.reduce((sum, d) => sum + d.total_requests, 0);

  return (
    <div className="relative">
      <canvas ref={canvasRef} />

      {/* Summary stats */}
      <div className="flex items-center justify-center gap-6 mt-3 text-xs">
        <div className="flex items-center gap-1.5">
          <span className="text-gray-500">Avg Rate:</span>
          <span className={avgErrorRate > (threshold || Infinity) ? 'text-red-400' : 'text-gray-300'}>
            {avgErrorRate.toFixed(2)}%
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-gray-500">Total Errors:</span>
          <span className="text-gray-300">{totalErrors.toLocaleString()}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-gray-500">Total Requests:</span>
          <span className="text-gray-300">{totalRequests.toLocaleString()}</span>
        </div>
      </div>
    </div>
  );
}
