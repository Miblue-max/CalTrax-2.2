# CalTraX PRO — Calorie & Hydration Tracker

Current release: 2.2.0 (see `src/js/config.js`). Data schema: 2.

## Structure
```
index.html              App shell (single entry point)
calorie_tracker.html    Redirect to index.html (keeps old links working)
sw.js                   Offline cache (bump CACHE_NAME on every release)
manifest.json           PWA install metadata
src/
  css/app.css           Styles and accessibility rules
  js/config.js          Version and language settings
  js/sound.js           Synthesised sound effects, mute control
  js/app.js             Application logic, state, rendering, i18n
  data/foods.js         Food database (319 items, EN / BN / HI names)
  assets/logo.png       Logo
```

## Languages
English, Bengali (bn), Hindi (hi). UI strings live in `I18N` inside `app.js`.
Food names live in `foods.js` as `name_en`, `name_bn`, `name_hi`.

## Releasing
1. Update `APP_VERSION` in `src/js/config.js`.
2. If saved-data format changed, bump `SCHEMA_VERSION` and add a migration in `app.js`.
3. Bump `CACHE_NAME` in `sw.js` so users get the new files.

## Testing
```
pip install playwright && playwright install chromium
python3 tests/smoke_test.py          # 14 checks: boot, wizard, search, logging,
                                     # custom targets, reset, sound, languages
```

## Daily targets
Users see suggested targets (calculated from body metrics and goal) and can
override calories, protein, carbs and fat on the Profile tab. Blank = suggested.
Values outside safe limits are rejected with a message.

## Data and migrations
Saved data carries a schema number (`app_schema`). On load, `runMigrations()` in
`app.js` upgrades older data. Data written by a newer app version is never
modified, so users who downgrade do not lose anything.

## Important
This app is a tracking aid, not medical advice. Clinical targets (sodium, carbs,
calories) must be reviewed by a qualified clinician before public release.
