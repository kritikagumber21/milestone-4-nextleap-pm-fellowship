---
name: Fintech Emerald System
colors:
  surface: '#f9f9ff'
  surface-dim: '#d7dae6'
  surface-bright: '#f9f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f1f3ff'
  surface-container: '#ebedfa'
  surface-container-high: '#e5e8f4'
  surface-container-highest: '#dfe2ef'
  on-surface: '#181c24'
  on-surface-variant: '#3c4a43'
  inverse-surface: '#2c303a'
  inverse-on-surface: '#eef0fd'
  outline: '#6b7b72'
  outline-variant: '#bacac1'
  surface-tint: '#006c4f'
  primary: '#006c4f'
  on-primary: '#ffffff'
  primary-container: '#00d09c'
  on-primary-container: '#00533c'
  inverse-primary: '#2fe0aa'
  secondary: '#3247e2'
  on-secondary: '#ffffff'
  secondary-container: '#4f63fb'
  on-secondary-container: '#fffbff'
  tertiary: '#af3015'
  on-tertiary: '#ffffff'
  tertiary-container: '#ff9e88'
  on-tertiary-container: '#8f1900'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#59fdc5'
  primary-fixed-dim: '#2fe0aa'
  on-primary-fixed: '#002116'
  on-primary-fixed-variant: '#00513b'
  secondary-fixed: '#dfe0ff'
  secondary-fixed-dim: '#bcc2ff'
  on-secondary-fixed: '#000b62'
  on-secondary-fixed-variant: '#102bcd'
  tertiary-fixed: '#ffdad3'
  tertiary-fixed-dim: '#ffb4a4'
  on-tertiary-fixed: '#3d0600'
  on-tertiary-fixed-variant: '#8c1800'
  background: '#f9f9ff'
  on-background: '#181c24'
  surface-variant: '#dfe2ef'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 44px
    fontWeight: '700'
    lineHeight: 52px
    letterSpacing: -0.02em
  headline-xl:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.015em
  headline-xl-mobile:
    fontFamily: Inter
    fontSize: 26px
    fontWeight: '700'
    lineHeight: 34px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  headline-sm:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
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
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
  label-lg:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Inter
    fontSize: 10px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.04em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.25rem
  gutter-desktop: 1.5rem
  margin: 1rem
  margin-desktop: 2.5rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

This design system embodies modern consumer investing: accessible, transparent, empowering, and friction-free. It bridges retail finance with institutional rigor, presenting complex market data through an intuitive, optimistic lens.

The visual style is rooted in **Corporate / Modern Minimalism** with consumer fintech touches. Surfaces are predominantly crisp white and soft tinted slates, punctuated by a signature vibrant emerald teal that denotes growth, balance, and financial vitality. The secondary periwinkle-blue accent (derived from the brand mark) introduces depth and technology confidence. Visuals rely on precise typographic hierarchy, generous breathing room, whisper-thin borders, and delicate ambient shadows rather than heavy ornament.

## Colors

The color palette is built for rapid scanning, trust, and absolute clarity across investment data:

- **Primary (`#00D09C`)**: The core brand teal/emerald. Represents positive market yield, active states, key conversion buttons, and affirmative indicators. Paired with dark slate text for accessible contrast on interactive surfaces.
- **Secondary (`#5367FF`)**: A bright periwinkle indigo reflecting the brand's secondary mark color. Used for informative badges, multi-asset categorization (e.g., mutual funds, US stocks), educational tooltips, and secondary interactive accents.
- **Tertiary (`#EB5B3C`)**: Standard financial red for loss metrics, negative percentage deltas, sell actions, and critical alert states.
- **Neutral (`#1E222B`)**: Deep ink navy for high-contrast headline readability. Subordinate text tiers transition through `#44475B` (body), `#7C7E8C` (subtext/captions), and `#E8ECEF` (border lines).
- **Backgrounds & Surfaces**: Base canvas is pure `#FFFFFF`, accompanied by `#F8F9FA` for secondary modules and `#F0F4F7` for subtle container fills and interactive hover fills.

## Typography

Typography is clean, highly legible, and optimized for tabular figures and financial values using **Inter**.

- **Numeric Rendering**: All monetary statistics, P&L tallies, and stock tickers should leverage tabular numbers (`font-feature-settings: "tnum"`) to maintain optical alignment across tables and watchlist listings.
- **Hierarchy Rules**: Primary currency amounts and hero portfolio balances use `display-lg` or `headline-xl` in `700` weight. Supporting ticker symbols, stock codes, and market capitalization badges rely on `label-sm` or `label-md` with slight letter tracking.
- **Body Hierarchy**: General financial disclosures and article insights use `body-md` in regular weight (`400`) tinted to `#44475B`, preventing harsh visual fatigue on white surfaces.

