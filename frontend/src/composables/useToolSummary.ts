import type { ToolTraceItem } from '../api/agent'

const names: Record<string, string> = {
  get_dataset_profile: '读取数据概况',
  get_data_quality_issues: '检查数据质量',
  conversion_by_dimension: '按维度统计转化',
  get_model_metrics: '读取模型指标',
  get_feature_schema: '读取特征结构',
  predict_proba: '计算转化概率',
  explain_global: '生成全局解释',
  explain_customer: '解释单个客户',
  segment_summary: '读取分群画像',
  assign_cluster: '分配客户分群',
  top_association_rules: '读取高价值规则',
  strategy_brief: '整理策略摘要',
  compare_experiments: '对比实验结果',
  get_calibration_summary: '检查概率校准',
  get_lift_table: '读取 Lift 表',
  simulate_budget: '模拟预算分配',
  counterfactual_explain: '分析模型敏感性',
  generate_analysis_report: '生成分析报告',
  render_chart: '生成图表数据',
}

const icons: Record<string, string> = {
  render_chart: 'uil:chart',
  predict_proba: 'uil:percentage',
  explain_customer: 'uil:search-alt',
  explain_global: 'uil:analysis',
  simulate_budget: 'uil:wallet',
  generate_analysis_report: 'uil:file-alt',
  top_association_rules: 'uil:code-branch',
  segment_summary: 'uil:users-alt',
}

export function toolLabel(tool: string) {
  return names[tool] || tool
}

export function toolIcon(tool: string) {
  return icons[tool] || 'uil:processor'
}

export function toolSummary(item: ToolTraceItem) {
  if (item.error) return item.error
  const keys = Object.keys(item.args || {})
  if (!keys.length) return '已按当前分析上下文执行'
  return `参数：${keys.slice(0, 3).join('、')}${keys.length > 3 ? ' 等' : ''}`
}
