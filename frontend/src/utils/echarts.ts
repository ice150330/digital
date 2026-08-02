/**
 * ECharts 按需引入的单一注册点（Stage 2）。
 * 所有图表组件经 BaseChart 使用本模块导出的 echarts 核心，
 * 禁止在组件内重复 echarts.use（重复注册无害但属双写）。
 * SankeyChart 用于总览大屏渠道转化流向。
 */
import * as echarts from 'echarts/core'
import { BarChart, FunnelChart, HeatmapChart, LineChart, PieChart, SankeyChart, ScatterChart } from 'echarts/charts'
import {
  GridComponent,
  GraphicComponent,
  LegendComponent,
  MarkLineComponent,
  TitleComponent,
  TooltipComponent,
  VisualMapComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([
  BarChart,
  FunnelChart,
  HeatmapChart,
  LineChart,
  PieChart,
  SankeyChart,
  ScatterChart,
  GridComponent,
  GraphicComponent,
  LegendComponent,
  MarkLineComponent,
  TitleComponent,
  TooltipComponent,
  VisualMapComponent,
  CanvasRenderer,
])

export default echarts
