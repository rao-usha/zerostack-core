import { useEffect, useRef, useState } from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface DataPoint {
  timestamp: string;
  value: number;
  isBreached?: boolean;
}

interface DriftTimeSeriesProps {
  data: DataPoint[];
  threshold?: number;
  baseline?: number;
  title?: string;
  metricName?: string;
  height?: number;
}

export default function DriftTimeSeries({
  data,
  threshold,
  baseline,
  title = 'Metric Over Time',
  metricName = 'Value',
  height = 200
}: DriftTimeSeriesProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 400, height });
  const [hoveredPoint, setHoveredPoint] = useState<DataPoint | null>(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

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
    if (!canvas || data.length === 0) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = dimensions.width * dpr;
    canvas.height = dimensions.height * dpr;
    ctx.scale(dpr, dpr);

    // Clear canvas
    ctx.clearRect(0, 0, dimensions.width, dimensions.height);

    // Calculate bounds
    const padding = { top: 20, right: 20, bottom: 40, left: 60 };
    const chartWidth = dimensions.width - padding.left - padding.right;
    const chartHeight = dimensions.height - padding.top - padding.bottom;

    const values = data.map(d => d.value);
    let minValue = Math.min(...values);
    let maxValue = Math.max(...values);

    // Include baseline and threshold in range if provided
    if (baseline !== undefined) {
      minValue = Math.min(minValue, baseline);
      maxValue = Math.max(maxValue, baseline);
    }
    if (threshold !== undefined && baseline !== undefined) {
      const upperThreshold = baseline * (1 + threshold);
      const lowerThreshold = baseline * (1 - threshold);
      minValue = Math.min(minValue, lowerThreshold);
      maxValue = Math.max(maxValue, upperThreshold);
    }

    // Add some padding to the range
    const range = maxValue - minValue || 1;
    minValue -= range * 0.1;
    maxValue += range * 0.1;

    // Helper functions
    const xScale = (i: number) => padding.left + (i / (data.length - 1 || 1)) * chartWidth;
    const yScale = (v: number) => padding.top + chartHeight - ((v - minValue) / (maxValue - minValue)) * chartHeight;

    // Draw threshold bands if baseline and threshold provided
    if (baseline !== undefined && threshold !== undefined) {
      const upperThreshold = baseline * (1 + threshold);
      const lowerThreshold = baseline * (1 - threshold);

      // Threshold zones (red/warning zones)
      ctx.fillStyle = 'rgba(239, 68, 68, 0.1)';
      ctx.fillRect(padding.left, padding.top, chartWidth, yScale(upperThreshold) - padding.top);
      ctx.fillRect(padding.left, yScale(lowerThreshold), chartWidth, padding.top + chartHeight - yScale(lowerThreshold));

      // Safe zone
      ctx.fillStyle = 'rgba(34, 197, 94, 0.05)';
      ctx.fillRect(padding.left, yScale(upperThreshold), chartWidth, yScale(lowerThreshold) - yScale(upperThreshold));

      // Threshold lines
      ctx.strokeStyle = 'rgba(239, 68, 68, 0.5)';
      ctx.lineWidth = 1;
      ctx.setLineDash([5, 5]);

      ctx.beginPath();
      ctx.moveTo(padding.left, yScale(upperThreshold));
      ctx.lineTo(padding.left + chartWidth, yScale(upperThreshold));
      ctx.stroke();

      ctx.beginPath();
      ctx.moveTo(padding.left, yScale(lowerThreshold));
      ctx.lineTo(padding.left + chartWidth, yScale(lowerThreshold));
      ctx.stroke();

      ctx.setLineDash([]);
    }

    // Draw baseline if provided
    if (baseline !== undefined) {
      ctx.strokeStyle = 'rgba(99, 102, 241, 0.7)';
      ctx.lineWidth = 2;
      ctx.setLineDash([10, 5]);
      ctx.beginPath();
      ctx.moveTo(padding.left, yScale(baseline));
      ctx.lineTo(padding.left + chartWidth, yScale(baseline));
      ctx.stroke();
      ctx.setLineDash([]);

      // Label
      ctx.fillStyle = 'rgba(99, 102, 241, 0.9)';
      ctx.font = '10px sans-serif';
      ctx.textAlign = 'left';
      ctx.fillText('Baseline', padding.left + 5, yScale(baseline) - 5);
    }

    // Draw the data line
    ctx.strokeStyle = '#a8d8ff';
    ctx.lineWidth = 2;
    ctx.beginPath();
    data.forEach((point, i) => {
      const x = xScale(i);
      const y = yScale(point.value);
      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });
    ctx.stroke();

    // Draw data points
    data.forEach((point, i) => {
      const x = xScale(i);
      const y = yScale(point.value);

      ctx.beginPath();
      ctx.arc(x, y, 4, 0, Math.PI * 2);
      ctx.fillStyle = point.isBreached ? '#ef4444' : '#a8d8ff';
      ctx.fill();
      ctx.strokeStyle = '#1f2937';
      ctx.lineWidth = 1;
      ctx.stroke();
    });

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

    const yTicks = 5;
    for (let i = 0; i <= yTicks; i++) {
      const value = minValue + (maxValue - minValue) * (i / yTicks);
      const y = yScale(value);
      ctx.fillText(value.toFixed(2), padding.left - 5, y + 3);

      // Grid line
      ctx.strokeStyle = '#1f2937';
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(padding.left + chartWidth, y);
      ctx.stroke();
    }

    // X-axis labels (show first, middle, last)
    ctx.fillStyle = '#9ca3af';
    ctx.textAlign = 'center';
    if (data.length > 0) {
      const formatDate = (dateStr: string) => {
        const d = new Date(dateStr);
        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      };

      ctx.fillText(formatDate(data[0].timestamp), xScale(0), padding.top + chartHeight + 20);
      if (data.length > 2) {
        const midIdx = Math.floor(data.length / 2);
        ctx.fillText(formatDate(data[midIdx].timestamp), xScale(midIdx), padding.top + chartHeight + 20);
      }
      if (data.length > 1) {
        ctx.fillText(formatDate(data[data.length - 1].timestamp), xScale(data.length - 1), padding.top + chartHeight + 20);
      }
    }
  }, [data, threshold, baseline, dimensions]);

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas || data.length === 0) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const padding = { left: 60, right: 20 };
    const chartWidth = dimensions.width - padding.left - padding.right;

    // Find nearest point
    const pointWidth = chartWidth / (data.length - 1 || 1);
    const pointIndex = Math.round((x - padding.left) / pointWidth);

    if (pointIndex >= 0 && pointIndex < data.length) {
      setHoveredPoint(data[pointIndex]);
      setMousePos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
    } else {
      setHoveredPoint(null);
    }
  };

  // Calculate trend
  const getTrend = () => {
    if (data.length < 2) return 'neutral';
    const recent = data.slice(-5);
    const first = recent[0]?.value || 0;
    const last = recent[recent.length - 1]?.value || 0;
    const change = ((last - first) / (first || 1)) * 100;
    if (change > 5) return 'up';
    if (change < -5) return 'down';
    return 'neutral';
  };

  const trend = getTrend();

  if (data.length === 0) {
    return (
      <div
        ref={containerRef}
        className="bg-dark-surface rounded-lg border border-dark-border p-4"
        style={{ height }}
      >
        <p className="text-gray-500 text-center">No data available</p>
      </div>
    );
  }

  return (
    <div ref={containerRef} className="bg-dark-surface rounded-lg border border-dark-border p-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-300">{title}</h3>
        <div className="flex items-center gap-1 text-sm">
          {trend === 'up' && <TrendingUp size={14} className="text-red-400" />}
          {trend === 'down' && <TrendingDown size={14} className="text-green-400" />}
          {trend === 'neutral' && <Minus size={14} className="text-gray-400" />}
          <span className="text-gray-400">
            {data[data.length - 1]?.value.toFixed(4)}
          </span>
        </div>
      </div>

      <div className="relative">
        <canvas
          ref={canvasRef}
          style={{ width: '100%', height }}
          onMouseMove={handleMouseMove}
          onMouseLeave={() => setHoveredPoint(null)}
        />

        {hoveredPoint && (
          <div
            className="absolute bg-dark-bg border border-dark-border rounded px-2 py-1 text-xs pointer-events-none z-10"
            style={{
              left: mousePos.x + 10,
              top: mousePos.y - 30,
              transform: 'translateX(-50%)'
            }}
          >
            <div className="text-gray-300">{metricName}: {hoveredPoint.value.toFixed(4)}</div>
            <div className="text-gray-500">{new Date(hoveredPoint.timestamp).toLocaleString()}</div>
            {hoveredPoint.isBreached && (
              <div className="text-red-400 font-medium">Breached</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
