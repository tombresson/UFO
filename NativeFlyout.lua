-- NativeFlyout
-- native Blizzard flyouts embedded in UFO menus

-------------------------------------------------------------------------------
-- Module Loading
-------------------------------------------------------------------------------

---@type Ufo
local ADDON_NAME, Ufo = ...
Ufo.Wormhole()

-- SpellIcons is optional; this branch also works without the active indicator.
local function getSpellTexture(spellId)
    if SpellIcons then return SpellIcons:getTexture(spellId) end
    return C_Spell.GetSpellTexture(spellId)
end


---@class NativeFlyout
NativeFlyout = {}
NativeFlyout.groups = setmetatable({}, { __mode = "k" })

-------------------------------------------------------------------------------
-- Methods
-------------------------------------------------------------------------------

function NativeFlyout:findSpellBookSlot(flyoutId)
    -- spellbook slots change with specs and learned spells; flyout IDs are not spell IDs
    local bank = Enum.SpellBookSpellBank.Player
    for line = 1, C_SpellBook.GetNumSpellBookSkillLines() do
        local info = C_SpellBook.GetSpellBookSkillLineInfo(line)
        if info then
            for slot = info.itemIndexOffset + 1, info.itemIndexOffset + info.numSpellBookItems do
                local kind, id = C_SpellBook.GetSpellBookItemType(slot, bank)
                if kind == Enum.SpellBookItemType.Flyout and id == flyoutId then
                    return slot, bank
                end
            end
        end
    end
end

function NativeFlyout:pickup(flyoutId)
    local slot, bank = self:findSpellBookSlot(flyoutId)
    assert(slot, "Blizzard flyout is not in this character's spellbook")
    C_SpellBook.PickupSpellBookItem(slot, bank)
    local cursorType, cursorId = GetCursorInfo()
    assert(cursorType == "flyout" and cursorId == flyoutId, "Could not pick up Blizzard flyout")
end

function NativeFlyout:getIcon(flyoutId)
    local slot, bank = self:findSpellBookSlot(flyoutId)
    if slot then
        local icon = C_SpellBook.GetSpellBookItemTexture(slot, bank)
        if icon then return icon end
    end

    -- shared catalog entries may have no spellbook texture on this character; try a child spell
    local _, _, numSlots = GetFlyoutInfo(flyoutId)
    local fallback
    for i = 1, numSlots or 0 do
        local spellId, overrideId, isKnown = GetFlyoutSlotInfo(flyoutId, i)
        spellId = overrideId and overrideId ~= 0 and overrideId or spellId
        local icon = spellId and getSpellTexture(spellId)
        if icon then
            if isKnown then return icon end
            fallback = fallback or icon
        end
    end
    return fallback
end

-- open/close in the secure environment; the child SecureActionButtonTemplate handles casting
NativeFlyout.actionPrefix = "UFO_NATIVE_"
NativeFlyout.openScript = [=[
    local menu = self:GetFrameRef("%s")
    if not menu then return end
    if menu:IsShown() then
        menu:Hide()
        return
    end
    local count = menu:GetAttribute("count") or 0
    if count == 0 then return end
    local owner = menu:GetFrameRef("owner")
    for i = 1, owner:GetAttribute("UFO_NATIVE_COUNT") or 0 do
        local other = owner:GetFrameRef("UFO_NATIVE_MENU_" .. i)
        if other then other:Hide() end
    end
    -- clear the parent's number keys, Escape and main-key alias before binding this submenu
    local parent = menu:GetFrameRef("parentMenu")
    if parent and parent:IsShown() then
        parent:ClearBindings()
        menu:SetAttribute("UFO_NATIVE_PARENT_SUSPENDED", true)
    end
    local direction = self:GetAttribute("UFO_NATIVE_DIRECTION") or "UP"
    local horizontal = direction == "LEFT" or direction == "RIGHT"
    menu:ClearAllPoints()
    if direction == "UP" then
        menu:SetPoint("BOTTOM", self, "TOP", 0, 6)
    elseif direction == "DOWN" then
        menu:SetPoint("TOP", self, "BOTTOM", 0, -6)
    elseif direction == "LEFT" then
        menu:SetPoint("RIGHT", self, "LEFT", -6, 0)
    else
        menu:SetPoint("LEFT", self, "RIGHT", 6, 0)
    end
    menu:SetWidth(horizontal and (count * 36 + 8) or 44)
    menu:SetHeight(horizontal and 44 or (count * 36 + 8))
    for i = 1, count do
        local child = menu:GetFrameRef("child" .. i)
        child:SetAttribute("UFO_NATIVE_PRESSED", nil)
        child:ClearAllPoints()
        if direction == "UP" then
            child:SetPoint("BOTTOMLEFT", menu, "BOTTOMLEFT", 6, 6 + (i-1)*36)
        elseif direction == "LEFT" then
            child:SetPoint("TOPRIGHT", menu, "TOPRIGHT", -6 - (i-1)*36, -6)
        else
            child:SetPoint("TOPLEFT", menu, "TOPLEFT", 6 + (horizontal and (i-1)*36 or 0), -6 - (horizontal and 0 or (i-1)*36))
        end
    end
    menu:Show()
    menu:SetBindingClick(true, "ESCAPE", menu:GetName(), "LeftButton")
    if owner:GetAttribute("doKeybindTheButtonsOnTheFlyout") then
        for i = 1, math.min(count, 10) do
            local key = (i == 10) and "0" or tostring(i)
            menu:SetBindingClick(true, key, menu:GetFrameRef("child" .. i), "LeftButton")
        end
    end
]=]

