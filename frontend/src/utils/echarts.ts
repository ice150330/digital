/**
 * ECharts 按需引入的单一注册点（Stage 2）。
 * 所有图表组件经 BaseChart 使用本模块导出的 echarts 核心，
 * 禁止在组件内重复 echarts.use（重复注册无害但属双写）。
 * FunnelChart/VisualMapComponent 为 Stage 3 大屏与热力图预备。
 */
import * as echarts from 'echarts/core'
import { BarChart, FunnelChart, HeatmapChart, LineChart, ScatterChart } from 'echarts/charts'
import {
  GridComponent,
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
  ScatterChart,
  GridComponent,
  LegendComponent,
  MarkLineComponent,
  TitleComponent,
  TooltipComponent,
  VisualMapComponent,
  CanvasRenderer,
])

export default echarts
