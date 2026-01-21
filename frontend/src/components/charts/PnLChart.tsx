// src/components/charts/PnLChart.tsx
'use client'

import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts'
import { formatCurrency, formatDate } from '@/lib/utils'

interface PnLChartProps {
  data: { date: string; pnl: number }[]
}

export function PnLChart({ data }: PnLChartProps) {
  return (
    <div className="h-[300px] w-full bg-white p-6 rounded-xl border">
      <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-6">P&L Over Time (Paper Trading)</h3>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <defs>
            <linearGradient id="colorPnl" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10b981" stopOpacity={0.1}/>
              <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
          <XAxis 
            dataKey="date" 
            axisLine={false} 
            tickLine={false} 
            tick={{ fontSize: 10, fill: '#94a3b8' }}
            tickFormatter={(str: string) => formatDate(str)}
          />
          <YAxis 
            axisLine={false} 
            tickLine={false} 
            tick={{ fontSize: 10, fill: '#94a3b8' }}
            tickFormatter={(val: number) => `$${val}`}
          />
          <Tooltip 
            contentStyle={{ 
              borderRadius: '8px', 
              border: '1px solid #e2e8f0',
              boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
            }}
            labelFormatter={(label: string) => formatDate(label)}
            formatter={(value: number) => [formatCurrency(value), 'P&L']}
          />
          <Area 
            type="monotone" 
            dataKey="pnl" 
            stroke="#10b981" 
            strokeWidth={3}
            fillOpacity={1} 
            fill="url(#colorPnl)" 
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