## Layout & Spacing

The layout model is anchored on an 8pt modular grid (with a 4pt subgrid for compact metric rows and pill badges):

- **Grid Architecture**: 
  - **Desktop (1200px+)**: 12-column responsive grid with `margin-desktop: 2.5rem` and `gutter-desktop: 1.5rem`. Max page content width is constrained to `1240px` for optimal chart readability.
  - **Tablet (768px - 1199px)**: 8-column grid with `margin: 1.5rem` and `gutter: 1.25rem`.
  - **Mobile (320px - 767px)**: 4-column fluid grid with `margin: 1rem` and `gutter: 0.75rem`.
- **Rhythm & Padding**: Cards use internal padding of `space-md` on mobile and `space-lg` on desktop. Horizontal stock lists utilize strict vertical cadence (`space-sm` to `space-md`) to ensure dense, scannable data visualization.

## Elevation & Depth

Visual depth is achieved through ultra-soft ambient shadowing and crisp structural hairline borders rather than heavy drop shadows:

- **Surface Layering**:
  - **Canvas (Level 0)**: Pure `#FFFFFF` baseline.
  - **Sub-surface (Level 1)**: `#F8F9FA` for alternate row stripes, page sidebars, and input containers.
  - **Card Containers (Level 2)**: Crisp white surfaces bordered with `1px solid #E8ECEF` and paired with shadow `0 2px 8px -2px rgba(30, 34, 43, 0.04)`.
  - **Floating / Hover Tiers (Level 3)**: Interactive stock cards, search drop-downs, and popovers use `0 8px 24px -4px rgba(30, 34, 43, 0.08)` with border `#E1E6EB`.
  - **Modal / Bottom Sheets (Level 4)**: Backdrop scrim of `rgba(30, 34, 43, 0.40)` with card elevation `0 16px 40px -8px rgba(30, 34, 43, 0.16)`.

## Shapes

The design uses a clean, contemporary rounded geometry (`roundedness: 2` = 8px base border radius):

- **Base Components**: Standard buttons, input fields, investment cards, and modal windows inherit `8px` (`0.5rem`) corner radiuses.
- **Pill Badges & Filter Chips**: Filter chips, market status pills (Open/Closed), and percentage gain/loss indicators utilize fully rounded caps (`9999px` / `rounded-full`) for high scanability.
- **Compound Cards**: Large nested sections (e.g., portfolio overview cards) scale up to `12px` or `16px` (`rounded-lg` / `rounded-xl`) to preserve organic visual nests.

## Components

- **Buttons**:
  - *Primary*: Filled `#00D09C` background with `#1E222B` bold text for maximum contrast and energetic brand presence. Hover state darkens gently to `#00B386`. Height: 44px (touch-friendly). Radius: 8px.
  - *Secondary / Outlined*: Hairline `1.5px solid #00D09C` border, transparent background, text `#00A37A`.
  - *Tertiary / Ghost*: Slate `#44475B` text with `#F0F4F7` background on hover.
  - *Destructive / Sell*: `#EB5B3C` filled or soft red tint (`#FDECE8`) with `#EB5B3C` label text.

- **Chips & Metric Badges**:
  - *Positive Delta Pill*: Background `#E6FAF5`, text `#008765`, bold label with up-triangle or `+` sign.
  - *Negative Delta Pill*: Background `#FDECE8`, text `#C93B1D`, bold label with down-triangle or `-` sign.
  - *Filter Chips*: Neutral `#F8F9FA` with 1px border `#E8ECEF`, shifting to `#1E222B` text and `#00D09C` border tint when active.

- **Input Fields**:
  - Border: `1px solid #DFE3E8`, background: `#FFFFFF`, radius: 8px, height: 44px.
  - Focus state: Border transitions to `#00D09C` with a soft `0 0 0 3px rgba(0, 208, 156, 0.15)` focus ring.
  - Financial amount inputs: Large monospace or tabular `Inter` display size with fixed currency prefix (`₹`, `$`) in muted `#7C7E8C`.

- **Cards & Data Lists**:
  - *Portfolio Card*: Clean white container with `#E8ECEF` hairline outline. Features bold asset total, mini sparkline chart in `#00D09C` or `#EB5B3C`, and subtle metadata caption.
  - *Watchlist Item*: Borderless list row with bottom hairline separator (`#F0F4F7`), avatar/company logo (circle, 36px), title in `14px semi-bold`, and right-aligned realtime ticker price and % pill.