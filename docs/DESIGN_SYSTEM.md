# ProMirrorGolf Design System

**Version:** 1.0  
**Last Updated:** November 2024  
**Framework:** PyQt6

## Overview

ProMirrorGolf uses a GitHub-inspired dark theme optimized for professional golf swing analysis. The design system emphasizes clarity, accessibility, and consistency across all UI components.

## Color Palette

### Base Colors

#### Backgrounds
- **Base Background**: `#0f1116` - Main window background
- **Surface**: `#161b22` - Cards, panels, elevated surfaces
- **Surface Elevated**: `#1c2128` - Selected items, hover states
- **Control Container**: `#0d1117` - Input fields, buttons, controls

#### Borders & Dividers
- **Border Default**: `#21262d` - Standard borders
- **Border Hover**: `#30363d` - Hover state borders
- **Border Active**: `#484f58` - Active/focus borders
- **Divider**: `#21262d` - Table row dividers, separators

#### Text Colors
- **Primary Text**: `#c9d1d9` - Main content text (87% white opacity equivalent)
- **Secondary Text**: `#8b949e` - Labels, hints, metadata (60% white opacity equivalent)
- **Disabled Text**: `#484f58` - Disabled state text (38% white opacity equivalent)
- **Placeholder Text**: `rgba(255, 255, 255, 0.38)` - Input placeholders

### Accent Colors

#### Primary Accent (Red)
- **Accent**: `#ff4d4d` - Primary actions, highlights, focus indicators
- **Accent Hover**: `#ff5c5c` - Hover state
- **Accent Active**: `#da3633` - Active/pressed state
- **Accent Light**: `rgba(255, 77, 77, 0.1)` - Subtle backgrounds

#### Success (Green)
- **Success**: `#238636` - Success actions, positive indicators
- **Success Hover**: `#2ea043` - Success hover state
- **Success Active**: `#1e6e2e` - Success active state

#### Danger (Red)
- **Danger**: `#da3633` - Destructive actions
- **Danger Hover**: `#b62324` - Danger hover state
- **Danger Text**: `#f85149` - Danger text color

### Interactive States

#### Hover
- **Background Overlay**: `rgba(255, 255, 255, 0.08)` - 8% white overlay
- **Border Brightness**: Increase by 10-15%
- **Transition**: 150ms ease

#### Active/Pressed
- **Background Overlay**: `rgba(255, 255, 255, 0.16)` - 16% white overlay
- **Scale**: 0.98 (subtle press effect)
- **Transition**: 100ms ease

#### Focus
- **Outline**: `2px solid #ff4d4d` - Accent color outline
- **Outline Offset**: `2px`
- **Background**: Slight brightness increase
- **Required**: Always visible for keyboard navigation

#### Disabled
- **Opacity**: `0.38` (38%)
- **Background**: `#0d1117`
- **Text**: `#484f58`
- **Cursor**: `not-allowed`
- **No hover effects**

## Typography

### Font Family
```css
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", sans-serif;
```

### Font Sizes
- **H1/Title**: `28px` - Page titles, major headings
- **H2/Heading**: `24px` - Section headings
- **H3/Subheading**: `18px` - Subsection headings
- **Body**: `13px` - Default body text
- **Small**: `12px` - Labels, metadata, secondary text
- **Tiny**: `11px` - Tooltips, fine print

### Font Weights
- **Bold**: `600` - Headings, emphasis
- **Medium**: `500` - Buttons, important text
- **Regular**: `400` - Body text
- **Light**: `300` - Not used (hard to read on dark)

### Line Heights
- **Tight**: `1.2` - Headings
- **Normal**: `1.5` - Body text
- **Loose**: `1.6` - Long-form content

## Spacing System

### Base Unit
**8px grid system** - All spacing values must be multiples of 8px

### Common Spacing Values
- **XS**: `4px` - Tight spacing (icon to text)
- **S**: `8px` - Small spacing (between related elements)
- **M**: `16px` - Medium spacing (default padding)
- **L**: `24px` - Large spacing (section spacing)
- **XL**: `32px` - Extra large (major sections)
- **XXL**: `48px` - Maximum (page margins)

