# Native Blizzard flyouts

This local build adds Blizzard spellbook flyouts as buttons inside UFO menus.
Drag a flyout such as Sharpen Your Knife or Warbands from your spellbook into
a UFO in the catalog, then put that UFO on an action bar as usual. Click the
embedded button to open its submenu. Click it again or press Escape to close it.

The submenu uses UFO-owned secure spell buttons populated from Blizzard's
flyout data. It does not invoke or reparent Blizzard's shared SpellFlyout.
This replaces the original implementation, which could trigger a blocked-action
dialog when selecting a spell. Install this build and `/reload` before retesting
to clear the earlier UI taint.

The nested menu opens perpendicular to the UFO menu. UFO stays open while
you choose a nested action, including when Close on Click is enabled. Selecting
a nested spell closes the submenu; Close on Click also closes the parent UFO.
Normal spell and item buttons retain their existing Close on Click behavior.

With UFO's number-key binding option enabled, an open submenu takes over
`1` through `9` and `0` (the tenth option), with numbers shown on its buttons.
For example, press your UFO key, then `2` to open its second entry, then `1`
to use the first spell in that submenu. Escape closes the submenu and restores
the parent UFO's number keys. Selecting a spell also restores them if Close on
Click leaves the parent open. Closing the UFO clears both layers' overrides. Opening the ordinary UFO menu
also closes a submenu opened directly by a primary/recent/random/cycle action.
Resetting or hiding its owning action button closes any remaining submenu.

Flyout IDs are saved; the submenu refreshes from Blizzard's data outside combat
when UFO handles spell and flyout update events. Unknown or
empty flyouts are hidden on characters that cannot use them. They remain in
the shared catalog. Primary, recent, random and cycle behavior use the same
restricted submenu handler as a direct click.

## Install and try

Spell buttons keep their own artwork and show a slightly rounded green edge
with a feathered outer glow when their
active state is readable: enabled minimap tracking, a current spell action,
or a matching helpful player-applied effect. This includes timed effects;
an active glow does not mean that clicking the spell will cancel it.
Unknown or restricted states stay unmarked. There are no spell-ID mappings,
shared active spell icons, or spare action-bar copies required. Blizzard's
own conditional spell artwork and custom UFO icons remain supported.
Appearance updates leave secure actions and number-key bindings intact.

1. Exit WoW. Back up your existing `Interface/AddOns/UFO` folder and the
   account and character `SavedVariables/UFO.lua` files under `WTF`.
2. Extract the supplied ZIP into the Retail `Interface/AddOns` directory.
   It contains a top-level `UFO` folder with its required libraries.
3. Launch WoW, enable UFO and open `/ufo`. Drag one of the Blizzard flyouts
   into the catalog, then put the UFO on a bar.
4. Test opening, closing and selecting a nested spell; try both mouse and
   UFO number keys, Close on Click, and each bar direction.
5. Test primary/recent/random/cycle choices, switching specs, dragging the
   flyout back out of the catalog, and reloading with `/reload`.
6. Test an allowed nested action in combat and watch for blocked-action or
   Lua errors. Editing and dragging remain out-of-combat operations.

Native flyouts, nested number bindings, and the active indicator have been
exercised during development in WoW. Automated Lua 5.1 mock checks also cover
menu transitions and syntax. The menu lifecycle fixes added during review
still need in-game validation, including combat restrictions. Addon managers
may overwrite this local build.

## Development

Upstream: https://github.com/ScottIngram/UFO

Run `python tests/test_native_flyouts.py` with `lupa` installed. In this
workspace it can reuse `ContextLayouts/.test-deps`.

The implementation follows the live Blizzard UI source mirror:

- https://github.com/Gethe/wow-ui-source/blob/live/Interface/AddOns/Blizzard_FrameXML/SecureTemplates.lua
- https://github.com/Gethe/wow-ui-source/blob/live/Interface/AddOns/Blizzard_ActionBar/Shared/SpellFlyout.lua
- https://github.com/Gethe/wow-ui-source/blob/live/Interface/AddOns/Blizzard_Flyout/Flyout.lua

UFO and this modification remain under the included Mozilla Public License 2.0.