NativeFlyout.onHide = [=[
    self:ClearBindings()
    if not self:GetAttribute("UFO_NATIVE_PARENT_SUSPENDED") then return end
    self:SetAttribute("UFO_NATIVE_PARENT_SUSPENDED", nil)
    local parent = self:GetFrameRef("parentMenu")
    if not parent or not parent:IsShown() then return end
    local owner = self:GetFrameRef("owner")
    parent:SetBindingClick(true, "ESCAPE", owner, parent:GetAttribute("UFO_OPEN_MOUSE_CLICK") or "LeftButton")
    if owner:GetAttribute("doKeybindTheButtonsOnTheFlyout") then
        for i = 1, math.min(parent:GetAttribute("IN_USE_BTN_COUNT") or 0, 10) do
            local target = parent:GetFrameRef("UFO_NATIVE_NUMBER_" .. i)
            if target then
                local key = (i == 10) and "0" or tostring(i)
                parent:SetBindingClick(true, key, target, "LeftButton")
                if i == 1 then
                    local alias = owner:GetAttribute("UFO_KEYBIND_1")
                    if alias then parent:SetBindingClick(true, alias, target, "LeftButton") end
                end
            end
        end
    end
]=]

NativeFlyout.closeAfterSpell = [=[
    if down then
        self:SetAttribute("UFO_NATIVE_PRESSED", true)
        return
    end
    -- ignore release of the key that opened the submenu; it may now be bound to a child
    if not self:GetAttribute("UFO_NATIVE_PRESSED") then return end
    self:SetAttribute("UFO_NATIVE_PRESSED", nil)
    local menu = self:GetFrameRef("submenu")
    menu:Hide()
    local parent = menu:GetFrameRef("parentMenu")
    local owner = menu:GetFrameRef("owner")
    local config = menu:GetFrameRef("config")
    if parent and (parent:GetAttribute("doCloseOnClick") or owner:GetAttribute("doCloseOnClick") or
        (config and config:GetAttribute("doCloseOnClick"))) then
        parent:Hide()
        parent:ClearBindings()
    end
]=]

function NativeFlyout:getAction(flyoutId)
    assert(type(flyoutId) == "number" and flyoutId > 0 and flyoutId == math.floor(flyoutId), "Invalid flyout ID")
    local action = self.actionPrefix .. flyoutId
    return action, "_" .. action, string.format(self.openScript, action)
end

function NativeFlyout:closeForOwner(owner)
    local group = self.groups[owner]
    if not group then return end
    for _, menu in pairs(group.menus) do menu:Hide() end
end