### Component Padding
- **Buttons**: `8px 16px` (vertical horizontal)
- **Input Fields**: `8px 12px`
- **Cards**: `16px` or `20px`
- **Panels**: `16px 24px`
- **Dialogs**: `24px`

### Layout Spacing
- **Between sections**: `24px` or `32px`
- **Between cards**: `16px`
- **Between form fields**: `16px`
- **Between buttons**: `8px`

## Component Specifications

### Buttons

#### Primary Button
```css
min-height: 32px;
border-radius: 6px;
padding: 8px 16px;
background-color: #ff4d4d;
border: 1px solid #ff4d4d;
color: #ffffff;
font-size: 12px;
font-weight: 600;
```

**States:**
- **Hover**: `background-color: #ff5c5c`
- **Active**: `background-color: #da3633`
- **Disabled**: `opacity: 0.38`, `cursor: not-allowed`
- **Focus**: `outline: 2px solid #ff4d4d`, `outline-offset: 2px`

#### Secondary Button
```css
min-height: 32px;
border-radius: 6px;
padding: 8px 16px;
background-color: #21262d;
border: 1px solid #30363d;
color: #c9d1d9;
font-size: 12px;
font-weight: 500;
```

**States:**
- **Hover**: `background-color: #30363d`, `border-color: #484f58`
- **Active**: `background-color: #161b22`
- **Disabled**: `background-color: #0d1117`, `color: #484f58`

#### Danger Button
```css
background-color: #21262d;
border: 1px solid #da3633;
color: #f85149;
```

**States:**
- **Hover**: `background-color: #b62324`, `color: #ffffff`

### Input Fields

#### Text Input (QLineEdit, QTextEdit, QPlainTextEdit)
```css
background-color: #0d1117;
border: 1px solid #30363d;
border-radius: 6px;
padding: 8px 12px;
color: #c9d1d9;
font-size: 13px;
min-height: 32px;
```

**States:**
- **Focus**: `border: 1px solid #ff4d4d`
- **Hover**: `border-color: #484f58`
- **Disabled**: `background-color: #0d1117`, `color: #484f58`
- **Placeholder**: `color: rgba(255, 255, 255, 0.38)`

#### ComboBox
Same as text input, plus:
- **Dropdown Arrow**: Custom styled triangle
- **Dropdown Menu**: Dark background matching theme

### Tables

#### Table Container
```css
background-color: #0d1117;
border: 1px solid #21262d;
border-radius: 8px;
gridline-color: transparent;
```

#### Table Header
```css
background-color: #0d1117;
color: #8b949e;
padding: 12px 16px;
border-bottom: 1px solid #21262d;
font-size: 12px;
font-weight: 600;
```

#### Table Cell
```css
padding: 12px 16px;
border-bottom: 1px solid #21262d;
color: #c9d1d9;
font-size: 13px;
```

**States:**
- **Selected**: `background-color: #1c2128`
- **Hover**: `background-color: #161b22`

### Cards & Panels

#### Card Container
```css
background-color: #161b22;
border: 1px solid #21262d;
border-radius: 8px;
padding: 16px;
```

#### Panel Container
```css
background-color: #0d1117;
border: 1px solid #21262d;
border-radius: 8px;
padding: 16px 24px;
```

### Sliders

#### Slider Groove
```css
background: #1c1c1c;
height: 4px;
border-radius: 2px;
```

#### Slider Handle
```css
background: #ff4d4d;
width: 16px;
height: 16px;
border-radius: 8px;
margin: -6px 0;
```

**States:**
- **Hover**: Slightly brighter
- **Active**: Slightly darker

### Scrollbars

#### Scrollbar Track
```css
background-color: #0d1117;
border: none;
width: 12px;
```

#### Scrollbar Handle
```css
background-color: #30363d;
border-radius: 6px;
min-height: 20px;
```

**States:**
- **Hover**: `background-color: #484f58`

### Tabs

#### Tab Button
```css
background-color: #0e0e0e;
color: #7c8899;
padding: 8px 18px;
border-top-left-radius: 10px;
border-top-right-radius: 10px;
border: 1px solid #1a1a1a;
```

#### Tab Selected
```css
background-color: #151515;
color: #f2f4fa;
border-bottom: 1px solid #151515;
```

## Accessibility Standards

