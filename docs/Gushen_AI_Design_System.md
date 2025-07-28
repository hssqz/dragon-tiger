# GushenAI 设计系统文档

> **版本**: v1.0  
> **更新时间**: 2025-01-27  
> **适用范围**: GushenAI 产品全线  

---

## 📋 目录

1. [设计理念](#设计理念)
2. [核心配色系统](#核心配色系统)
3. [字体系统](#字体系统)
4. [视觉效果](#视觉效果)
5. [组件规范](#组件规范)
6. [使用指南](#使用指南)
7. [代码实现](#代码实现)

---

## 🎯 设计理念

### 核心价值观
**"AI科技 × 中国金融文化 × 现代极简"**

### 设计原则

#### 1. **双灵魂驱动**
- **技术灵魂**: AI优先，所有设计围绕AI能力展开
- **用户灵魂**: 从真实用户需求出发，追求Product-Market Fit

#### 2. **文化融合**
- **本土化**: 遵循中国股市传统认知（红涨绿跌）
- **国际化**: 融合现代国际设计语言
- **专业性**: 体现金融投资的严谨性

#### 3. **用户体验**
- **简单直接**: 核心功能一键可达
- **可信可靠**: 数据透明，逻辑清晰
- **及时有效**: 实时响应，优先级明确

---

## 🎨 核心配色系统

### 主要颜色规范

```css
/* GushenAI 品牌主色 */
--gushen-primary: #356BFD;     /* 主色蓝 - 科技、专业、信任 */
--gushen-accent: #FB9D0E;      /* 辅色橙 - 活力、创新、突出 */
--gushen-light: #EAEFFB;       /* 浅色 - 高亮、辅助 */
--gushen-bg: #FAFBFC;          /* 背景色 - 简洁、清爽 */

/* 中国股市传统色彩 */
--market-buy: #FF4444;         /* 红色 - 买入/多方/上涨 */
--market-sell: #00AA66;        /* 绿色 - 卖出/空方/下跌 */
--market-positive: #FF4444;    /* 正值显示 */
--market-negative: #00AA66;    /* 负值显示 */

/* 基础色彩 */
--text-primary: #1F2937;       /* 主要文字 */
--text-secondary: #6B7280;     /* 次要文字 */
--grid-color: #E5E7EB;         /* 网格线 */
--border-color: #D1D5DB;       /* 边框 */
```

### 席位类型专用配色

```css
/* 席位分类色彩 */
--seat-quant: #356BFD;         /* 量化 - 主色蓝 */
--seat-institution: #FB9D0E;   /* 机构 - 辅色橙 */
--seat-famous: #8B5CF6;        /* 知名游资 - 紫色 */
--seat-normal: #6B7280;        /* 普通席位 - 中性灰 */
```

### 语义化配色

| 用途 | 颜色 | HEX | 说明 |
|------|------|-----|------|
| 成功/盈利 | <span style="color:#FF4444">■</span> | `#FF4444` | 符合中国"红涨"传统 |
| 风险/亏损 | <span style="color:#00AA66">■</span> | `#00AA66` | 符合中国"绿跌"传统 |
| 信息/中性 | <span style="color:#1F2937">■</span> | `#1F2937` | 客观数据展示 |
| 品牌强调 | <span style="color:#356BFD">■</span> | `#356BFD` | GushenAI品牌识别 |
| 警告/提醒 | <span style="color:#FB9D0E">■</span> | `#FB9D0E` | 重要信息突出 |

---

## ✍️ 字体系统

### 字体族

```css
font-family: "'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', Arial, sans-serif";
```

### 字体层级

| 级别 | 字号 | 用途 | CSS类名 |
|------|------|------|---------|
| H1 | 28px | 页面主标题 | `.text-4xl` |
| H2 | 22px | 区块标题 | `.text-xl` |
| H3 | 18px | 子标题 | `.text-lg` |
| Body | 14px | 正文内容 | `.text-sm` |
| Caption | 12px | 说明文字 | `.text-xs` |

### 字重规范

```css
.font-normal    /* 400 - 正文 */
.font-medium    /* 500 - 重点信息 */
.font-semibold  /* 600 - 小标题 */
.font-bold      /* 700 - 主标题 */
```

---

## ✨ 视觉效果

### 阴影系统

```css
/* GushenAI 品牌阴影 */
.gushen-shadow {
    box-shadow: 0 20px 25px -5px rgba(53, 107, 253, 0.1), 
                0 10px 10px -5px rgba(53, 107, 253, 0.04);
}

/* 轻微阴影 */
.shadow-sm {
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

/* 中等阴影 */
.shadow-md {
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}
```

### 渐变效果

```css
/* 品牌渐变背景 */
.gushen-gradient {
    background: linear-gradient(135deg, rgba(53, 107, 253, 0.1) 0%, rgba(53, 107, 253, 0.05) 100%);
}

/* 页面背景渐变 */
.page-gradient {
    background: linear-gradient(135deg, #FAFBFC 0%, #EAEFFB 100%);
}

/* 科技光晕效果 */
.tech-glow::before {
    background: linear-gradient(45deg, rgba(255, 68, 68, 0.3), rgba(0, 170, 102, 0.3));
    filter: blur(10px);
    opacity: 0.7;
}
```

### 动画效果

```css
/* 淡入动画 */
.animate-fade-in {
    animation: fadeIn 1s ease-in-out;
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

/* 滑入动画 */
.animate-slide-up {
    animation: slideUp 0.8s ease-out;
}

@keyframes slideUp {
    from { 
        opacity: 0;
        transform: translateY(30px);
    }
    to { 
        opacity: 1;
        transform: translateY(0);
    }
}

/* 悬停效果 */
.hover-lift:hover {
    transform: translateY(-5px);
    transition: transform 0.3s ease;
}
```

---

## 🧩 组件规范

### 按钮设计

```css
/* 主要按钮 */
.btn-primary {
    background-color: #356BFD;
    color: white;
    padding: 0.75rem 1.5rem;
    border-radius: 0.5rem;
    font-weight: 600;
    transition: all 0.2s ease;
}

.btn-primary:hover {
    background-color: #2563EB;
    transform: translateY(-1px);
    box-shadow: 0 10px 20px rgba(53, 107, 253, 0.3);
}

/* 次要按钮 */
.btn-secondary {
    background-color: #FB9D0E;
    color: white;
    padding: 0.75rem 1.5rem;
    border-radius: 0.5rem;
    font-weight: 600;
}
```

### 卡片设计

```css
.card {
    background: white;
    border-radius: 1rem;
    padding: 1.5rem;
    box-shadow: 0 20px 25px -5px rgba(53, 107, 253, 0.1);
    border: 1px solid #E5E7EB;
}

.card-hover:hover {
    box-shadow: 0 25px 50px -12px rgba(53, 107, 253, 0.25);
    transform: translateY(-2px);
    transition: all 0.3s ease;
}
```

### 图标使用

```html
<!-- 品牌图标 -->
<i class="fas fa-robot text-gushen-accent"></i>        <!-- AI机器人 -->
<i class="fas fa-chart-line text-gushen-primary"></i>  <!-- 趋势分析 -->
<i class="fas fa-balance-scale text-gushen-primary"></i> <!-- 席位博弈 -->
<i class="fas fa-shield-alt text-gushen-primary"></i>  <!-- 安全可靠 -->

<!-- 功能图标 -->
<i class="fas fa-arrow-up text-market-buy"></i>        <!-- 上涨 -->
<i class="fas fa-arrow-down text-market-sell"></i>     <!-- 下跌 -->
<i class="fas fa-users text-primary"></i>              <!-- 席位 -->
<i class="fas fa-chart-bar text-accent"></i>           <!-- 数据 -->
```

---

## 📖 使用指南

### 配色使用原则

#### 1. **功能性优先**
- 买卖方向：严格使用红买绿卖的中国传统
- 数据正负：正值红色，负值绿色
- 品牌识别：主要UI元素使用品牌蓝

#### 2. **层次感营造**
- 主要信息：使用高对比度颜色
- 次要信息：降低饱和度和对比度
- 背景装饰：使用极低饱和度

#### 3. **情感化表达**
- 成功/正面：红色系，传达积极情绪
- 风险/警告：橙色系，引起适度注意
- 中性/客观：灰色系，保持专业感

### 响应式设计

```css
/* 移动端适配 */
@media (max-width: 768px) {
    .container {
        padding: 1rem;
    }
    
    .text-4xl {
        font-size: 1.875rem; /* 30px */
    }
    
    .chart-container {
        height: 400px;
        width: 100%;
    }
}

/* 桌面端优化 */
@media (min-width: 1024px) {
    .chart-container {
        height: 700px;
        width: 1400px;
    }
}
```

---

## 💻 代码实现

### Python配色定义

```python
class GushenDesignSystem:
    """GushenAI设计系统配色方案"""
    
    def __init__(self):
        # 主要配色
        self.colors = {
            # 品牌色彩
            'primary': '#356BFD',      # 主色蓝
            'accent': '#FB9D0E',       # 辅色橙  
            'light': '#EAEFFB',        # 浅色
            'background': '#FAFBFC',   # 背景色
            
            # 市场色彩（中国传统）
            'buy': '#FF4444',          # 红色 - 买入/上涨
            'sell': '#00AA66',         # 绿色 - 卖出/下跌
            'positive': '#FF4444',     # 正值
            'negative': '#00AA66',     # 负值
            
            # 基础色彩
            'text': '#1F2937',         # 主要文字
            'text_secondary': '#6B7280', # 次要文字
            'grid': '#E5E7EB',         # 网格线
            'border': '#D1D5DB',       # 边框
        }
        
        # 席位类型配色
        self.seat_colors = {
            '量化': '#356BFD',         # 主色蓝
            '机构': '#FB9D0E',         # 辅色橙
            '知名游资': '#8B5CF6',     # 紫色
            '普通席位': '#6B7280'      # 中性灰
        }
```

### CSS变量定义

```css
:root {
    /* GushenAI 品牌色彩 */
    --gushen-primary: #356BFD;
    --gushen-accent: #FB9D0E;
    --gushen-light: #EAEFFB;
    --gushen-bg: #FAFBFC;
    
    /* 市场色彩 */
    --market-buy: #FF4444;
    --market-sell: #00AA66;
    
    /* 基础色彩 */
    --text-primary: #1F2937;
    --text-secondary: #6B7280;
    --grid-color: #E5E7EB;
    
    /* 字体 */
    --font-family: "'PingFang SC', 'Microsoft YaHei', sans-serif";
    
    /* 间距 */
    --spacing-xs: 0.25rem;   /* 4px */
    --spacing-sm: 0.5rem;    /* 8px */
    --spacing-md: 1rem;      /* 16px */
    --spacing-lg: 1.5rem;    /* 24px */
    --spacing-xl: 2rem;      /* 32px */
    
    /* 圆角 */
    --radius-sm: 0.25rem;    /* 4px */
    --radius-md: 0.5rem;     /* 8px */
    --radius-lg: 1rem;       /* 16px */
    --radius-xl: 1.5rem;     /* 24px */
}
```

### TailwindCSS配置

```javascript
// tailwind.config.js
module.exports = {
    theme: {
        extend: {
            colors: {
                'gushen': {
                    'primary': '#356BFD',
                    'accent': '#FB9D0E', 
                    'light': '#EAEFFB',
                    'bg': '#FAFBFC',
                    'buy': '#FF4444',
                    'sell': '#00AA66'
                }
            },
            fontFamily: {
                'sans': ["'PingFang SC'", "'Microsoft YaHei'", 'sans-serif']
            },
            animation: {
                'fade-in': 'fadeIn 1s ease-in-out',
                'slide-up': 'slideUp 0.8s ease-out',
            }
        }
    }
}
```

---

## 🎯 设计检查清单

### 配色检查
- [ ] 是否遵循中国股市传统（红涨绿跌）
- [ ] 品牌色彩是否正确使用
- [ ] 对比度是否满足可访问性要求
- [ ] 色彩层次是否清晰

### 字体检查  
- [ ] 中文字体是否优先显示
- [ ] 字体大小是否符合层级规范
- [ ] 字重是否合理使用

### 交互检查
- [ ] 悬停效果是否一致
- [ ] 动画时长是否合适
- [ ] 响应式适配是否完整

### 品牌检查
- [ ] 是否体现GushenAI科技感
- [ ] 是否符合金融产品专业性
- [ ] 用户体验是否简洁直观

---

## 📝 更新日志

### v1.0 (2025-01-27)
- 初始版本发布
- 确立核心配色系统
- 定义字体和视觉效果规范
- 建立组件使用指南

---

**© 2025 GushenAI - 智能投资新时代** 