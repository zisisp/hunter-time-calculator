# LLM Instruction: Mobile App Design for `index.html`

Use these guidelines to recreate the **Hunter 30% Time Calculator** in a Flutter mobile app (iOS and Android). Mirror the current `index.html` experience while adapting to native mobile patterns. Keep the wording concise so it can be fed directly to an LLM.

## Product Goals
- Deliver the same calculator logic as `index.html`: compute target health (30% of V), decay rate (V / 60 per minute), minutes to hit 30%, and minutes to reach 100%, with MM:SS output formatting.
- Preserve the friendly “hunter” aesthetic: forest-to-brown gradient background, parchment-style card, and gold/green accents.
- Maintain validation behavior and helper messaging so users never see empty or confusing results.

## UI / UX Blueprint
- **Layout**: One scrollable card centered on the screen; include generous padding and drop shadow similar to the web card.
- **Color & Typography**: Use the same palette as the web: deep greens (#1a472a, #2d5a3d), browns (#8b4513, #8b6914), parchment (#f5f3e8), and white text on dark bars. Use a clean system font stack equivalent (e.g., `SF Pro`/`Roboto`).
- **Inputs**:
  - Two numeric fields: **Total health (V)** and **Current health (C)**.
  - Spinner/stepper buttons on both sides (+/−) mirroring the web layout; enforce non-negative numbers and prevent C from exceeding V.
  - Inline validation messages under each field with red styling when invalid.
- **Health Bar**:
  - Progress bar showing `C / V` with centered text showing rounded values (e.g., `325 / 1000`).
  - Switch bar to a red gradient when below 30%; keep a separate label below that shows the target health value.
- **Results Section**:
  - Show: formatted MM:SS to reach 30%, formatted MM:SS to reach 100%, the target health, and the rate per minute.
  - Include the “already at target” notice when `C >= target`.
  - Reveal results only when inputs are valid.
- **Metadata Blocks**: Display friend code and referral code just like the web version.
- **Copy interactions**: Provide a tap-to-copy affordance for codes (use platform clipboard APIs and a brief toast/snackbar confirmation).

## Behavior & Validation
- Replicate the pure functions from `index.html`:
  - `computeTarget(V) = 0.3 * V`
  - `computeRatePerMinute(V) = V / 60`
  - `computeMinutes(V, C) = max(0, 60 * (0.3 - C / V))`, but return 0 when `V <= 0` or `C >= target`
  - `computeMinutesTo100(V, C) = max(0, 60 * (1 - C / V))`, but return 0 when `V <= 0` or `C >= V`
  - Format numbers with grouping and fixed decimals similar to the web outputs.
- Run validation before calculations; hide the results block until inputs are valid.
- Default calculation should run on first load with sensible starting values.

## Flutter Implementation Notes
- Use a single `MaterialApp` with a themed `Scaffold` and a `Card` to mirror the parchment container.
- Use `TextFormField` with input formatters for numbers and custom `Stepper`/`IconButton` controls for increment/decrement.
- Use `LinearProgressIndicator` or a custom `Container` with animated width to recreate the health bar; support color swap below 30%.
- Apply responsive padding and `MediaQuery` safe areas; ensure comfortable spacing on small screens.
- Manage state with a lightweight approach (e.g., `StatefulWidget`); keep computation in pure helper methods.

## Deployment & Automation
- Use **Fastlane** for both platforms:
  - iOS: lanes for build, test, and App Store/TestFlight upload; handle code signing via match or API keys.
  - Android: lanes for build, test, and Play Store deployment with supply; keep keystore setup documented.
- Add GitHub Actions workflows to lint, test, and trigger Fastlane lanes on main and release branches. Cache Flutter SDK and Gradle where possible.
- Provide sample `.env`/secrets guidance for Fastlane and CI (API keys, keystore passwords, Apple credentials) without committing secrets.

## Delivery Checklist
- UI matches the web layout and palette while respecting platform conventions.
- Validation, calculations, and “already at target” behavior match the web.
- Copy-to-clipboard works on both platforms.
- CI uses GitHub Actions; distribution uses Fastlane with documented lanes for iOS and Android.
