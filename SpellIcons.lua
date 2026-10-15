-- SpellIcons
-- spell artwork and active-state indicators

-------------------------------------------------------------------------------
-- Module Loading
-------------------------------------------------------------------------------

---@type Ufo
local ADDON_NAME, Ufo = ...
Ufo.Wormhole()

---@class SpellIcons
SpellIcons = {}

-------------------------------------------------------------------------------
-- Methods
-------------------------------------------------------------------------------

local function isPublic(value)
    return not issecretvalue or not issecretvalue(value)
end

local function isPassiveSpell(spellId)
    if not C_SpellBook.FindSpellBookSlotForSpell or not C_SpellBook.GetSpellBookItemInfo then return false end
    local slot, bank = C_SpellBook.FindSpellBookSlotForSpell(spellId, true, false)
    local info = slot and C_SpellBook.GetSpellBookItemInfo(slot, bank)
    return info and info.isPassive
end

local function getActiveState(spellId)
    if C_Minimap and C_Minimap.GetNumTrackingTypes and C_Minimap.GetTrackingInfo then
        for i = 1, C_Minimap.GetNumTrackingTypes() do
            local info = C_Minimap.GetTrackingInfo(i)
            if info and isPublic(info.spellID) and info.spellID == spellId and isPublic(info.active) then
                return info.active
            end
        end
    end
    if C_Spell.IsCurrentSpell then
        local current = C_Spell.IsCurrentSpell(spellId)
        if isPublic(current) and current then return true end
    end
    if not C_UnitAuras or not C_UnitAuras.GetPlayerAuraBySpellID then return end
    local aura = C_UnitAuras.GetPlayerAuraBySpellID(spellId)
    if not isPublic(aura) or not aura then return end
    -- mark this spell's own helpful effect; this includes timed buffs, not just toggles
    for _, field in ipairs({"spellId", "sourceUnit", "isHelpful", "isHarmful"}) do
        if not isPublic(aura[field]) then return end
    end
    if aura.spellId ~= spellId or aura.sourceUnit ~= "player" or
        aura.isHelpful ~= true or aura.isHarmful == true then return end
    local ok, passive = pcall(isPassiveSpell, spellId)
    if ok and (not isPublic(passive) or passive) then return end
    return true
end

function SpellIcons:getActiveState(spellId)
    if not spellId then return end
    local ok, active = pcall(getActiveState, spellId)
    if ok and isPublic(active) then return active end
end

function SpellIcons:initializeIndicator(button)
    if button.ufoActiveBorder then return end
    -- one texture keeps the corners and edges aligned when the UI is scaled
    local border = button:CreateTexture(nil, "OVERLAY", nil, 4)
    border:SetTexture("Interface\\AddOns\\" .. ADDON_NAME .. "\\ui\\ActiveBorder")
    border:SetPoint("TOPLEFT", button, "TOPLEFT", -3, 3)
    border:SetPoint("BOTTOMRIGHT", button, "BOTTOMRIGHT", 3, -3)
    border:SetVertexColor(0.2, 1, 0.4)
    border:Hide()
    button.ufoActiveBorder = {border}
end

function SpellIcons:updateIndicator(button, spellId)
    -- textures are created during initialization, outside combat; unknown states stay unmarked
    if not button.ufoActiveBorder then return end
    local active = self:getActiveState(spellId) == true
    for _, edge in ipairs(button.ufoActiveBorder) do edge:SetShown(active) end
end

function SpellIcons:getTexture(spellId)
    local spellIcon, _, conditionalIcon = C_Spell.GetSpellTexture(spellId)
    -- use this spell's own artwork, including any conditional texture supplied by Bliz
    return conditionalIcon or spellIcon
end

function SpellIcons:requestRefresh(event)
    if not Ufo.hasShitCalmedTheFuckDown or self.refreshQueued then return end
    self.refreshQueued = true
    -- let Bliz finish the state change and combine events from this frame; leave secure actions alone
    C_Timer.After(0, function()
        self.refreshQueued = nil
        self:refresh(event)
    end)
end

function SpellIcons:refreshButton(button, event)
    local def = button:getDef()
    self:updateIndicator(button, def and def.spellId)
    if not def or not def.spellId then return end
    local icon
    if button.ufoType == "Germ" then
        -- keep the UFO's custom icon, if any
        icon = button:getIcon()
    else
        icon = def:getIcon()
    end
    if icon then button:setIcon(icon, event) end
end

function SpellIcons:refresh(event)
    if not Ufo.hasShitCalmedTheFuckDown then return end
    GermCommander:forEachActiveGerm(function(germ)
        self:refreshButton(germ, event)
        germ.flyoutMenu:forEachButton(function(button)
            self:refreshButton(button, event)
        end)
    end)
    if Catalog.flyoutMenu then
        Catalog.flyoutMenu:forEachButton(function(button)
            self:refreshButton(button, event)
        end)
    end
    for _, group in pairs(NativeFlyout.groups) do
        for _, menu in pairs(group.menus) do
            for _, child in ipairs(menu.children) do
                if child:GetAttribute("type") == "spell" then
                    local spellId = child:GetAttribute("spell")
                    local icon = self:getTexture(spellId)
                    if icon then child.icon:SetTexture(icon) end
                    self:updateIndicator(child, spellId)
                else
                    self:updateIndicator(child, nil)
                end
            end
        end
    end
end
