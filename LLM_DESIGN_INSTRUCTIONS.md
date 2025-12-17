# LLM Instruction: Mirror the `index.html` Design for Mobile

Use these guidelines to recreate the **Hunter 30% Time Calculator** from `index.html` inside a Flutter mobile app (iOS and Android). Keep the wording concise so it can be fed directly to an LLM.

## Product Goals
- Replicate every calculation shown on the web: target health (30% of V), rate per minute (V/60), time to reach 30%, and time to reach 100%, all formatted as `Xm Ys`.
- Preserve the exact hunter theme: full-screen forest-to-brown gradient background, parchment cards with a gold (#8b6914) border and shadow, and deep green text accents.
- Keep validation and messaging identical so users never see empty or confusing results.

## UI / UX Blueprint (match the visible web layout)
- **Overall layout**: One scrollable column of cards centered in the viewport. Each card has generous padding, rounded corners, and a strong drop shadow on parchment (#f5f3e8).
- **Typography & palette**: System font stack (`-apple-system`, `Roboto`, etc.). Headings use deep green (#2d5a3d); subheadings use saddle brown (#8b4513). Body text uses muted gray (#5a5a5a).
- **Hero card content**:
  - Title: “Monster Hunter Now”; subtitle: “Hunter Health Recovery Calculator”; description: “Calculate the time needed for your hunter's health to regenerate.”
  - Maker note centered under the description: “Made by ZedIsDead”.
- **Input controls**:
  - Two numeric fields with side steppers: **Total Health (V)** defaults to `100`; **Current Health (C)** defaults to `1` but is treated as `0` for calculations (so the first render shows the 18m baseline).
  - Steppers are square, dark green (#2d5a3d) with white text; press state darkens (#1a472a).
  - Inputs use thick gold borders (#8b6914); focus border switches to deep green (#2d5a3d). Show inline red validation text beneath each input.
- **Health bar**:
  - Dark wooden wrapper with gold border and inset shadow; inside fill is a vertical green gradient (`#4caf50` to `#2e7d32`).
  - Centered white text reads `rounded C / rounded V` (e.g., `1 / 100`).
  - Below the bar, show “Target health: {target}” using whole-number formatting. Swap fill to a red gradient (`#f44336` to `#c62828`) when below 30%.
- **Results card** (always present but only shows values when inputs are valid):
  - An optional green notice “Already at or above 30%” appears when `C >= target`.
  - Primary block for 30% timing uses a pale green background (#e8f5e9), green border, and text. Show the label “Time to reach 30%:”, the large time value, and “Target: {target with 1 decimal}”.
  - Secondary block for 100% timing uses pale orange (#fff3e0) with brown (#8b4513) border and deep orange text (#bf360c) for the time value.
  - Codes strip below shows two stacked labels “My Friend Code” and “My Referral Code” with bold green values and a QR image to the right (`assets/friend-referral-qr.png.png`). Ensure both text values are exposed for tap-to-copy.
  - Summary rows list “Target (30% of V)” and “Rate per minute (V/60)” with bold right-aligned values.
- **Help card**:
  - Header “Formula & Constraints”. Show the formula block `t = 60 × (0.3 − C/V) minutes` and a bulleted list exactly matching the web copy (target, rate, 18m/60m defaults, and the C ≥ Target rule).

## Behavior & Validation
- Pure functions should match the web:
  - `computeTarget(V) = 0.3 * V`
  - `computeRatePerMinute(V) = V / 60`
  - `computeMinutes(V, C) = max(0, 60 * (0.3 - C / V))`, but return 0 when `V <= 0` or `C >= target`
  - `computeMinutesTo100(V, C) = max(0, 60 * (1 - C / V))`, but return 0 when `V <= 0` or `C >= V`
  - `toMMSS` formatting matches the web’s `Xm Ys` output (two-digit seconds).
- Inputs must be non-negative; run validation before calculations and hide results data when invalid.
- On first load, auto-calculate with the default values (100 max, 1 current treated as 0) so the UI shows 30% target of 30, 1/100 bar, 18m to 30%, and 60m to 100%.

## Flutter Implementation Notes
- Single `MaterialApp` with a themed `Scaffold`; use `Card` widgets to mirror the parchment containers and keep the gold borders/shadows.
- Use `TextFormField` with numeric-only input formatters and custom stepper buttons for +/- controls.
- Health bar can be a `Container` with animated width; swap to red gradient when percentage < 30% and overlay centered text.
- Provide tap-to-copy interactions for friend/referral codes with a brief snackbar/toast confirmation.
- Respect safe areas and add vertical padding so the scrollable stack breathes on small screens.

## Deployment & Automation
- Use **Fastlane** for iOS and Android: lanes for build, test, and store uploads (App Store/TestFlight and Play Store). Handle signing with match/API keys or keystore configuration.
- Add GitHub Actions workflows to lint, test, and trigger Fastlane lanes on main/release branches. Cache Flutter SDK and Gradle where possible.
- Include sample `.env`/secrets guidance for Fastlane and CI without committing secrets.

## Delivery Checklist
- UI matches the web’s copy, colors, and layout described above.
- Validation, calculations, and “already at target” behavior are identical to `index.html`.
- Copy-to-clipboard works for both codes.
- CI uses GitHub Actions; distribution uses Fastlane with documented lanes for iOS and Android.