function NativeFlyout:prepare(button, def)
    assert(not InCombatLockdown(), "Configure native flyouts outside combat")
    local nested = button.ufoType == ButtonOnFlyoutMenu.ufoType
    local parentMenu = nested and button:getFlyoutMenu() or button.flyoutMenu
    local owner = nested and parentMenu:getParent() or button
    local action, key, script = self:getAction(def.flyoutId)
    local group = self.groups[owner]
    if not group then
        group = { menus = {}, count = 0 }
        self.groups[owner] = group
    end
    local menu = group.menus[def.flyoutId]
    if not menu then
        local name = owner:GetName() .. "_NativeFlyout" .. def.flyoutId
        menu = CreateFrame("Button", name, owner, "SecureHandlerClickTemplate,SecureHandlerShowHideTemplate")
        menu:Hide()
        menu:SetFrameStrata("DIALOG")
        menu:RegisterForClicks("AnyUp")
        menu:SetAttribute("_onclick", "self:Hide(); self:ClearBindings()")
        menu:SetAttribute("_onhide", self.onHide)
        menu:SetFrameRef("owner", owner)
        menu:SetFrameRef("parentMenu", parentMenu)
        if _G.UFO_DUM_DUM then menu:SetFrameRef("config", _G.UFO_DUM_DUM) end
        menu.children = {}
        local background = menu:CreateTexture(nil, "BACKGROUND")
        background:SetAllPoints()
        background:SetColorTexture(0.05, 0.05, 0.05, 0.95)
        group.menus[def.flyoutId] = menu
        group.count = group.count + 1
        owner:SetFrameRef("UFO_NATIVE_MENU_" .. group.count, menu)
        owner:SetAttribute("UFO_NATIVE_COUNT", group.count)
        local closeMenu = 'local menu = self:GetFrameRef("' .. action .. '"); if menu then menu:Hide() end'
        -- Direct primary/recent/random/cycle actions can show the submenu
        -- while the ordinary UFO menu is hidden. Close that sibling before
        -- it can compete with a newly opened parent menu's number bindings.
        SecureHandlerWrapScript(owner, "OnHide", menu, closeMenu)
        if parentMenu then
            for i = 1, 10 do
                local target = parentMenu:getButtonFrame(i)
                if target then parentMenu:SetFrameRef("UFO_NATIVE_NUMBER_" .. i, target) end
            end
            parentMenu:SetFrameRef(action, menu)
            SecureHandlerWrapScript(parentMenu, "OnHide", menu, closeMenu)
            SecureHandlerWrapScript(parentMenu, "OnShow", menu, closeMenu)
        end
    end

    menu:Hide()
    local _, _, numSlots = GetFlyoutInfo(def.flyoutId)
    local count = 0
    for slot = 1, numSlots or 0 do
        local spellId, overrideId, isKnown = GetFlyoutSlotInfo(def.flyoutId, slot)
        if isKnown then
            count = count + 1
            spellId = overrideId and overrideId ~= 0 and overrideId or spellId
            local child = menu.children[count]
            if not child then
                child = CreateFrame("CheckButton", menu:GetName() .. "_Spell" .. count, menu, "SecureActionButtonTemplate")
                child:SetSize(32, 32)
                if SpellIcons then SpellIcons:initializeIndicator(child) end
                child:RegisterForClicks("AnyDown", "AnyUp")
                child.icon = child:CreateTexture(nil, "ARTWORK")
                child.icon:SetAllPoints()
                child.HotKey = child:CreateFontString(nil, "OVERLAY", "NumberFontNormalSmall")
                child.HotKey:SetPoint("TOPRIGHT", child, "TOPRIGHT", -1, -1)
                child.HotKey:SetJustifyH("RIGHT")
                child:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
                SecureHandlerSetFrameRef(child, "submenu", menu)
                SecureHandlerWrapScript(child, "PostClick", menu, self.closeAfterSpell)
                child:SetScript("OnEnter", function(zelf)
                    GameTooltip:SetOwner(zelf, "ANCHOR_RIGHT")
                    GameTooltip:SetSpellByID(zelf:GetAttribute("spell"))
                end)
                child:SetScript("OnLeave", function() GameTooltip:Hide() end)
                menu.children[count] = child
                menu:SetFrameRef("child" .. count, child)
            end
            child:SetAttribute("type", "spell")
            child:SetAttribute("spell", spellId)
            child.icon:SetTexture(getSpellTexture(spellId))
            if SpellIcons then SpellIcons:updateIndicator(child, spellId) end
            local hotKey = ""
            if Config:get("doKeybindTheButtonsOnTheFlyout") and count <= 10 then
                hotKey = (count == 10) and "0" or tostring(count)
            end
            child.HotKey:SetText(hotKey)
            child:Show()
        end
    end
    for i = count + 1, #menu.children do
        menu.children[i]:Hide()
        menu.children[i]:SetAttribute("type", nil)
        if SpellIcons then SpellIcons:updateIndicator(menu.children[i], nil) end
    end
    menu:SetAttribute("count", count)

    -- prime/recent/random/cycle copy the action to the germ, so prepare its handler before combat too
    for _, launcher in ipairs({button, owner}) do
        launcher:SetFrameRef(action, menu)
        launcher:SetAttribute(key, script)
    end
    -- GetFrameRef is secure-env only; keep a Lua reference for the arrow state
    button.ufoNativeFlyoutMenu = menu
    button.ufoNativeFlyoutId = def.flyoutId
    button:SetAttribute("UFO_NATIVE_DIRECTION", nested and button:GetPopupDirection() or owner:getDirection())
    owner:SetAttribute("UFO_NATIVE_DIRECTION", owner:getDirection())
end

function NativeFlyout:isOpen(button)
    local def = button.btnDef
    if not def or def.type ~= ButtonType.FLYOUT then return false end
    if button.ufoNativeFlyoutId ~= def.flyoutId then return false end
    local menu = button.ufoNativeFlyoutMenu
    return menu and menu:IsShown() or false
end
