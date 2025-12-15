# 📊 龙虎榜每日分析汇总

## 📅 2025-07-02 龙虎榜分析

**📊 当日统计**: 共分析 68 只个股

### 情绪分布

<div class="emotion-stats">
  <div class="stat-card">
    <span class="emoji">🚀</span>
    <h4>亢奋</h4>
    <div class="number">40只</div>
    <div class="percent">58.8%</div>
  </div>
  <div class="stat-card">
    <span class="emoji">😰</span>
    <h4>恐慌</h4>
    <div class="number">17只</div>
    <div class="percent">25.0%</div>
  </div>
  <div class="stat-card">
    <span class="emoji">🤔</span>
    <h4>分歧</h4>
    <div class="number">11只</div>
    <div class="percent">16.2%</div>
  </div>
</div>

### 🎯 关键洞察

**主导情绪**: 亢奋 (40只, 58.8%)  
**整体特征**: 个股情绪普遍高涨，多头氛围浓厚  
**风险等级**: 中等偏高

---

### 🚀 亢奋情绪个股 (40只)

<div class="stock-card">
  <div class="stock-header">
    <span class="stock-code">300670.SZ</span>
    <span class="stock-name">大烨智能</span>
  </div>
  <div class="stock-info">
    <div class="info-row">
      <span class="label">结论：</span>
      <span class="value">多方获胜</span>
    </div>
    <div class="info-row">
      <span class="label">形态：</span>
      <span class="value">趋势加速</span>
    </div>
    <details class="participants">
      <summary>参与者</summary>
      <p>机构(卖) vs 量化打板,瑞鹤仙(博弈)</p>
    </details>
    <a href="./analysis/300670.SZ_analysis.html" class="analysis-link">
      查看详细分析 →
    </a>
  </div>
</div>

<div class="stock-card">
  <div class="stock-header">
    <span class="stock-code">300961.SZ</span>
    <span class="stock-name">深水海纳</span>
  </div>
  <div class="stock-info">
    <div class="info-row">
      <span class="label">结论：</span>
      <span class="value">多方胜出</span>
    </div>
    <div class="info-row">
      <span class="label">形态：</span>
      <span class="value">趋势加速</span>
    </div>
    <details class="participants">
      <summary>参与者</summary>
      <p>机构(卖) vs 量化打板,T王,苏南帮,消闲派(博弈)</p>
    </details>
    <a href="./analysis/300961.SZ_analysis.html" class="analysis-link">
      查看详细分析 →
    </a>
  </div>
</div>

<!-- 更多股票卡片... -->

<style>
/* 移动端优化样式 */
.emotion-stats {
  display: flex;
  gap: 10px;
  margin: 20px 0;
  overflow-x: auto;
}

.stat-card {
  flex: 1;
  min-width: 100px;
  background: #f5f5f5;
  padding: 15px;
  border-radius: 8px;
  text-align: center;
}

.stat-card .emoji {
  font-size: 2em;
}

.stat-card h4 {
  margin: 10px 0 5px 0;
  font-size: 1em;
}

.stat-card .number {
  font-size: 1.2em;
  font-weight: bold;
  color: #333;
}

.stat-card .percent {
  font-size: 0.9em;
  color: #666;
}

.stock-card {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  margin: 15px 0;
  padding: 15px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.stock-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid #f0f0f0;
}

.stock-code {
  font-weight: bold;
  color: #1a73e8;
}

.stock-name {
  color: #333;
}

.info-row {
  margin: 8px 0;
  display: flex;
  align-items: center;
}

.info-row .label {
  color: #666;
  margin-right: 8px;
  min-width: 50px;
}

.info-row .value {
  color: #333;
  font-weight: 500;
}

.participants {
  margin: 10px 0;
}

.participants summary {
  cursor: pointer;
  color: #1a73e8;
  font-weight: 500;
  padding: 5px 0;
}

.participants p {
  margin: 5px 0 0 15px;
  color: #666;
  font-size: 0.9em;
}

.analysis-link {
  display: inline-block;
  margin-top: 10px;
  padding: 8px 16px;
  background: #1a73e8;
  color: white;
  text-decoration: none;
  border-radius: 4px;
  font-size: 0.9em;
}

/* 响应式布局 */
@media (max-width: 600px) {
  .emotion-stats {
    justify-content: space-between;
  }
  
  .stock-card {
    margin: 10px 0;
  }
  
  .stock-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>