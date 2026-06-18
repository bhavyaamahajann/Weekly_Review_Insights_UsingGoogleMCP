---
name: Review Pulse Design System
colors:
  surface: '#f9f9ff'
  surface-dim: '#cfdaf2'
  surface-bright: '#f9f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f0f3ff'
  surface-container: '#e7eeff'
  surface-container-high: '#dee8ff'
  surface-container-highest: '#d8e3fb'
  on-surface: '#111c2d'
  on-surface-variant: '#444655'
  inverse-surface: '#263143'
  inverse-on-surface: '#ecf1ff'
  outline: '#757687'
  outline-variant: '#c5c5d8'
  surface-tint: '#354ae4'
  primary: '#3247e2'
  on-primary: '#ffffff'
  primary-container: '#4f63fb'
  on-primary-container: '#fffbff'
  inverse-primary: '#bcc2ff'
  secondary: '#006c4f'
  on-secondary: '#ffffff'
  secondary-container: '#59fdc5'
  on-secondary-container: '#007354'
  tertiary: '#9c3f00'
  on-tertiary: '#ffffff'
  tertiary-container: '#c45100'
  on-tertiary-container: '#fffbff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dfe0ff'
  primary-fixed-dim: '#bcc2ff'
  on-primary-fixed: '#000b62'
  on-primary-fixed-variant: '#102bcd'
  secondary-fixed: '#59fdc5'
  secondary-fixed-dim: '#2fe0aa'
  on-secondary-fixed: '#002116'
  on-secondary-fixed-variant: '#00513b'
  tertiary-fixed: '#ffdbcc'
  tertiary-fixed-dim: '#ffb693'
  on-tertiary-fixed: '#351000'
  on-tertiary-fixed-variant: '#7a3000'
  background: '#f9f9ff'
  on-background: '#111c2d'
  surface-variant: '#d8e3fb'
typography:
  display-lg:
    fontFamily: Outfit
    fontSize: 40px
    fontWeight: '600'
    lineHeight: 48px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Outfit
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Outfit
    fontSize: 18px
    fontWeight: '500'
    lineHeight: 24px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  label-bold:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
  headline-md-mobile:
    fontFamily: Outfit
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 4px
  container-padding: 24px
  card-gap: 20px
  row-height-dense: 48px
  row-height-standard: 64px
  gutter: 16px
---

## Brand & Style

This design system embodies a premium, data-centric SaaS aesthetic that bridges the gap between high-finance reliability and modern technology agility. The brand personality is clinical, efficient, and sophisticated, designed to evoke a sense of "informed control" for power users managing high volumes of critical feedback.

The visual style is **Corporate Modern with a Minimalist edge**. It utilizes a "Paper & Ink" philosophy—using crisp white surfaces and purposeful gray scales to establish a neutral stage where vibrant brand accents (Blue and Mint) highlight actionable insights and status transitions. The interface prioritizes readability through generous whitespace and a high-density information architecture that remains uncluttered.

## Colors

The palette is anchored by the signature Groww Blue and Mint Green, functioning as the primary drivers for interaction and positive confirmation.

- **Primary (Blue):** Used for primary actions, active navigation states, and brand-critical elements.
- **Secondary (Mint):** Reserved for success states, "Yes" indicators, and high-quality ratings.
- **Accent (Urgent Orange):** A tertiary safety color specifically for high-priority alerts and urgent statuses.
- **Neutral Scale:** A sophisticated range of cool grays (from Slate-50 to Slate-900) ensures depth and hierarchical clarity without introducing visual noise.
- **Surface Strategy:** Backgrounds utilize a "Soft Gray" (`#F8FAFC`) for the main canvas, while "Paper White" (`#FFFFFF`) is reserved for foreground cards and data containers to create subtle, natural separation.

## Typography

This system employs a dual-font strategy to balance character with utility. **Outfit** is used for headlines and display elements to provide a modern, premium geometric feel. **Inter** is utilized for all body text, data tables, and labels, selected for its exceptional legibility at small sizes and high-density environments.

Hierarchy is established primarily through weight and color rather than excessive size shifts. Secondary information (like timestamps or IDs) should use `body-sm` in a muted gray color. Data headers must use `label-bold` with slight letter spacing to ensure clear categorization of tabular content.

## Layout & Spacing

The design system follows a **Fixed Grid** philosophy for desktop layouts, centering content within a 1280px max-width container to maintain a professional, dashboard-like focus. 

- **Grid:** 12-column system with 24px margins and 16px gutters.
- **Rhythm:** A 4px baseline grid governs all internal padding. 
- **Density:** High-density architecture is achieved through controlled row heights in tables (48px for dense, 64px for multi-line data). 
- **Breakpoints:** 
  - **Desktop (1024px+):** Full sidebar navigation, 12-column grid.
  - **Tablet (768px - 1023px):** 8-column grid, collapsed sidebar, reduced horizontal margins (16px).
  - **Mobile (Up to 767px):** 4-column grid, stacked card components instead of complex tables, 12px horizontal margins.

## Elevation & Depth

To maintain a "premium" feel, the system avoids heavy drop shadows in favor of **Tonal Layers and Low-Contrast Outlines**.

Depth is created through three primary tiers:
1.  **Canvas (Level 0):** The base background color (`#F8FAFC`).
2.  **Surface (Level 1):** Primary cards and containers using White (`#FFFFFF`) with a subtle 1px border (`#E2E8F0`). A very soft, diffused shadow (0px 2px 4px rgba(0,0,0,0.02)) is applied to separate cards from the canvas.
3.  **Overlay (Level 2):** Modals and dropdown menus, utilizing a slightly more pronounced shadow (0px 10px 20px rgba(0,0,0,0.05)) and a crisp 1px border to ensure focus.

Status badges use a "soft-fill" approach: a 10% opacity background of their respective status color combined with a 100% opacity text for high readability without visual weight.

## Shapes

The shape language is **Soft and Professional**, utilizing a disciplined corner radius that avoids the playfulness of fully rounded "pill" styles while remaining more approachable than sharp corners.

- **Standard Elements:** Buttons, Input fields, and Badges use a **4px (0.25rem)** radius.
- **Large Containers:** Cards and Modals use a **8px (0.5rem)** radius.
- **Status Pills:** Status indicators (Urgent, High) use a slightly more rounded **12px** radius to distinguish them as floating metadata elements.
- **Iconography:** Use 2px stroke weight icons with slightly rounded caps to match the UI's geometry.

## Components

### Buttons
- **Primary:** Groww Blue background, white text. No gradient. 
- **Secondary/Ghost:** Transparent background, Blue border or Gray border for neutral actions.
- **Action Links:** Text-only with a right-pointing chevron for table-row interactions ("View Details").

### Status Badges
- **Urgent:** Orange-600 text on Orange-50 background. 
- **High/Yes:** Mint-600 text on Mint-50 background.
- **No/Low:** Slate-500 text on Slate-100 background.
- All badges should use `label-bold` typography for maximum clarity.

### Tables & Lists
- **Headers:** Light gray background (`#F1F5F9`) with `label-bold` text.
- **Rows:** White background with a 1px bottom border. Hover state should use a subtle gray tint (`#F8FAFC`).
- **Cell Alignment:** Numeric IDs and status badges are centered; text-heavy "Topics" or "Root Causes" are left-aligned.

### Input Fields
- Borders are Slate-200. On focus, the border transitions to Groww Blue with a soft 2px blue glow.
- Labels are placed above the field in `label-md`.

### Cards
- White fill, 1px Slate-200 border. 
- Header section inside cards should have a subtle 1px bottom divider to separate the title from the content.