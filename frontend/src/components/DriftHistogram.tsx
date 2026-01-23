import { useEffect, useRef, useState } from 'react';

interface HistogramData {
  baseline: number[];
  current: number[];
}

interface DriftHistogramProps {
  data: HistogramData;
  title?: string;
  buckets?: number;
  height?: number;
  showLegend?: boolean;
}

export default function DriftHistogram({
  data,
  title = 'Distribution Comparison',
  buckets = 20,
  height = 200,
  showLegend = true
}: DriftHistogramProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 400, height });

  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.offsetWidth,
          height
        });
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, [height]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = dimensions.width * dpr;
    canvas.height = dimensions.height * dpr;
    ctx.scale(dpr, dpr);

    // Clear canvas
    ctx.clearRect(0, 0, dimensions.width, dimensions.height);

    if (data.baseline.length === 0 && data.current.length === 0) {
      ctx.fillStyle = '#9ca3af';
      ctx.font = '14px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('No data available', dimensions.width / 2, dimensions.height / 2);
      return;
    }

    // Calculate bounds
    const padding = { top: 20, right: 20, bottom: 40, left: 50 };
    const chartWidth = dimensions.width - padding.left - padding.right;
    const chartHeight = dimensions.height - padding.top - padding.bottom;

    // Find min/max across both distributions
    const allValues = [...data.baseline, ...data.current];
    const minValue = Math.min(...allValues);
    const maxValue = Math.max(...allValues);
    const valueRange = maxValue - minValue || 1;

    // Create histogram buckets
    const bucketWidth = valueRange / buckets;

    const baselineHist = new Array(buckets).fill(0);
    const currentHist = new Array(buckets).fill(0);

    data.baseline.forEach(v => {
      const idx = Math.min(Math.floor((v - minValue) / bucketWidth), buckets - 1);
      baselineHist[idx]++;
    });

    data.current.forEach(v => {
      const idx = Math.min(Math.floor((v - minValue) / bucketWidth), buckets - 1);
      currentHist[idx]++;
    });

    // Normalize to percentages
    const baselineTotal = data.baseline.length || 1;
    const currentTotal = data.current.length || 1;
    const baselineNorm = baselineHist.map(c => c / baselineTotal);
    const currentNorm = currentHist.map(c => c / currentTotal);

    const maxFreq = Math.max(...baselineNorm, ...currentNorm);

    // Helper functions
    const xScale = (i: number) => padding.left + (i / buckets) * chartWidth;
    const yScale = (f: number) => padding.top + chartHeight - (f / maxFreq) * chartHeight;
    const barWidth = (chartWidth / buckets) * 0.4;

    // Draw bars
    for (let i = 0; i < buckets; i++) {
      const x = xScale(i);

      // Baseline bar (blue)
      if (baselineNorm[i] > 0) {
        ctx.fillStyle = 'rgba(99, 102, 241, 0.6)';
        const barHeight = chartHeight * (baselineNorm[i] / maxFreq);
        ctx.fillRect(x, yScale(baselineNorm[i]), barWidth, barHeight);
      }

      // Current bar (cyan)
      if (currentNorm[i] > 0) {
        ctx.fillStyle = 'rgba(168, 216, 255, 0.6)';
        const barHeight = chartHeight * (currentNorm[i] / maxFreq);
        ctx.fillRect(x + barWidth, yScale(currentNorm[i]), barWidth, barHeight);
      }
    }

    // Draw axes
    ctx.strokeStyle = '#374151';
    ctx.lineWidth = 1;

    // Y-axis
    ctx.beginPath();
    ctx.moveTo(padding.left, padding.top);
    ctx.lineTo(padding.left, padding.top + chartHeight);
    ctx.stroke();

    // X-axis
    ctx.beginPath();
    ctx.moveTo(padding.left, padding.top + chartHeight);
    ctx.lineTo(padding.left + chartWidth, padding.top + chartHeight);
    ctx.stroke();

    // Y-axis labels
    ctx.fillStyle = '#9ca3af';
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'right';

    const yTicks = 4;
    for (let i = 0; i <= yTicks; i++) {
      const freq = maxFreq * (i / yTicks);
      const y = yScale(freq);
      ctx.fillText((freq * 100).toFixed(0) + '%', padding.left - 5, y + 3);

      // Grid line
      ctx.strokeStyle = '#1f2937';
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(padding.left + chartWidth, y);
      ctx.stroke();
    }

    // X-axis labels
    ctx.fillStyle = '#9ca3af';
    ctx.textAlign = 'center';

    const xLabels = 5;
    for (let i = 0; i <= xLabels; i++) {
      const value = minValue + (valueRange * i / xLabels);
      const x = padding.left + (chartWidth * i / xLabels);
      ctx.fillText(value.toFixed(2), x, padding.top + chartHeight + 20);
    }

    // Legend
    if (showLegend) {
      const legendY = padding.top + 10;

      // Baseline legend
      ctx.fillStyle = 'rgba(99, 102, 241, 0.6)';
      ctx.fillRect(dimensions.width - 120, legendY, 12, 12);
      ctx.fillStyle = '#9ca3af';
      ctx.textAlign = 'left';
      ctx.fillText('Baseline', dimensions.width - 105, legendY + 10);

      // Current legend
      ctx.fillStyle = 'rgba(168, 216, 255, 0.6)';
      ctx.fillRect(dimensions.width - 120, legendY + 18, 12, 12);
      ctx.fillStyle = '#9ca3af';
      ctx.fillText('Current', dimensions.width - 105, legendY + 28);
    }
  }, [data, buckets, dimensions, showLegend]);

  // Calculate statistics
  const calcStats = (values: number[]) => {
    if (values.length === 0) return { mean: 0, std: 0, min: 0, max: 0 };
    const mean = values.reduce((a, b) => a + b, 0) / values.length;
    const std = Math.sqrt(values.reduce((sum, v) => sum + (v - mean) ** 2, 0) / values.length);
    return {
      mean,
      std,
      min: Math.min(...values),
      max: Math.max(...values)
    };
  };

  const baselineStats = calcStats(data.baseline);
  const currentStats = calcStats(data.current);

  return (
    <div ref={containerRef} className="bg-dark-surface rounded-lg border border-dark-border p-4">
      <h3 className="text-sm font-medium text-gray-300 mb-2">{title}</h3>

      <canvas
        ref={canvasRef}
        style={{ width: '100%', height }}
      />

      {/* Statistics comparison */}
      <div className="mt-3 grid grid-cols-2 gap-4 text-xs">
        <div className="space-y-1">
          <div className="text-indigo-400 font-medium">Baseline</div>
          <div className="text-gray-400">
            <span className="text-gray-500">Mean:</span> {baselineStats.mean.toFixed(4)}
          </div>
          <div className="text-gray-400">
            <span className="text-gray-500">Std:</span> {baselineStats.std.toFixed(4)}
          </div>
          <div className="text-gray-400">
            <span className="text-gray-500">n:</span> {data.baseline.length}
          </div>
        </div>
        <div className="space-y-1">
          <div className="text-cyan-400 font-medium">Current</div>
          <div className="text-gray-400">
            <span className="text-gray-500">Mean:</span> {currentStats.mean.toFixed(4)}
          </div>
          <div className="text-gray-400">
            <span className="text-gray-500">Std:</span> {currentStats.std.toFixed(4)}
          </div>
          <div className="text-gray-400">
            <span className="text-gray-500">n:</span> {data.current.length}
          </div>
        </div>
      </div>

      {/* Mean shift indicator */}
      {data.baseline.length > 0 && data.current.length > 0 && (
        <div className="mt-2 pt-2 border-t border-dark-border">
          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-500">Mean Shift:</span>
            <span className={
              Math.abs(currentStats.mean - baselineStats.mean) / (baselineStats.std || 1) > 1
                ? 'text-red-400'
                : 'text-green-400'
            }>
              {((currentStats.mean - baselineStats.mean) / (baselineStats.mean || 1) * 100).toFixed(2)}%
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
