"""Run with Python and lupa (Lua 5.1). No WoW client required for these mocks."""
from pathlib import Path
import sys
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
# Reuse the workspace's existing test dependency when available.
sys.path.insert(0, str(ROOT.parent / "ContextLayouts" / ".test-deps"))
from lupa.lua51 import LuaRuntime

MOCK = r'''
Ufo = { Wormhole = function() end }
local log = setmetatable({}, {__index = function(self) return function() return self end end})
zebug = setmetatable({}, {__index = function() return log end})
Zebug = {new = function() return zebug end}
UfoMixIn = {mixInto = function(_, target)
    target.installMyToString = function() end
end}
Pacifier = {wrap = function(_, fn) return fn end}
L10N = {JEWELCRAFTING='jc', BLACKSMITHING='bs', LEATHERWORKING='lw', ENGINEERING='eng'}
INSCRIPTION, UNKNOWN, DEFAULT_ICON_FULL = 'inscription', 'Unknown', 134400
C_Spell = {PickupSpell=function() end, GetSpellInfo=function() return {name='Spell'} end,
           GetSpellTexture=function(id) return id+1000 end}
C_Item, C_PetJournal, C_TransmogOutfitInfo = {}, {}, {}
UfoProxy = {isButtonOnCursor=function() return false end}
Enum = {SpellBookSpellBank={Player=0}, SpellBookItemType={Flyout=3}}
known, slots = true, 2
function GetFlyoutInfo(id)
    assert(id == 42, 'flyout ID must remain distinct from a spell ID')
    return 'Test flyout', 'Choose an ability', slots, known
end
function GetFlyoutSlotInfo(id, slot)
    assert(id == 42)
    return 100+slot, slot == 1 and 201 or 0, slot <= 2
end
cursor = {'flyout', 42}
function GetCursorInfo() return unpack(cursor) end
C_SpellBook = {
    GetNumSpellBookSkillLines=function() return 1 end,
    GetSpellBookSkillLineInfo=function() return {itemIndexOffset=10,numSpellBookItems=2} end,
    GetSpellBookItemType=function(slot) return 3, slot == 12 and 42 or 99 end,
    GetSpellBookItemTexture=function(slot, bank)
        assert(slot == 12 and bank == 0, 'Texture lookup needs a spellbook slot, not a flyout ID')
        return 987
    end,
    PickupSpellBookItem=function(slot, bank)
        assert(slot == 12 and bank == 0)
        pickedSlot = slot
        cursor = {'flyout',42}
    end,
}
GameTooltip = {
    SetText=function(_, text) tooltipName=text end,
    AddLine=function(_, text) tooltipDescription=text end,
    Show=function() end,
}
callbacks = {}
EventRegistry = {
    RegisterCallback=function(_, event, callback, owner) callbacks[owner]=callback end,
    UnregisterCallback=function(_, event, owner) callbacks[owner]=nil end,
}
SpellFlyout = {shown=false}
function SpellFlyout:IsAttachedToButton(button) return self.flyoutButton == button end
function SpellFlyout:AttachToButton(button) self.flyoutButton=button; self.shown=true end
function SpellFlyout:DetatchFromButton()
    assert(self.flyoutButton)
    self.shown=false
    -- Blizzard broadcasts Hidden synchronously during Hide.
    for _, callback in pairs(callbacks) do callback() end
    self.flyoutButton=nil
end
function launcher()
    return {popup={ufo=true}, OnPopupToggled=function(self) self.toggled=(self.toggled or 0)+1 end}
end
-- Access to Blizzard's shared menu or an insecure cast must fail these tests.
SpellFlyout = setmetatable({}, {__index=function() error('Do not use Blizzard SpellFlyout') end})
function CastSpellByID() error('No casts from addon Lua') end
combat=false
function InCombatLockdown() return combat end
function CreateColor(r,g,b,a) return {r=r,g=g,b=b,a=a} end
function toggleAura(id)
    return {spellId=id,icon=7549236,duration=0,expirationTime=0,
            sourceUnit='player',isHelpful=true,isHarmful=false,canApplyAura=true}
end
numberKeys=true
Config={get=function(_,key) assert(key=='doKeybindTheButtonsOnTheFlyout'); return numberKeys end}
frames={}
local Frame={}
function Frame:SetAttribute(k,v) self.attrs[k]=v end
function Frame:GetAttribute(k) return self.attrs[k] end
function Frame:SetFrameRef(k,v) self.refs[k]=v end
function Frame:GetFrameRef(k) return self.refs[k] end
function Frame:GetName() return self.name end
function Frame:GetParent() return self.parent end
function Frame:Show()
    if self.shown then return end
    self.shown=true
    if self.wraps.OnShow then runSnippet(self.wraps.OnShow,self) end
end
function Frame:Hide()
    if not self.shown then return end
    self.shown=false
    if self.attrs._onhide then runSnippet(self.attrs._onhide,self) end
    if self.wraps.OnHide then runSnippet(self.wraps.OnHide,self) end
end
function Frame:IsShown() return self.shown end
function Frame:SetScript(k,fn)
    assert(k~='OnClick' and k~='PreClick' and k~='PostClick', 'Do not replace secure click scripts')
    self.scripts[k]=fn
end
function Frame:SetSize(w,h) self.width=w; self.height=h end
function Frame:SetWidth(w) self.width=w end
function Frame:SetHeight(h) self.height=h end
function Frame:ClearAllPoints() end
function Frame:SetPoint(...) self.point={...} end
function Frame:SetFrameStrata() end
function Frame:RegisterForClicks(...) self.clicks={...} end
function Frame:SetHighlightTexture() end
function Frame:SetBindingClick(priority,key,target,button)
    local name=type(target)=='table' and target:GetName() or target
    self.binding={priority,key,name,button}
    self.bindings[key:upper()]=self.binding
end
function Frame:ClearBindings() self.binding=nil; self.bindings={} end
function Frame:CreateFontString()
    return {SetPoint=function() end, SetJustifyH=function() end,
            SetText=function(self,text) self.text=text end}
end
function Frame:CreateTexture()
    return {SetAllPoints=function() end,SetColorTexture=function() end,SetPoint=function() end,
            SetBlendMode=function() end,SetVertexColor=function() end,SetAlpha=function() end,
            SetGradient=function() end,
            SetTexCoord=function() end,SetSize=function() end,
            SetWidth=function() end,SetHeight=function() end,
            SetShown=function(self,shown) self.shown=shown end,
            Show=function(self) self.shown=true end,Hide=function(self) self.shown=false end,
            SetTexture=function(self,id) self.texture=id end}
end
function CreateFrame(kind,name,parent,template)
    local frame=setmetatable({name=name,parent=parent,template=template,attrs={},refs={},wraps={},scripts={},
                             bindings={},shown=true}, {__index=Frame})
    frames[#frames+1]=frame
    return frame
end
function SecureHandlerSetFrameRef(frame,key,value) frame:SetFrameRef(key,value) end
function SecureHandlerWrapScript(frame,event,owner,script)
    local previous=frame.wraps[event]
    frame.wraps[event]=previous and (previous .. '\n' .. script) or script
end
function runSnippet(script,frame,isDown)
    local fn=assert(loadstring(script))
    setfenv(fn,setmetatable({self=frame,down=isDown,button='LeftButton'},{__index=_G}))
    fn()
end
function makeLaunchers()
    local owner=CreateFrame('Button','TestOwner')
    owner:SetAttribute('doKeybindTheButtonsOnTheFlyout',numberKeys)
    owner.getDirection=function() return 'UP' end
    local parent=CreateFrame('Frame','TestUfoMenu',owner)
    parent.getParent=function() return owner end
    parent.buttons={}
    for i=1,10 do parent.buttons[i]=CreateFrame('Button','TestParentButton'..i,parent) end
    parent.getButtonFrame=function(self,i) return self.buttons[i] end
    parent:SetAttribute('IN_USE_BTN_COUNT',2)
    owner.flyoutMenu=parent
    local b=CreateFrame('Button','TestNested',parent)
    b.ufoType=ButtonOnFlyoutMenu.ufoType
    b.btnDef=ButtonDef:new(42,'flyout')
    b.getDef=function(self) return self.btnDef end
    b.getFlyoutMenu=function() return parent end
    b.GetPopupDirection=function() return 'RIGHT' end
    b.getMouseBtnNumber=Button_Mixin.getMouseBtnNumber
    b.adjustSecureKeyToMatchTheMouseClick=Button_Mixin.adjustSecureKeyToMatchTheMouseClick
    parent.buttons[2]=b
    return b,owner,parent
end
function dispatchNumber(key,isDown,useOnKeyDown)
    local binding
    for _,frame in ipairs(frames) do
        if frame:IsShown() and frame.bindings[key] then
            assert(not binding,'Two menu layers must not own the same key')
            binding=frame.bindings[key]
        end
    end
    assert(binding,'No number key target')
    local target
    for _,frame in ipairs(frames) do if frame.name==binding[3] then target=frame end end
    assert(target)
    if isDown==useOnKeyDown then
        local action=target:GetAttribute('type')
        if action=='spell' then castSpell=target:GetAttribute('spell')
        elseif action then runSnippet(target:GetAttribute('_'..action),target,isDown) end
    end
    if target.wraps.PostClick then runSnippet(target.wraps.PostClick,target,isDown) end
end
MouseClick={ANY='AnyButton'}
MouseClickAsSecEnvId={AnyButton='type'}
function time() return 1 end
Mark={FIRE='fire',INFO='info'}
Xedni={getFlyoutDef=function() return 1 end}
'''


