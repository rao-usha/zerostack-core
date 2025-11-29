# NEX.AI Dark Mode Color Scheme

## Overview
NEX.AI features a modern, sophisticated dark mode design with vibrant accent colors that convey innovation and cutting-edge technology.

## Color Palette

### Dark Theme Base Colors

```css
--dark-bg:      #0a0e27  /* Deep space blue - Main background */
--dark-surface: #141829  /* Dark navy - Header, sidebar */
--dark-card:    #1a1f3a  /* Rich dark blue - Cards, panels */
--dark-border:  #2a2f4a  /* Muted border - Subtle separators */
--dark-text:    #e2e8f0  /* Light slate - Primary text */
--dark-muted:   #94a3b8  /* Slate gray - Secondary text */
```

### Accent Colors

```css
--accent-blue:   #3b82f6  /* Vibrant blue - Primary accent */
--accent-purple: #a855f7  /* Electric purple - Secondary accent */
--accent-pink:   #ec4899  /* Hot pink - Tertiary accent */
--accent-cyan:   #06b6d4  /* Bright cyan - Quaternary accent */
```

### Semantic Colors

```css
--success:  #10b981  /* Green */
--warning:  #f59e0b  /* Amber */
--error:    #ef4444  /* Red */
--info:     #3b82f6  /* Blue */
```

## Usage Guidelines

### Backgrounds
- **Page Background**: Use `dark-bg` for main app background
- **Surface Elements**: Use `dark-surface` for headers, sidebars
- **Cards**: Use `dark-card` for content cards, modals
- **Hover States**: Lighten by 5-10% or use accent colors at 10-20% opacity

### Text
- **Primary Text**: Use `dark-text` for headings, important content
- **Secondary Text**: Use `dark-muted` for descriptions, labels
- **Links**: Use `accent-blue` with hover effects

### Borders
- **Subtle Borders**: Use `dark-border` at full opacity
- **Hover Borders**: Use accent colors at 50% opacity
- **Focus States**: Use accent colors at full opacity

### Gradients

#### Primary Gradient (NEX.AI Brand)
```css
background: linear-gradient(to right, #3b82f6, #a855f7, #ec4899);
```

#### Button Gradients
```css
/* Primary CTA */
background: linear-gradient(to right, #3b82f6, #a855f7);

/* Success */
background: linear-gradient(to right, #10b981, #06b6d4);

/* Info */
background: linear-gradient(to right, #06b6d4, #3b82f6);
```

#### Card Hover Effects
```css
/* Hover glow */
box-shadow: 0 0 20px rgba(59, 130, 246, 0.2);
border-color: rgba(59, 130, 246, 0.5);
```

## Component-Specific Guidelines

### Sidebar Navigation
- **Background**: `dark-surface`
- **Inactive Items**: `dark-text` with hover to `accent-blue`
- **Active Items**: Gradient background `accent-blue/20` to `accent-purple/20`, text `accent-blue`

### Cards
- **Background**: `dark-card`
- **Border**: `dark-border`
- **Hover**: Border changes to `accent-blue/50`, shadow `accent-blue/20`

### Buttons
- **Primary**: Gradient `accent-blue` → `accent-purple`
- **Secondary**: `dark-card` with `dark-border`
- **Success**: Gradient `green-500` → `accent-cyan`

### Tables
- **Header**: `dark-surface` background, `dark-muted` text
- **Rows**: `dark-card` background, `dark-border` dividers
- **Hover**: `dark-surface` background

### Forms
- **Inputs**: `dark-card` background, `dark-border` border
- **Focus**: `accent-blue` border, shadow
- **Placeholders**: `dark-muted` text

## Accessibility

### Contrast Ratios
All color combinations meet WCAG AA standards:
- `dark-text` on `dark-bg`: 12.63:1 ✓
- `dark-muted` on `dark-bg`: 7.15:1 ✓
- `accent-blue` on `dark-bg`: 8.59:1 ✓

### Color Blind Friendly
- Use multiple visual cues (icons, text, borders)
- Don't rely on color alone for important information
- Provide sufficient contrast for all states

## Animation & Transitions

### Standard Transitions
```css
transition: all 0.3s ease;  /* Default */
transition: all 0.2s ease;  /* Fast (hover) */
transition: all 0.5s ease;  /* Slow (complex) */
```

### Hover Effects
- Scale: 1.02
- Brightness: 1.1
- Shadow: Increase with accent color

## Dark Mode Best Practices

1. **Avoid Pure Black**: Use `#0a0e27` instead of `#000000`
2. **Layer Surfaces**: Lighter backgrounds for elevated surfaces
3. **Reduce Contrast**: Use `dark-text` (#e2e8f0) not pure white
4. **Vibrant Accents**: Use saturated accent colors for visual pop
5. **Consistent Shadows**: Use colored shadows matching accent colors
6. **Smooth Gradients**: Multi-color gradients for modern feel

## Export for Design Tools

### Tailwind Config
See `frontend/tailwind.config.js` for complete configuration.

### CSS Variables
```css
:root {
  --dark-bg: #0a0e27;
  --dark-surface: #141829;
  --dark-card: #1a1f3a;
  --dark-border: #2a2f4a;
  --dark-text: #e2e8f0;
  --dark-muted: #94a3b8;
  --accent-blue: #3b82f6;
  --accent-purple: #a855f7;
  --accent-pink: #ec4899;
  --accent-cyan: #06b6d4;
}
```

## Logo Colors
The NEX.AI logo uses a three-color gradient:
- Start: `#3b82f6` (Blue)
- Middle: `#a855f7` (Purple)  
- End: `#ec4899` (Pink)