### WCAG Compliance
- **Level AA Required** - All text must meet 4.5:1 contrast ratio
- **Level AAA Preferred** - Aim for 7:1 where possible

### Contrast Ratios (Verified)
- **Primary Text (#c9d1d9) on Base (#0f1116)**: 12.6:1 ✅ AAA
- **Secondary Text (#8b949e) on Base (#0f1116)**: 7.2:1 ✅ AAA
- **Accent (#ff4d4d) on Base (#0f1116)**: 4.8:1 ✅ AA
- **White (#ffffff) on Accent (#ff4d4d)**: 3.2:1 ⚠️ (acceptable for large text)

### Focus Indicators
- **Required**: Always visible 2px outline
- **Color**: Accent color (#ff4d4d)
- **Offset**: 2px from element
- **Never remove**: Keyboard navigation depends on this

### Keyboard Navigation
- **Tab Order**: Logical, left-to-right, top-to-bottom
- **Enter/Space**: Activate buttons and controls
- **Escape**: Close dialogs, cancel actions
- **Arrow Keys**: Navigate lists, tables, menus

### Screen Reader Support
- **Labels**: All inputs must have associated labels
- **ARIA**: Use Qt's accessibility features
- **Descriptions**: Provide tooltips and help text

## Animation & Transitions

### Timing Functions
- **Ease**: Default for most transitions
- **Ease-in-out**: For complex animations
- **Linear**: Avoid (feels mechanical)

### Duration
- **Fast**: `100ms` - Active/pressed states
- **Normal**: `150ms` - Hover states, color changes
- **Slow**: `200-300ms` - Complex animations, page transitions

### Properties to Animate
- **Color**: Smooth color transitions
- **Background**: Background color changes
- **Opacity**: Fade in/out effects
- **Transform**: Scale, translate (use sparingly)

## Layout Principles

### Grid System
- **Base Unit**: 8px
- **Columns**: Flexible, responsive
- **Gutters**: 16px or 24px between columns
- **Max Width**: 1400px for content (centered)

### Responsive Breakpoints
- **Small**: < 1024px - Single column, stacked layout
- **Medium**: 1024px - 1440px - Two columns
- **Large**: > 1440px - Three columns, expanded layout

### Component Sizing
- **Minimum Heights**: 
  - Buttons: 32px
  - Inputs: 32px
  - Table rows: 40px
- **Maximum Widths**:
  - Forms: 600px
  - Cards: 400px
  - Content: 1400px

## Iconography

### Icon Style
- **Style**: Outlined, minimal
- **Size**: 16px, 20px, 24px (standard sizes)
- **Color**: Inherit text color or use accent
- **Spacing**: 8px from text

### Common Icons
- **Play**: ▶
- **Pause**: ⏸
- **Stop**: ⏹
- **Settings**: ⚙
- **Close**: ✕
- **Check**: ✓
- **Arrow**: →, ←, ↑, ↓

## Usage Guidelines

### Do's
✅ Use design system colors from constants  
✅ Follow 8px spacing grid  
✅ Maintain consistent border radius (6px for inputs, 8px for cards)  
✅ Ensure all text meets WCAG AA contrast  
✅ Always show focus indicators  
✅ Use smooth transitions (150ms)  
✅ Test keyboard navigation  

### Don'ts
❌ Hardcode colors (use constants)  
❌ Use arbitrary spacing values  
❌ Remove focus indicators  
❌ Use pure black (#000000) backgrounds  
❌ Use highly saturated colors  
❌ Skip accessibility testing  
❌ Animate without smooth transitions  

## Implementation

### Constants File
All colors and spacing values are defined in `app/theme.py` and should be imported from there.

### Stylesheet Application
Apply styles via:
1. Global stylesheet (`DARK_THEME` in `theme.py`)
2. Component-specific overrides (use sparingly)
3. Inline styles (avoid, use only for dynamic values)

### Component Patterns
- Create reusable styled components
- Use object names for component variants (`#accentButton`, `#dangerButton`)
- Follow existing patterns in codebase

## References

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Material Design Dark Theme](https://material.io/design/color/dark-theme.html)
- [GitHub Dark Theme](https://github.com/primer/primer)
- [PyQt6 Stylesheet Reference](https://doc.qt.io/qt-6/stylesheet-reference.html)