class NativeFlyouts(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute(MOCK)
        for filename in ("SpellIcons.lua", "ButtonDef.lua", "NativeFlyout.lua", "ui/Button_Mixin.lua",
                         "ui/ButtonOnFlyoutMenu.lua", "FlyoutDef.lua", "ui/FlyoutMenu.lua"):
            self.lua.execute((ROOT / filename).read_text(encoding="utf-8"), "UFO", self.lua.globals().Ufo)

    def check(self, code):
        self.lua.execute(code)

    def test_cursor_metadata_and_secure_action(self):
        self.check('''
            local d=ButtonDef:getFromCursor()
            assert(d.type=='flyout' and d.flyoutId==42 and d.spellId==nil)
            assert(d:getName()=='Test flyout' and d:getIcon()==987 and d:isUsable())
            local kind, key, value=d:asSecureClickHandlerAttributes()
            assert(kind=='UFO_NATIVE_42' and key=='_UFO_NATIVE_42' and type(value)=='string')
            d:getToolTipSetter()()
            assert(tooltipName=='Test flyout' and tooltipDescription=='Choose an ability')
        ''')

    def test_flyout_tooltip_layout_includes_description_and_clears_old_lines(self):
        self.check('''
            GameTooltip={
                SetText=function(self,text)
                    self.lines={text}
                    self.wordWrap=nil
                    self:Show()
                end,
                AddLine=function(self,text,r,g,b,wrap)
                    self.lines[#self.lines+1]=text
                    self.wordWrap=wrap
                end,
                Show=function(self) self.sizedLines={unpack(self.lines)} end,
            }
            local description="Maximize your Warband's collaborative potential with these abilities."
            for _,case in ipairs({{description=description},{description=''},{}}) do
                GetFlyoutInfo=function() return 'Warbands',case.description,2,true end
                ButtonDef:new(42,'flyout'):getToolTipSetter()()
                assert(GameTooltip.sizedLines[1]=='Warbands')
                if case.description and case.description~='' then
                    assert(#GameTooltip.sizedLines==2)
                    assert(GameTooltip.sizedLines[2]==description and GameTooltip.wordWrap)
                else
                    assert(#GameTooltip.sizedLines==1)
                end
            end
        ''')

    def test_unlearned_or_empty_flyout_is_filtered(self):
        self.check('''
            local d=ButtonDef:new(42, 'flyout')
            known=false; assert(not d:isUsable())
            known=true; slots=0; assert(not d:isUsable())
        ''')

    def test_flyout_icon_renders_through_menu_without_bad_data_warning(self):
        self.check('''
            assert(GetFlyoutTexture==nil)
            local d=ButtonDef:new(42,'flyout')
            local icon,err=FlyoutMenu.getIcon({},d)
            assert(icon==987 and err==nil)
            local flyout=FlyoutDef:oneOfUs({btns={d}})
            assert(flyout:getIcon()==987)
        ''')

    def test_missing_spellbook_entry_uses_child_spell_icon(self):
        self.check('''
            C_SpellBook.GetNumSpellBookSkillLines=function() return 0 end
            local d=ButtonDef:new(42,'flyout')
            assert(d:getIcon()==1201)
        ''')

    def test_missing_spellbook_texture_uses_child_spell_icon(self):
        self.check('''
            C_SpellBook.GetSpellBookItemTexture=function() return nil end
            assert(ButtonDef:new(42,'flyout'):getIcon()==1201)
        ''')

    def test_unavailable_flyout_keeps_previous_icon(self):
        self.check('''
            local d=ButtonDef:new(42,'flyout')
            assert(d:getIcon()==987)
            C_SpellBook.GetNumSpellBookSkillLines=function() return 0 end
            slots=0
            assert(d:getIcon()==987)
            assert(ButtonDef:new(42,'flyout'):getIcon()==DEFAULT_ICON_FULL)
        ''')

    def test_conditional_spell_texture_changes_without_changing_saved_spell(self):
        self.check('''
            local def=ButtonDef:new(1250491,'spell')
            local active=false
            C_Spell.GetSpellTexture=function(id)
                assert(id==1250491)
                return 100,100,active and 200 or nil
            end
            assert(def:getIcon()==100)
            active=true
            assert(def:getIcon()==200)
            active=false
            assert(def:getIcon()==100 and def.spellId==1250491)
        ''')

    def test_spell_icon_does_not_depend_on_native_action_bar_copy(self):
        self.check('''
            C_Spell.GetSpellTexture=function() return 7549236,7549236 end
            C_ActionBar={FindSpellActionButtons=function() error('No action bar dependency') end}
            C_SpellBook.FindSpellBookSlotForSpell=function() error('No icon lookup dependency') end
            local def=ButtonDef:new(1250491,'spell')
            assert(def:getIcon()==7549236)
        ''')

    def test_active_effects_get_generic_indicator_without_changing_spell_icons(self):
        self.check('''
            local active=false
            C_Spell.GetSpellTexture=function() return 7549236,7549236 end
            C_UnitAuras={GetPlayerAuraBySpellID=function(id) return active and toggleAura(id) or nil end}
            for _,id in ipairs({123,456,1250491}) do
                local b=CreateFrame('Button','ActiveTest'..id)
                SpellIcons:initializeIndicator(b)
                for _,state in ipairs({false,true,false}) do
                    active=state
                    SpellIcons:updateIndicator(b,id)
                    for _,edge in ipairs(b.ufoActiveBorder) do assert(edge.shown==state) end
                    assert(SpellIcons:getTexture(id)==7549236)
                end
            end
        ''')

    def test_high_value_beasts_refresh_updates_border_in_combat_without_reconfiguring(self):
        self.check('''
            local active=false
            C_Spell.GetSpellTexture=function() return 7549236,7549236 end
            local def=ButtonDef:new(1250491,'spell')
            local button=CreateFrame('Button','StateTest')
            button.getDef=function() return def end
            button.setIcon=function(self,icon) self.texture=icon end
            SpellIcons:initializeIndicator(button)
            C_UnitAuras={GetPlayerAuraBySpellID=function(id) return active and toggleAura(id) or nil end}
            Ufo.hasShitCalmedTheFuckDown=true
            GermCommander={forEachActiveGerm=function() end}
            Catalog={flyoutMenu={forEachButton=function(_,fn) fn(button) end}}
            combat=true
            button.CreateTexture=function() error('Do not create textures during refresh') end
            button.SetAttribute=function() error('Do not change actions during refresh') end
            button.SetBindingClick=function() error('Do not change bindings during refresh') end
            for _,state in ipairs({false,true,false}) do
                active=state
                SpellIcons:refresh('UNIT_AURA')
                assert(button.texture==7549236)
                for _,edge in ipairs(button.ufoActiveBorder) do assert(edge.shown==state) end
            end
        ''')

    def test_unavailable_state_clears_previously_active_indicator(self):
        self.check('''
            local b=CreateFrame('Button','RestrictedState')
            SpellIcons:initializeIndicator(b)
            C_UnitAuras={GetPlayerAuraBySpellID=function(id) return toggleAura(id) end}
            SpellIcons:updateIndicator(b,123)
            assert(b.ufoActiveBorder[1].shown)
            C_UnitAuras.GetPlayerAuraBySpellID=function() error('Restricted') end
            assert(SpellIcons:getActiveState(123)==nil)
            SpellIcons:updateIndicator(b,123)
            assert(not b.ufoActiveBorder[1].shown)
        ''')

    def test_minimap_tracking_state_does_not_need_an_aura(self):
        self.check('''
            local active=false
            C_Minimap={GetNumTrackingTypes=function() return 2 end,
                GetTrackingInfo=function(i) return {spellID=100+i,active=active} end}
            C_Spell.GetSpellTexture=function() return 100 end
            for _,id in ipairs({101,102}) do
                active=false; assert(SpellIcons:getActiveState(id)==false)
                active=true; assert(SpellIcons:getActiveState(id)==true)
                assert(SpellIcons:getTexture(id)==100)
            end
            assert(SpellIcons:getActiveState(999)==nil)
        ''')

    def test_timed_self_buff_is_active_without_being_classified_as_a_toggle(self):
        self.check('''
            C_UnitAuras={GetPlayerAuraBySpellID=function(id)
                local aura=toggleAura(id); aura.duration=60; aura.expirationTime=120; return aura
            end}
            assert(SpellIcons:getActiveState(123)==true)
        ''')

    def test_external_harmful_and_mismatched_auras_are_not_marked_active(self):
        self.check('''
            for field,value in pairs({sourceUnit='party1',isHelpful=false,isHarmful=true,spellId=999}) do
                C_UnitAuras={GetPlayerAuraBySpellID=function(id)
                    local aura=toggleAura(id); aura[field]=value; return aura
                end}
                assert(SpellIcons:getActiveState(123)==nil,field)
            end
        ''')

    def test_known_passive_effect_is_not_marked_active(self):
        self.check('''
            C_UnitAuras={GetPlayerAuraBySpellID=function(id) return toggleAura(id) end}
            C_SpellBook.FindSpellBookSlotForSpell=function() return 12,0 end
            C_SpellBook.GetSpellBookItemInfo=function() return {isPassive=true} end
            assert(SpellIcons:getActiveState(123)==nil)
        ''')

    def test_restricted_aura_fields_are_not_used_for_active_state(self):
        self.check('''
            local private={}
            issecretvalue=function(value) return value==private end
            C_UnitAuras={GetPlayerAuraBySpellID=function(id)
                local aura=toggleAura(id); aura.sourceUnit=private; return aura
            end}
            assert(SpellIcons:getActiveState(123)==nil)
        ''')

    def test_restricted_duration_is_unnecessary_to_identify_active_effect(self):
        self.check('''
            local private={}
            issecretvalue=function(value) return value==private end
            C_UnitAuras={GetPlayerAuraBySpellID=function(id)
                local aura=toggleAura(id); aura.duration=private; return aura
            end}
            assert(SpellIcons:getActiveState(123)==true)
        ''')

    def test_current_spell_action_marks_active_without_an_aura(self):
        self.check('''
            C_Spell.IsCurrentSpell=function(id) return id==123 end
            assert(SpellIcons:getActiveState(123)==true)
            assert(SpellIcons:getActiveState(456)==nil)
        ''')

    def test_native_submenu_active_border_preserves_icon_action_and_number_keys(self):
        self.check('''
            local b=makeLaunchers()
            NativeFlyout:prepare(b,b.btnDef)
            local menu=b:GetFrameRef('UFO_NATIVE_42')
            runSnippet(b:GetAttribute('_UFO_NATIVE_42'),b)
            local child=menu.children[1]
            local texture=child.icon.texture
            local bindings=menu.bindings
            C_UnitAuras={GetPlayerAuraBySpellID=function(id)
                if id==201 then return toggleAura(id) end
            end}
            Ufo.hasShitCalmedTheFuckDown=true
            GermCommander={forEachActiveGerm=function() end}
            Catalog={}
            combat=true
            child.SetAttribute=function() error('Do not change spell action') end
            menu.SetBindingClick=function() error('Do not change number bindings') end
            SpellIcons:refresh('UNIT_AURA')
            assert(child.ufoActiveBorder[1].shown)
            assert(not menu.children[2].ufoActiveBorder[1].shown)
            assert(child.icon.texture==texture and child:GetAttribute('spell')==201)
            assert(menu.bindings==bindings and child.HotKey.text=='1')
            C_UnitAuras.GetPlayerAuraBySpellID=function() return nil end
            SpellIcons:refresh('UNIT_AURA')
            assert(not child.ufoActiveBorder[1].shown)
        ''')

    def test_reused_empty_or_nonspell_button_clears_border(self):
        self.check('''
            local def=ButtonDef:new(123,'spell')
            local b=CreateFrame('Button','ReusedButton')
            b.getDef=function() return def end
            b.setIcon=function() end
            SpellIcons:initializeIndicator(b)
            C_UnitAuras={GetPlayerAuraBySpellID=function(id) return toggleAura(id) end}
            SpellIcons:refreshButton(b)
            assert(b.ufoActiveBorder[1].shown)
            def=nil
            SpellIcons:refreshButton(b)
            assert(not b.ufoActiveBorder[1].shown)
            def={type='item',itemId=1}
            SpellIcons:refreshButton(b)
            assert(not b.ufoActiveBorder[1].shown)
        ''')

    def test_custom_ufo_icon_is_preserved_with_active_border(self):
        self.check('''
            local b=CreateFrame('Button','CustomIcon')
            b.ufoType='Germ'
            b.getDef=function() return ButtonDef:new(123,'spell') end
            b.getIcon=function() return 999 end
            b.setIcon=function(self,icon) self.texture=icon end
            SpellIcons:initializeIndicator(b)
            C_UnitAuras={GetPlayerAuraBySpellID=function(id) return toggleAura(id) end}
            SpellIcons:refreshButton(b)
            assert(b.texture==999 and b.ufoActiveBorder[1].shown)
        ''')

    def test_only_spell_supplied_conditional_artwork_can_replace_base_icon(self):
        self.check('''
            C_Spell.GetSpellTexture=function() return 100,100,200 end
            C_ActionBar={FindSpellActionButtons=function() error('Do not mirror unrelated action appearance') end}
            C_UnitAuras={GetPlayerAuraBySpellID=function(id) return toggleAura(id) end}
            assert(SpellIcons:getTexture(123)==200)
        ''')

    def test_icon_refresh_is_deferred_and_coalesced(self):
        self.check('''
            local timers={}
            C_Timer={After=function(delay,callback) assert(delay==0); timers[#timers+1]=callback end}
            Ufo.hasShitCalmedTheFuckDown=true
            local refreshes=0
            SpellIcons.refresh=function() refreshes=refreshes+1 end
            SpellIcons:requestRefresh('UNIT_AURA')
            SpellIcons:requestRefresh('ACTIONBAR_UPDATE_STATE')
            assert(#timers==1 and refreshes==0)
            timers[1]()
            assert(refreshes==1)
            SpellIcons:requestRefresh('SPELL_UPDATE_ICON')
            assert(#timers==2)
        ''')

    def test_icon_refresh_updates_both_menus_and_keeps_custom_ufo_icon(self):
        self.check('''
            Ufo.hasShitCalmedTheFuckDown=true
            C_Spell.GetSpellTexture=function() return 100,100,200 end
            local def=ButtonDef:new(1250491,'spell')
            local function button(kind)
                return {ufoType=kind,getDef=function() return def end,
                    getIcon=function() return 999 end,
                    setIcon=function(self,icon) self.texture=icon end}
            end
            local ordinary=button('ButtonOnFlyoutMenu')
            local catalog=button('ButtonOnFlyoutMenu')
            local germ=button('Germ')
            germ.flyoutMenu={forEachButton=function(_,fn) fn(ordinary) end}
            GermCommander={forEachActiveGerm=function(_,fn) fn(germ) end}
            Catalog={flyoutMenu={forEachButton=function(_,fn) fn(catalog) end}}
            combat=true
            SpellIcons:refresh('SPELL_UPDATE_ICON')
            assert(ordinary.texture==200 and catalog.texture==200 and germ.texture==999)
        ''')

    def test_icon_refresh_updates_native_spell_without_rebinding_or_changing_action(self):
        self.check('''
            local b=makeLaunchers()
            NativeFlyout:prepare(b,b.btnDef)
            local menu=b:GetFrameRef('UFO_NATIVE_42')
            runSnippet(b:GetAttribute('_UFO_NATIVE_42'),b)
            local child=menu.children[1]
            local bindings=menu.bindings
            Ufo.hasShitCalmedTheFuckDown=true
            GermCommander={forEachActiveGerm=function() end}
            Catalog={}
            C_Spell.GetSpellTexture=function() return 100,100,200 end
            combat=true
            child.SetAttribute=function() error('Icon refresh must not change protected attributes') end
            menu.SetBindingClick=function() error('Icon refresh must not rebind keys') end
            SpellIcons:refresh('MINIMAP_UPDATE_TRACKING')
            assert(child.icon.texture==200 and child:GetAttribute('spell')==201)
            assert(menu:IsShown() and menu.bindings==bindings)
        ''')

    def test_icon_refresh_waits_for_addon_initialization(self):
        self.check('''
            assert(not Ufo.hasShitCalmedTheFuckDown)
            -- GermCommander and Catalog are intentionally not initialized.
            SpellIcons:refresh('SPELL_UPDATE_ICON')
        ''')

    def test_drag_back_uses_current_spellbook_slot(self):
        self.check('''
            local d=ButtonDef:new(42, 'flyout')
            assert(d:pickupToCursor())
            assert(pickedSlot==12 and Ufo.pickedUpBtn==d)
        ''')

    def test_missing_spellbook_entry_does_not_report_pickup_success(self):
        self.check('''
            C_SpellBook.GetNumSpellBookSkillLines=function() return 0 end
            local d=ButtonDef:new(42, 'flyout')
            assert(not d:pickupToCursor())
        ''')

    def test_popup_toggle_and_close_preserve_ufo_ownership(self):
        self.check('''
            local b,owner,parent=makeLaunchers()
            owner.popup=parent
            NativeFlyout:prepare(b,b.btnDef)
            local menu=b:GetFrameRef('UFO_NATIVE_42')
            runSnippet(b:GetAttribute('_UFO_NATIVE_42'),b)
            assert(menu:IsShown() and menu.binding and parent:IsShown())
            assert(menu.width==80 and menu.height==44)
            runSnippet(b:GetAttribute('_UFO_NATIVE_42'),b)
            assert(not menu:IsShown() and not menu.binding and owner.popup==parent)
        ''')

    def test_parent_hide_closes_nested_menu_and_clears_escape(self):
        self.check('''
            local b=makeLaunchers()
            NativeFlyout:prepare(b,b.btnDef)
            local menu=b:GetFrameRef('UFO_NATIVE_42')
            runSnippet(b:GetAttribute('_UFO_NATIVE_42'),b)
            b:getFlyoutMenu():Hide()
            assert(not menu:IsShown() and not menu.binding)
        ''')

    def test_primary_action_is_prepared_on_owner_before_combat(self):
        self.check('''
            local b,owner=makeLaunchers()
            NativeFlyout:prepare(b,b.btnDef)
            local action,key,script=b.btnDef:asSecureClickHandlerAttributes()
            assert(owner:GetAttribute(key)==script)
            assert(owner:GetFrameRef(action)==b:GetFrameRef(action))
            combat=true
            runSnippet(owner:GetAttribute(key),owner)
            local menu=owner:GetFrameRef(action)
            assert(menu:IsShown() and menu.width==44 and menu.height==80)
        ''')

    def test_children_cast_with_secure_spell_attributes_and_close_on_release(self):
        self.check('''
            local b,owner,parent=makeLaunchers()
            NativeFlyout:prepare(b,b.btnDef)
            local menu=b:GetFrameRef('UFO_NATIVE_42')
            local child=menu.children[1]
            assert(child.template=='SecureActionButtonTemplate')
            assert(child:GetAttribute('type')=='spell' and child:GetAttribute('spell')==201)
            assert(menu.children[2]:GetAttribute('spell')==102)
            assert(child.scripts.OnClick==nil)
            runSnippet(b:GetAttribute('_UFO_NATIVE_42'),b)
            combat=true
            -- Model the engine's secure cast, then its PostClick notification.
            runSnippet(child.wraps.PostClick,child,true)
            castSpell=child:GetAttribute('spell')
            runSnippet(child.wraps.PostClick,child,false)
            assert(castSpell==201 and not menu:IsShown() and not menu.binding)
            assert(parent:IsShown())
            owner:SetAttribute('doCloseOnClick',true)
            runSnippet(b:GetAttribute('_UFO_NATIVE_42'),b)
            runSnippet(child.wraps.PostClick,child,true)
            runSnippet(child.wraps.PostClick,child,false)
            assert(not parent:IsShown())
        ''')

    def test_refresh_reuses_frames_and_disables_removed_spells(self):
        self.check('''
            local b=makeLaunchers()
            NativeFlyout:prepare(b,b.btnDef)
            local menu=b:GetFrameRef('UFO_NATIVE_42')
            local child=menu.children[1]
            slots=1
            NativeFlyout:prepare(b,b.btnDef)
            assert(menu==b:GetFrameRef('UFO_NATIVE_42') and child==menu.children[1])
            assert(menu:GetAttribute('count')==1 and not menu.children[2]:IsShown())
            assert(menu.children[2]:GetAttribute('type')==nil)
        ''')

    def test_escape_closes_only_submenu(self):
        self.check('''
            local b,owner,parent=makeLaunchers()
            NativeFlyout:prepare(b,b.btnDef)
            local menu=b:GetFrameRef('UFO_NATIVE_42')
            runSnippet(b:GetAttribute('_UFO_NATIVE_42'),b)
            assert(menu.bindings.ESCAPE[3]==menu:GetName())
            runSnippet(menu:GetAttribute('_onclick'),menu,false)
            assert(not menu:IsShown() and not menu.binding and parent:IsShown())
        ''')

    def test_unlearned_slots_do_not_become_secure_actions(self):
        self.check('''
            local b=makeLaunchers()
            slots=3
            NativeFlyout:prepare(b,b.btnDef)
            local menu=b:GetFrameRef('UFO_NATIVE_42')
            assert(menu:GetAttribute('count')==2 and #menu.children==2)
        ''')

    def test_empty_menu_does_not_open_or_capture_escape(self):
        self.check('''
            local b=makeLaunchers()
            slots=0
            NativeFlyout:prepare(b,b.btnDef)
            local menu=b:GetFrameRef('UFO_NATIVE_42')
            runSnippet(b:GetAttribute('_UFO_NATIVE_42'),b)
            assert(not menu:IsShown() and not menu.binding)
        ''')

    def test_prepare_cannot_mutate_frames_in_combat(self):
        self.check('''
            local b=makeLaunchers()
            combat=true
            local ok=pcall(function() NativeFlyout:prepare(b,b.btnDef) end)
            assert(not ok and not b:GetFrameRef('UFO_NATIVE_42'))
        ''')

    def test_spell_press_does_not_hide_button_before_release(self):
        self.check('''
            local b=makeLaunchers()
            NativeFlyout:prepare(b,b.btnDef)
            local menu=b:GetFrameRef('UFO_NATIVE_42')
            runSnippet(b:GetAttribute('_UFO_NATIVE_42'),b)
            runSnippet(menu.children[1].wraps.PostClick,menu.children[1],true)
            assert(menu:IsShown())
        ''')

    def test_number_sequence_selects_child_for_both_key_activation_settings(self):
        for key_down in (True, False):
            with self.subTest(key_down=key_down):
                self.setUp()
                self.lua.globals().useOnKeyDown = key_down
                self.check('''
                    local b,owner,parent=makeLaunchers()
                    Button_Mixin.assignSecEnvMouseClickBehaviorVia_AttributeFromBtnDef(b,'AnyButton')
                    parent:SetBindingClick(true,'1',parent.buttons[1],'LeftButton')
                    parent:SetBindingClick(true,'2',b,'LeftButton')
                    dispatchNumber('2',true,useOnKeyDown)
                    dispatchNumber('2',false,useOnKeyDown)
                    local menu=b:GetFrameRef('UFO_NATIVE_42')
                    assert(menu:IsShown() and not castSpell)
                    assert(not next(parent.bindings))
                    assert(menu.children[1].HotKey.text=='1' and menu.children[2].HotKey.text=='2')
                    combat=true
                    dispatchNumber('1',true,useOnKeyDown)
                    dispatchNumber('1',false,useOnKeyDown)
                    assert(castSpell==201 and not menu:IsShown())
                    assert(parent.bindings['2'][3]==b:GetName() and not next(menu.bindings))
                ''')

    def test_parent_opener_closes_direct_native_action_before_number_dispatch(self):
        self.lua.execute((ROOT / "SecEnvDrugMule.lua").read_text(), "UFO", self.lua.globals().Ufo)
        self.check('''
            local b,owner,parent=makeLaunchers()
            parent:Hide()
            NativeFlyout:prepare(owner,b.btnDef)
            runSnippet(owner:GetAttribute('_UFO_NATIVE_42'),owner)
            local menu=owner:GetFrameRef('UFO_NATIVE_42')
            assert(menu:IsShown() and not parent:IsShown() and menu.bindings['1'])
            germ,flyoutMenu=owner,parent
            SecEnvAttribute={flyoutDirection='direction'}
            MouseClick.LEFT='LeftButton'
            owner:SetAttribute('direction','UP')
            DIRECTION_AS_ANCHOR={UP='TOP'}
            ANCHOR_OPPOSITE={TOP='BOTTOM'}
            UFO_DUM_DUM={GetAttribute=function() return 10 end}
            GLOBAL_BTNS=parent.buttons
            parent.SetParent=function(self,value) self.parent=value end
            parent.RunAttribute=function() end
            parent.buttons[1]:SetAttribute('type','spell')
            parent.buttons[1]:SetAttribute('spell',999)
            combat=true
            runSnippet(SecEnv:getSecEnvScriptFor_Opener(),parent,false)
            assert(parent:IsShown() and not menu:IsShown())
            assert(not next(menu.bindings) and parent.bindings['1'])
            dispatchNumber('1',true,true)
            dispatchNumber('1',false,true)
            assert(castSpell==999)
        ''')

    def test_owner_reset_closes_direct_native_action_with_parent_already_hidden(self):
        source = (ROOT / "Germ.lua").read_text()
        body = re.search(r'function Germ:closeFlyout\(\)(.*?)\nend', source, re.S).group(1)
        self.lua.execute('Germ={}\nfunction Germ:closeFlyout()' + body + '\nend')
        self.check('''
            local b,owner,parent=makeLaunchers()
            parent:Hide()
            NativeFlyout:prepare(owner,b.btnDef)
            runSnippet(owner:GetAttribute('_UFO_NATIVE_42'),owner)
            local menu=owner:GetFrameRef('UFO_NATIVE_42')
            assert(menu:IsShown() and menu.bindings['1'])
            ClearOverrideBindings=function(frame) frame:ClearBindings() end
            parent.close=FlyoutMenu.close
            Germ.closeFlyout(owner)
            assert(not parent:IsShown() and not menu:IsShown())
            assert(not next(menu.bindings) and not next(parent.bindings))
        ''')

    def test_owner_hide_closes_direct_native_action_and_does_not_revive_it(self):
        self.check('''
            local b,owner,parent=makeLaunchers()
            parent:Hide()
            NativeFlyout:prepare(owner,b.btnDef)
            runSnippet(owner:GetAttribute('_UFO_NATIVE_42'),owner)
            local menu=owner:GetFrameRef('UFO_NATIVE_42')
            assert(menu:IsShown() and menu.bindings['1'])
            combat=true
            owner:Hide()
            assert(not menu:IsShown() and not next(menu.bindings))
            owner:Show()
            assert(not menu:IsShown() and not next(parent.bindings))
        ''')

    def test_escape_restores_parent_numbers_alias_and_original_close_button(self):
        self.check('''
            local b,owner,parent=makeLaunchers()
            owner:SetAttribute('UFO_KEYBIND_1','F')
            parent:SetAttribute('UFO_OPEN_MOUSE_CLICK','Button7')
            NativeFlyout:prepare(b,b.btnDef)
            local menu=b:GetFrameRef('UFO_NATIVE_42')
            runSnippet(b:GetAttribute('_UFO_NATIVE_42'),b)
            assert(not next(parent.bindings))
            runSnippet(menu:GetAttribute('_onclick'),menu,false)
            assert(parent.bindings['1'][3]==parent.buttons[1]:GetName())
            assert(parent.bindings['2'][3]==b:GetName())
            assert(parent.bindings.F[3]==parent.buttons[1]:GetName())
            assert(parent.bindings.ESCAPE[3]==owner:GetName() and parent.bindings.ESCAPE[4]=='Button7')
            assert(not next(menu.bindings))
        ''')

    def test_parent_close_does_not_restore_any_number_overrides(self):
        self.check('''
            local b,owner,parent=makeLaunchers()
            NativeFlyout:prepare(b,b.btnDef)
            local menu=b:GetFrameRef('UFO_NATIVE_42')
            runSnippet(b:GetAttribute('_UFO_NATIVE_42'),b)
            parent:Hide()
            assert(not next(parent.bindings) and not next(menu.bindings))
        ''')

    def test_tenth_child_uses_zero_and_extra_children_have_no_number(self):
        self.check('''
            slots=11
            GetFlyoutSlotInfo=function(_,slot) return 100+slot,0,true end
            local b=makeLaunchers()
            NativeFlyout:prepare(b,b.btnDef)
            local menu=b:GetFrameRef('UFO_NATIVE_42')
            runSnippet(b:GetAttribute('_UFO_NATIVE_42'),b)
            assert(menu.bindings['0'][3]==menu.children[10]:GetName())
            assert(menu.children[10].HotKey.text=='0' and menu.children[11].HotKey.text=='')
            assert(not menu.bindings['10'] and not menu.bindings['11'])
        ''')

    def test_disabling_number_key_option_disables_submenu_numbers_and_labels(self):
        self.check('''
            numberKeys=false
            local b,owner,parent=makeLaunchers()
            NativeFlyout:prepare(b,b.btnDef)
            local menu=b:GetFrameRef('UFO_NATIVE_42')
            runSnippet(b:GetAttribute('_UFO_NATIVE_42'),b)
            assert(not menu.bindings['1'] and not menu.bindings['2'] and menu.bindings.ESCAPE)
            assert(menu.children[1].HotKey.text=='')
            runSnippet(menu:GetAttribute('_onclick'),menu,false)
            assert(not parent.bindings['1'] and parent.bindings.ESCAPE)
        ''')

    def test_close_on_click_clears_both_binding_layers(self):
        self.check('''
            local b,owner,parent=makeLaunchers()
            owner:SetAttribute('doCloseOnClick',true)
            NativeFlyout:prepare(b,b.btnDef)
            local menu=b:GetFrameRef('UFO_NATIVE_42')
            runSnippet(b:GetAttribute('_UFO_NATIVE_42'),b)
            local child=menu.children[1]
            runSnippet(child.wraps.PostClick,child,true)
            runSnippet(child.wraps.PostClick,child,false)
            assert(not parent:IsShown() and not menu:IsShown())
            assert(not next(parent.bindings) and not next(menu.bindings))
        ''')

    def test_nested_popup_direction(self):
        self.check('''
            for _, direction in ipairs({'UP','DOWN','LEFT','RIGHT'}) do
                local b=setmetatable({btnDef={type='flyout'}, GetParent=function()
                    return {getDirection=function() return direction end}
                end}, {__index=ButtonOnFlyoutMenu})
                local result=b:GetPopupDirection()
                assert(result==((direction=='UP' or direction=='DOWN') and 'RIGHT' or 'UP'))
            end
        ''')

    def test_arrow_direction_before_parent_initialization(self):
        self.check('assert(ButtonOnFlyoutMenu.GetPopupDirection({})=="UP")')

    def test_arrow_state_without_public_get_frame_ref(self):
        self.check('''
            -- WoW exposes GetFrameRef only to restricted snippets. Arrow
            -- updates run before prepare too, while loading saved flyouts.
            local button={btnDef={type='flyout',flyoutId=235}, GetFrameRef=false}
            assert(not NativeFlyout:isOpen(button))
            button.ufoNativeFlyoutId=235
            button.ufoNativeFlyoutMenu={IsShown=function() return true end}
            assert(NativeFlyout:isOpen(button))
            button.btnDef.flyoutId=42
            assert(not NativeFlyout:isOpen(button))
            button.btnDef=nil
            assert(not NativeFlyout:isOpen(button))
        ''')

    def test_catalog_set_def_updates_arrow_without_launcher_parent(self):
        self.check('''
            -- Reproduce the catalog panel parent in the reported stack.
            local panel={}
            local menu=setmetatable({isForCatalog=true, getParent=function() return panel end},
                                    {__index=FlyoutMenu})
            local button=setmetatable({
                GetParent=function() return menu end,
                UpdateArrowShown=function() end,
                UpdateArrowPosition=function(self) arrowDirection=self:GetPopupDirection() end,
                UpdateArrowRotation=function(self) assert(self:GetPopupDirection()=='UP') end,
                setExcluderVisibility=function() end,
            }, {__index=ButtonOnFlyoutMenu})
            for _, kind in ipairs({'spell','flyout'}) do
                button:setDef({type=kind})
                assert(arrowDirection=='UP' and menu:getDirection()=='RIGHT')
            end
            button:setDef(nil)
            assert(arrowDirection=='UP')
        ''')

    def test_catalog_direction_before_parent_is_available(self):
        self.check('''
            local menu=setmetatable({isForCatalog=true,
                getParent=function() error('catalog must not consult its parent') end},
                {__index=FlyoutMenu})
            assert(menu:getDirection()=='RIGHT')
        ''')

    def test_action_bar_menu_reads_current_launcher_direction(self):
        self.check('''
            local direction='LEFT'
            local menu=setmetatable({getParent=function()
                return {getDirection=function() return direction end}
            end}, {__index=FlyoutMenu})
            assert(menu:getDirection()=='LEFT')
            direction='DOWN'
            assert(menu:getDirection()=='DOWN')
        ''')

    def test_cooldown_does_not_pass_flyout_id_to_item_api(self):
        self.check('''
            local b={getDef=function() return ButtonDef:new(42,'flyout') end,
                     cooldown={Clear=function() cleared=true end}}
            Button_Mixin.updateCooldown(b)
            assert(cleared)
        ''')

    def test_spell_refresh_includes_native_flyouts(self):
        self.check('''
            local d=FlyoutDef:oneOfUs({btns={ButtonDef:new(42,'flyout')}})
            assert(d:hasSpell())
        ''')

    def test_lua_syntax(self):
        for path in ROOT.rglob("*.lua"):
            if "reference" not in path.parts:
                with self.subTest(path=path.relative_to(ROOT)):
                    self.lua.execute('assert(loadstring(...))', path.read_text(encoding="utf-8-sig"))

    def test_nested_launch_keeps_parent_open_but_spell_closes_it(self):
        source = (ROOT / "ui/FlyoutMenu.lua").read_text(encoding="utf-8")
        script = re.search(r'local CLOSE_FLYOUT_WHEN_BTN_IS_CLICKED_SEC_ENV_SCRIPT = \[=\[(.*?)\]=\]', source, re.S).group(1)
        run = self.lua.eval('function(script) return assert(loadstring(script)) end')(script)
        self.check('''
            down=false
            flyoutMenu={Hide=function() hidden=true end, SetAttribute=function() end,
                        ClearBindings=function() bindingsCleared=true end,
                        GetAttribute=function() return true end}
            germ={GetAttribute=function() return true end}
            self={GetID=function() return 1 end,
                  GetAttribute=function() return actionType end,
                  GetFrameRef=function() return germ end}
            actionType='UFO_NATIVE_42'
        ''')
        run()
        self.check("assert(not hidden and not bindingsCleared); actionType='spell'")
        run()
        self.check('assert(hidden and bindingsCleared)')

    def test_secure_attributes_keep_flyout_id_out_of_spell_metadata(self):
        self.check('''
            local b,owner=makeLaunchers()
            Button_Mixin.assignSecEnvMouseClickBehaviorVia_AttributeFromBtnDef(b,'AnyButton')
            assert(b.attrs.type=='UFO_NATIVE_42' and b.attrs.spell==nil)
            assert(b.attrs.SEC_ENV_ACTION_TYPE_DUMBER=='_UFO_NATIVE_42')
            assert(type(b.attrs.SEC_ENV_ACTION_ARG)=='string')
            assert(type(owner:GetAttribute('_UFO_NATIVE_42'))=='string')
            ButtonOnFlyoutMenu.copyDefToBlizFields(b)
            assert(b.spellID==nil and b.actionType=='flyout')
        ''')


if __name__ == "__main__":
    unittest.main()
