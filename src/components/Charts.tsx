import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { chartTheme } from '@/lib/chartTheme'
import { ESTADO_LABEL, type Metricas } from '@/lib/types'

interface ChartProps {
  oscuro: boolean
}

const tooltipStyle = (oscuro: boolean) => {
  const t = chartTheme(oscuro)
  return {
    contentStyle: {
      background: t.surface,
      border: `1px solid ${t.border}`,
      borderRadius: 10,
      fontSize: 12,
      color: t.text,
      boxShadow: '0 6px 24px rgb(15 23 42 / 0.12)',
    },
    labelStyle: { color: t.text, fontWeight: 600 },
    itemStyle: { color: t.text },
    cursor: { fill: oscuro ? 'rgb(148 163 184 / 0.08)' : 'rgb(100 116 139 / 0.08)' },
  }
}

export function TendenciaChart({ datos, oscuro }: ChartProps & { datos: Metricas['porMes'] }) {
  const t = chartTheme(oscuro)
  const tip = tooltipStyle(oscuro)
  return (
    <ResponsiveContainer width="100%" height={260}>
      <AreaChart data={datos} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
        <defs>
          <linearGradient id="gNuevos" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={t.duo[0]} stopOpacity={0.28} />
            <stop offset="100%" stopColor={t.duo[0]} stopOpacity={0} />
          </linearGradient>
          <linearGradient id="gFin" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={t.duo[1]} stopOpacity={0.28} />
            <stop offset="100%" stopColor={t.duo[1]} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke={t.grid} strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="mes" tick={{ fontSize: 12, fill: t.axis }} tickLine={false} axisLine={false} />
        <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: t.axis }} tickLine={false} axisLine={false} width={36} />
        <Tooltip {...tip} />
        <Legend iconType="circle" wrapperStyle={{ fontSize: 12, color: t.axis }} />
        <Area
          type="monotone"
          dataKey="nuevos"
          name="Nuevos"
          stroke={t.duo[0]}
          strokeWidth={2}
          fill="url(#gNuevos)"
          dot={{ r: 3, strokeWidth: 2, fill: t.surface }}
        />
        <Area
          type="monotone"
          dataKey="finalizados"
          name="Finalizados"
          stroke={t.duo[1]}
          strokeWidth={2}
          fill="url(#gFin)"
          dot={{ r: 3, strokeWidth: 2, fill: t.surface }}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}

export function AreasChart({ datos, oscuro }: ChartProps & { datos: Metricas['porArea'] }) {
  const t = chartTheme(oscuro)
  const tip = tooltipStyle(oscuro)
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={datos} layout="vertical" margin={{ top: 4, right: 16, left: 8, bottom: 0 }}>
        <CartesianGrid stroke={t.grid} strokeDasharray="3 3" horizontal={false} />
        <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12, fill: t.axis }} tickLine={false} axisLine={false} />
        <YAxis
          type="category"
          dataKey="area"
          width={104}
          tick={{ fontSize: 12, fill: t.axis }}
          tickLine={false}
          axisLine={false}
        />
        <Tooltip {...tip} />
        <Bar dataKey="total" name="Proyectos" fill={t.duo[0]} radius={[0, 4, 4, 0]} barSize={14} />
      </BarChart>
    </ResponsiveContainer>
  )
}

export function EstadosChart({ datos, oscuro }: ChartProps & { datos: Metricas['porEstado'] }) {
  const t = chartTheme(oscuro)
  const tip = tooltipStyle(oscuro)
  const data = datos
    .filter((d) => d.total > 0)
    .map((d) => ({ nombre: ESTADO_LABEL[d.estado], total: d.total }))

  return (
    <ResponsiveContainer width="100%" height={260}>
      <PieChart>
        <Pie
          data={data}
          dataKey="total"
          nameKey="nombre"
          innerRadius={58}
          outerRadius={88}
          paddingAngle={2}
          stroke={t.surface}
          strokeWidth={2}
        >
          {data.map((_, i) => (
            <Cell key={i} fill={t.series[i % t.series.length]} />
          ))}
        </Pie>
        <Tooltip {...tip} cursor={false} />
        <Legend iconType="circle" wrapperStyle={{ fontSize: 12, color: t.axis }} />
      </PieChart>
    </ResponsiveContainer>
  )
}
