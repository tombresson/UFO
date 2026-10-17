"""Catalog docking/lifecycle checks with the same Lua 5.1 runtime as other tests."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "ContextLayouts" / ".test-deps"))
from lupa.lua51 import LuaRuntime


MOCK = r'''
Ufo = {Wormhole=function() end}
UfoMixIn = {mixInto=function() end}
local log = setmetatable({colorize=function(_, text) return text end},
    {__index=function(self) return function() return self end end})
zebug = setmetatable({}, {__index=function() return log end})
Event = {new=function() return {} end}
NORMAL_FONT_COLOR, GREEN_FONT_COLOR, BRIGHTBLUE_FONT_COLOR = {}, {}, {}
FrameType = {BUTTON='Button'}
Anchor = {LEFT='LEFT', RIGHT='RIGHT', TOPLEFT='TOPLEFT', TOPRIGHT='TOPRIGHT',
          BOTTOMLEFT='BOTTOMLEFT', BOTTOMRIGHT='BOTTOMRIGHT'}
Script = {ON_CLICK='OnClick', ON_ENTER='OnEnter', ON_LEAVE='OnLeave'}
MouseClick = {LEFT='LeftButton'}
TooltipAnchor = {LEFT='ANCHOR_LEFT'}
L10N = {LEFT_CLICK='Left-click', RIGHT_CLICK='Right-click', OPEN_CATALOG='Open catalog',
        OPEN_CONFIG='Settings'}
sprintf = string.format
combat = false
function InCombatLockdown() return combat end
function isInCombatLockdown() return combat end
Config = {toggle=function() settingsOpened=(settingsOpened or 0)+1 end}
GameTooltip = {}
function GameTooltip:SetOwner(owner) self.owner=owner end
function GameTooltip:GetOwner() return self.owner end
function GameTooltip:SetText(text) self.text=text end
function GameTooltip:Show() self.shown=true end
function GameTooltip:Hide() self.shown=false end

frames = {}
local Frame = {}
local function mutable() assert(not combat, 'Protected frame mutation during combat') end
function Frame:GetName() return self.name end
function Frame:GetParent() return self.parent end
function Frame:SetParent(parent) mutable(); self.parent=parent end
function Frame:GetWidth() return self.width end
function Frame:SetSize(width, height) mutable(); self.width=width; self.height=height end
function Frame:ClearAllPoints() mutable(); self.points={} end
function Frame:SetPoint(...) mutable(); self.points[#self.points+1]={...} end
function Frame:SetFrameStrata(strata) mutable(); self.strata=strata end
function Frame:GetFrameStrata() return self.strata end
function Frame:SetFrameLevel(level) mutable(); self.level=level end
function Frame:GetFrameLevel() return self.level end
function Frame:IsMouseOver() return false end
function Frame:SetBackdrop() mutable() end
function Frame:SetBackdropColor() mutable() end
function Frame:SetBackdropBorderColor() mutable() end
function Frame:SetHitRectInsets(...) mutable(); self.hitInsets={...} end
function Frame:SetFontString() end
function Frame:SetPushedTextOffset() end
function Frame:RegisterForClicks(...) self.clicks={...} end
function Frame:CreateFontString()
    return {SetPoint=function() end, SetTextColor=function() end,
            SetText=function(self, text) self.text=text end}
end
function Frame:CreateTexture()
    return {SetAllPoints=function() end, SetColorTexture=function() end,
        SetSize=function(self, w, h) self.width=w; self.height=h end,
        SetWidth=function(self, w) self.width=w end,
        SetHeight=function(self, h) self.height=h end,
        ClearAllPoints=function() end,
        SetPoint=function() end,
        SetTexture=function(self, path) self.path=path end,
        SetVertexColor=function() end,
        SetTexCoord=function(self, ...) self.texCoords={...} end,
        SetAtlas=function(self, atlas) self.atlas=atlas end}
end
function Frame:SetNormalTexture(path) self.normal=self:CreateTexture(); self.normal.path=path end
function Frame:SetPushedTexture(path) self.pushed=self:CreateTexture(); self.pushed.path=path end
function Frame:SetHighlightTexture(path) self.highlight=self:CreateTexture(); self.highlight.path=path end
function Frame:GetNormalTexture() return self.normal end
function Frame:GetPushedTexture() return self.pushed end
function Frame:GetHighlightTexture() return self.highlight end
function SetClampedTextureRotation(texture, degrees) texture.rotation=degrees end
function Frame:RegisterEvent(event) self.events[event]=true end
function Frame:UnregisterEvent(event) self.events[event]=nil end
function Frame:SetScript(event, fn) self.scripts[event]=fn end
function Frame:HookScript(event, fn)
    local previous=self.scripts[event]
    self.scripts[event]=function(...)
        if previous then previous(...) end
        fn(...)
    end
end
function Frame:RunScript(event, ...)
    if self.scripts[event] then self.scripts[event](self, ...) end
end
function Frame:IsShown() return self.shown end
function Frame:IsVisible() return self.shown and (not self.parent or self.parent:IsVisible()) end
local function visibilityChanged(frame, event)
    frame:RunScript(event)
    for _, child in ipairs(frames) do
        if child.parent==frame and child.shown then visibilityChanged(child, event) end
    end
end
function Frame:Show()
    mutable()
    if not self.shown then
        self.shown=true
        if self:IsVisible() then visibilityChanged(self, 'OnShow') end
    end
end
function Frame:Hide()
    mutable()
    local visible=self:IsVisible()
    self.shown=false
    if visible then visibilityChanged(self, 'OnHide') end
end
function CreateFrame(kind, name, parent, template)
    mutable()
    local frame=setmetatable({name=name,parent=parent,template=template,shown=true,
        scripts={},events={},points={},width=800,level=5,strata='MEDIUM'}, {__index=Frame})
    frames[#frames+1]=frame
    if name then _G[name]=frame end
    return frame
end
function fireEvent(event)
    for _,frame in ipairs(frames) do
        if frame.events[event] then frame:RunScript('OnEvent', event) end
    end
end
function SetUIPanelAttribute(frame, key, value) mutable(); frame[key..'Attribute']=value end
function UpdateUIPanelPositions() mutable() end
UFO_DUM_DUM=CreateFrame('Frame', 'UFO_DUM_DUM')
UFO_Catalog=CreateFrame('Frame', 'UFO_Catalog', UFO_DUM_DUM)
UFO_Catalog.width=150
UFO_Catalog:Hide()
PlayerSpellsFrame=CreateFrame('Frame', 'PlayerSpellsFrame')
CollectionsJournal=CreateFrame('Frame', 'CollectionsJournal')
MacroFrame=CreateFrame('Frame', 'MacroFrame')
ProfessionsBookFrame=CreateFrame('Frame', 'ProfessionsBookFrame')
function tab(parent) return _G['UFO_BtnToToggleCatalog_On'..parent:GetName()] end
function click(parent, button) tab(parent):RunScript('OnClick', button or 'LeftButton') end
function assertDocked(parent, open)
    local button=assert(tab(parent))
    assert(button:GetParent()==parent, 'Launcher must keep the Blizzard host as its parent')
    assert(button.Arrow.rotation==(open and 270 or 90), 'Arrow must reflect current dock state')
    assert(button.points[1][2]==(open and UFO_Catalog or parent), 'Wrong launcher anchor')
end
'''


class CatalogTab(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute(MOCK)
        self.lua.execute((ROOT / "ui/Catalog.lua").read_text(encoding="utf-8"),
                         "UFO", self.lua.globals().Ufo)

    def check(self, source):
        self.lua.execute(source)

    def test_all_hosts_work_without_title_bar_controls(self):
        self.check('''
            for _,host in ipairs({PlayerSpellsFrame,CollectionsJournal,MacroFrame,ProfessionsBookFrame}) do
                Catalog:createToggleButton(host)
                assertDocked(host, false)
                assert(tab(host).width==20 and tab(host).height==88)
                local count=#frames
                Catalog:createToggleButton(host)
                assert(#frames==count, 'Repeated loads must not duplicate launchers')
            end
        ''')

    def test_click_opens_existing_catalog_and_returns_tab_on_close(self):
        self.check('''
            Catalog:createToggleButton(PlayerSpellsFrame)
            click(PlayerSpellsFrame)
            assert(UFO_Catalog:IsShown() and UFO_Catalog:GetParent()==PlayerSpellsFrame)
            assertDocked(PlayerSpellsFrame, true)
            assert(PlayerSpellsFrame.widthAttribute==800+150+14, 'Reserve catalog and protruding tab')
            click(PlayerSpellsFrame)
            assert(not UFO_Catalog:IsShown())
            assertDocked(PlayerSpellsFrame, false)
            assert(PlayerSpellsFrame.widthAttribute==800)
        ''')

    def test_switching_hosts_restores_old_launcher_and_width(self):
        self.check('''
            Catalog:createToggleButton(PlayerSpellsFrame)
            Catalog:createToggleButton(CollectionsJournal)
            click(PlayerSpellsFrame)
            click(CollectionsJournal)
            assertDocked(PlayerSpellsFrame, false)
            assertDocked(CollectionsJournal, true)
            assert(PlayerSpellsFrame.widthAttribute==800)
            assert(CollectionsJournal.widthAttribute==964)
        ''')

    def test_external_catalog_hide_and_show_update_tab(self):
        self.check('''
            Catalog:createToggleButton(MacroFrame)
            click(MacroFrame)
            UFO_Catalog:Hide()
            assertDocked(MacroFrame, false)
            UFO_Catalog:Show()
            assertDocked(MacroFrame, true)
        ''')

    def test_parent_hide_preserves_docked_state_for_reopening(self):
        self.check('''
            Catalog:createToggleButton(PlayerSpellsFrame)
            click(PlayerSpellsFrame)
            tab(PlayerSpellsFrame):RunScript('OnEnter')
            assert(not GameTooltip.shown)
            PlayerSpellsFrame:Hide()
            assert(not tab(PlayerSpellsFrame):IsVisible() and not GameTooltip.shown)
            PlayerSpellsFrame:Show()
            assertDocked(PlayerSpellsFrame, true)
            assert(tab(PlayerSpellsFrame):IsVisible())
        ''')

    def test_combat_blocks_clicks_and_defers_creation_and_layout(self):
        self.check('''
            Catalog:createToggleButton(PlayerSpellsFrame)
            combat=true
            click(PlayerSpellsFrame)
            assert(not UFO_Catalog:IsShown())
            Catalog:createToggleButton(MacroFrame)
            Catalog:createToggleButton(MacroFrame)
            assert(not tab(MacroFrame))
            Catalog:updateToggleButtons()
            combat=false
            fireEvent('PLAYER_REGEN_ENABLED')
            assertDocked(MacroFrame, false)
            assertDocked(PlayerSpellsFrame, false)
            local count=#frames
            fireEvent('PLAYER_REGEN_ENABLED')
            assert(#frames==count)
        ''')

    def test_open_command_cannot_open_blizzard_panels_during_combat(self):
        self.check('''
            PlayerSpellsUtil={ToggleSpellBookFrame=function() error('Opened protected panel') end}
            combat=true
            Catalog:open()
        ''')

    def test_settings_work_and_tab_hover_has_no_tooltip(self):
        self.check('''
            Catalog:createToggleButton(MacroFrame)
            click(MacroFrame, 'RightButton')
            assert(settingsOpened==1 and not UFO_Catalog:IsShown())
            tab(MacroFrame):RunScript('OnEnter')
            assert(not GameTooltip.shown and not GameTooltip:GetOwner())
            assert(tab(MacroFrame).Arrow.atlas=='UI-HUD-ActionBar-Flyout-Mouseover')
            tab(MacroFrame):RunScript('OnLeave')
            assert(not GameTooltip.shown)
            assert(tab(MacroFrame).Arrow.atlas=='UI-HUD-ActionBar-Flyout')
        ''')

    def test_force_open_and_host_onshow_keep_the_same_catalog(self):
        self.check('''
            CollectionsJournal:Hide()
            MacroFrame:Hide()
            ProfessionsBookFrame:Hide()
            Catalog:createToggleButton(PlayerSpellsFrame)
            Catalog:open()
            Catalog:open()
            assertDocked(PlayerSpellsFrame, true)
            assert(UFO_Catalog:IsShown())
        ''')

    def test_legacy_spellbook_tabs_keep_their_clearance(self):
        self.check('''
            SpellBookFrame=CreateFrame('Frame', 'SpellBookFrame')
            Catalog:createToggleButton(SpellBookFrame)
            assert(tab(SpellBookFrame).points[1][4]==35-3)
            click(SpellBookFrame)
            assert(UFO_Catalog.points[1][4]==35)
            assert(SpellBookFrame.widthAttribute==800+35+150+14)
            assertDocked(SpellBookFrame, true)
        ''')


if __name__ == "__main__":
    unittest.main()
