# Hunter 30% Time Calculator

A single-page tool for Monster Hunter Now that shows how long it takes for your hunter to naturally regenerate health back to 30% and 100% of their maximum HP.

## Features
- **Guided inputs:** Spinner buttons and inline validation make it easy to set total health (V) and current health (C) without entering invalid values. A live health bar mirrors the numbers you enter. 【F:index.html†L377-L435】
- **Real-time timing:** Calculates time to reach 30% and 100% health, highlights when you are already at the target, and displays target/rate details without reloading the page. 【F:index.html†L440-L491】
- **Built-in formulas:** The calculator lists the exact regeneration math for reference so you can double-check results. 【F:index.html†L480-L488】
- **Shareable codes:** Friend and referral codes are shown directly on the page for easy copying. 【F:index.html†L456-L466】

## How to use
1. Open `index.html` in your browser (no build step required).
2. Set **Total Health (V)** with the +/− buttons or by typing a value.
3. Set **Current Health (C)** the same way. The health bar and validation messages update immediately.
4. Read the cards to see the formatted time to hit 30% and 100% health, the exact target HP, and the recovery rate per minute.
5. Share the friend/referral codes if you want others to add you.

## Regeneration formulas
- **Target health:** `0.3 × V`
- **Rate per minute:** `V ÷ 60`
- **Time to 30%:** `t = 60 × (0.3 − C/V)` (0 if current health is already at or above the target)
- **Time to 100%:** `t = 60 × (1 − C/V)` (0 if current health is already full)

These equations are shown directly on the page so players can verify the calculations. 【F:index.html†L480-L488】

## Development notes
- Everything is contained in `index.html`; open it directly or host it with any static file server.
   
