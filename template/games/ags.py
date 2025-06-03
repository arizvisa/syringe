'''
Adventure Game Studio v360.41
'''
import ptypes
from ptypes import *

class Int8(pint.uint8_t): pass
class Int16(pint.int16_t): pass
class Int32(pint.int32_t): pass
class Float(pfloat.single): pass
class Bool(pint.enum, Int8):
    _values_ = [
        ('TRUE', 1),
        ('FALSE', 0),
    ]

class RGB(pstruct.type):
    _fields_ = [
        (pint.uint8_t, 'r'),
        (pint.uint8_t, 'g'),
        (pint.uint8_t, 'b'),
        (pint.uint8_t, 'a'),
    ]
    def summary(self):
        r,g,b,a = (self[fld].li for fld in 'rgba')
        res = a.int()
        for x in [r,g,b]:
            res*= 0x100
            res+= x.int()
        return "(ARGB) {:#0{:d}x}".format(res, 2 + 8)

class StringK(pstr.string):
    def alloc(self, *args, **kwargs):
        if args:
            return super(Signature, self).alloc(*args, **kwargs)
        elif getattr(self, '_value_', None) is None:
            return super(Signature, self).alloc(*args, **kwargs)
        kwargs.setdefault('length', len(self._value_))
        return super(Signature, self).alloc(self._value_, **kwargs)

class Tag(StringK):
    def __init__(self, *args, **kwargs):
        if hasattr(self, '_value_') and not getattr(self, 'length', 0):
            value = "<{:s}>".format(self._value_)
            self.length = len(value)
        super(Tag, self).__init__(*args, **kwargs)

    def alloc(self, *args, **kwargs):
        if args:
            return super(Signature, self).alloc(*args, **kwargs)
        elif getattr(self, '_value_', None) is None:
            return super(Signature, self).alloc(*args, **kwargs)
        value = "<{:s}>".format(self._value_)
        kwargs.setdefault('length', len(value))
        return super(Tag, self).alloc(value, **kwargs)

class StringPrefixed(pstruct.type):
    def __value(self):
        res = self['length'].li
        return dyn.clone(pstr.string, length=max(0, res.int()))
    _fields_ = [
        (Int32, 'length'),
        (__value, 'value'),
    ]
    def summary(self):
        length, res = (self[fld] for fld in ['length', 'value'])
        return "({:d}) {!r}".format(length.int(), res.str())

class Signature(StringK):
    _value_ = 'Adventure Game Studio saved game v2'
    length = len(_value_)

class Environment(pstruct.type):
    class _engine_name(StringK):
        _value_ = 'Adventure Game Studio run-time engine'
    class _engine_version(StringK):
        _value_ = ''
    class _game_guid(StringK):
        length = 40
    class _game_gamename(StringK):
        _value_ = ''
    class _ResPaths_GamePak(StringK):
        _value_ = ''

    _fields_ = [
        (StringPrefixed, 'engine_name'),
        (StringPrefixed, 'engine_version'),
        (StringPrefixed, 'game_guid'),
        (StringPrefixed, 'game_name'),
        (StringPrefixed, 'game_res'),
        (Int32, 'game_version'),
        (Int32, 'color_depth'),
        (Int32, 'uniqueid'),
        (ptype.block, 'unknown'),
    ]

class GameDataVersion(pint.enum):
    _values_ = [
        ('kGameVersion_Undefined', 0),
        ('kGameVersion_200', 5),
        ('kGameVersion_201', 6),
        ('kGameVersion_203', 7),
        ('kGameVersion_207', 9),
        ('kGameVersion_220', 11),
        ('kGameVersion_230', 12),
        ('kGameVersion_240', 12),
        ('kGameVersion_250', 18),
        ('kGameVersion_251', 19),
        ('kGameVersion_253', 20),
        ('kGameVersion_254', 21),
        ('kGameVersion_255', 22),
        ('kGameVersion_256', 24),
        ('kGameVersion_260', 25),
        ('kGameVersion_261', 26),
        ('kGameVersion_262', 27),
        ('kGameVersion_270', 31),
        ('kGameVersion_272', 32),
        ('kGameVersion_300', 35),
        ('kGameVersion_301', 36),
        ('kGameVersion_310', 37),
        ('kGameVersion_311', 39),
        ('kGameVersion_312', 40),
        ('kGameVersion_320', 41),
        ('kGameVersion_321', 42),
        ('kGameVersion_330', 43),
        ('kGameVersion_331', 44),
        ('kGameVersion_340_1', 45),
        ('kGameVersion_340_2', 46),
        ('kGameVersion_340_4', 47),
        ('kGameVersion_341', 48),
        ('kGameVersion_341_2', 49),
        ('kGameVersion_350', 50),
        ('kGameVersion_360', 3060000),
        ('kGameVersion_360_11', 3060011),
        ('kGameVersion_360_16', 3060016),
        ('kGameVersion_360_21', 3060021),
        ('kGameVersion_360_41', 3060041),
        ('kGameVersion_361', 3060100),
        ('kGameVersion_361_10', 3060110),
        ('kGameVersion_361_14', 3060114),
        ('kGameVersion_362', 3060200),
        ('kGameVersion_362_03', 3060203),
        ('kGameVersion_363', 3060300),
    ]

class Description(pstruct.type):
    class _version(GameDataVersion, Int32):
        pass

    def __env(self):
        res = self['size'].li
        return dyn.clone(Environment, _length_=res.int())
    def __padding(self):
        res, size = (self[fld].li for fld in ['env', 'size'])
        total = res.size() + size.size()
        return dyn.block(max(0, size.int() - total))

    _fields_ = [
        (_version, 'version'),
        (Int32, 'size'),
        (__env, 'env'),
        (__padding, 'padding'),
    ]

class SaveImageFlags(pbinary.flags):
    _fields_ = [
        (30, 'Unused'),
        (1, 'Deflate'),
        (1, 'Present'),
    ]

class Bitmap(pstruct.type):
    def __data(self):
        w, h, d = (self[fld].li for fld in ['Width', 'Height', 'ColorDepth'])
        count, extra = divmod(d.int(), 8)
        pixel = count + 1 if extra else count
        stride = w.int() * pixel
        return dyn.block(stride * h.int()) 

    _fields_ = [
        (Int32, 'Width'),
        (Int32, 'Height'),
        (Int32, 'ColorDepth'),
        (__data, 'data'),
    ]

class CompressedBitmap(pstruct.type):
    def __data(self):
        res = self['size'].li
        return dyn.block(max(0, res.int() - res.size()))
    _fields_ = [
        (Int32, 'Width'),
        (Int32, 'Height'),
        (Int32, 'ColorDepth'),
        (Int32, 'reserved'),
        (Int32, 'size'),
        (__data, 'data'),
    ]

class UserImage(pstruct.type):
    def __bitmap(self):
        res = self['flags'].li
        if not res['Present']:
            return ptype.block
        elif res['Deflate']:
            return CompressedBitmap
        return Bitmap
    _fields_ = [
        (SaveImageFlags, 'flags'),
        (__bitmap, 'bitmap'),
    ]

class UserDescription(pstruct.type):
    _fields_ = [
        (StringPrefixed, 'user_text'),
        (UserImage, 'user_image'),
    ]

class ComponentListTag(Tag):    _value_ = 'Components'
class GUIsTag(Tag):             _value_ = 'GUIs'
class GUIButtonsTag(Tag):       _value_ = 'GUIButtons'
class GUILabelsTag(Tag):        _value_ = 'GUILabels'
class GUIInvWindowsTag(Tag):    _value_ = 'GUIInvWindows'
class GUISlidersTag(Tag):       _value_ = 'GUISliders'
class GUITextBoxesTag(Tag):     _value_ = 'GUITextBoxes'
class GUIListBoxesTag(Tag):     _value_ = 'GUIListBoxes'
class AnimatedButtonsTag(Tag):  _value_ = 'AnimatedButtons'
class RoomStateTag(Tag):        _value_ = 'RoomState'

class ComponentTag(Tag):
    pass

class ComponentTagLoader(pstr.szstring):
    def isTerminator(self, value):
        return value.str() in '\0>'
    def alloc(self, *args, **kwargs):
        raise NotImplementedError
    def tagname(self):
        string = self.str()
        if {string[:2], string[-1:]} == {'</', '>'}:
            return string[+2 : -1]
        elif string[:1] + string[-1:] == '<>':
            return string[+1 : -1]
        return string

class ComponentTagOpen(ComponentTagLoader):
    def alloc(self, *args, **kwargs):
        if args:
            return super(Signature, self).alloc(*args, **kwargs)
        elif getattr(self, '_value_', None) is None:
            return super(Signature, self).alloc(*args, **kwargs)
        value = "<{:s}>".format(self._value_)
        kwargs.setdefault('length', len(value))
        return super(Tag, self).alloc(value, **kwargs)

class ComponentTagClose(ComponentTagLoader):
    def alloc(self, *args, **kwargs):
        if args:
            return super(Signature, self).alloc(*args, **kwargs)
        elif getattr(self, '_value_', None) is None:
            return super(Signature, self).alloc(*args, **kwargs)
        value = "</{:s}>".format(self._value_)
        kwargs.setdefault('length', len(value))
        return super(Tag, self).alloc(value, **kwargs)

#class Component(pstruct.type):
#    '''>= kSvgVersion_363'''
#    _fields_ = [
#        (ComponentTag, 'tag'),
#        (Int32, 'size'),
#        (Int32, 'flags'),
#        (Int32, 'version'),
#        (Int32, 'component_size'),
#        (Int32, 'uncompressed_size'),
#        (Int32, 'checksum'),
#    ]

class ComponentHandler(ptype.definition):
    attribute = '_tag_'
    cache = {}

class Component(pstruct.type):
    def __data(self):
        return getattr(self, '_object_', ptype.block)
    def __extra(self):
        res, fields = self['size'].li, ['data']
        total = sum(self[fld].li.size() for fld in fields)
        return dyn.block(max(0, res.int() - total))

    _fields_ = [
        (Int32, 'version'),
        (Int32, 'size'),
        (Int32, 'reserved'),
        (__data, 'data'),
        (__extra, 'extra'),
    ]

    def summary(self):
        res = []
        res.append("version={:#x}".format(self['version']))
        if self['reserved'].int():
            res.append("reserved={:#x}".format(self['reserved']))
        res.append(':')
        field = 'data' if self['data'].size() else 'extra'
        res.append(self[field].summary())
        return ' '.join(res)

class TaggedComponent(pstruct.type):
    def __component(self):
        open = self['tagOpen'].li
        string = open.str()
        if string.startswith('</'):
            return ptype.block
        elif not ComponentHandler.has(open.tagname()):
            return Component
        res = ComponentHandler.lookup(open.tagname())
        return dyn.clone(Component, _object_=res)

    def __tagClose(self):
        tag = self['tagOpen'].li.str()
        if tag.startswith('</'):
            return pstr.string
        return ComponentTagClose

    _fields_ = [
        (ComponentTagOpen, 'tagOpen'),
        (__component, 'component'),
        (__tagClose, 'tagClose'),
    ]

# Engine/game/savegame_components.cpp:1697-1865

#class GameStateComponent(ComponentTag):
#    _value_ = "Game State"
#class AudioComponent(ComponentTag):
#    _value_ = "Audio"
#class CharactersComponent(ComponentTag):
#    _value_ = "Characters"
#class DialogsComponent(ComponentTag):
#    _value_ = "Dialogs"
#class GUIComponent(ComponentTag):
#    _value_ = "GUI"
#class InventoryItemsComponent(ComponentTag):
#    _value_ = "Inventory Items"
#class MouseCursorsComponent(ComponentTag):
#    _value_ = "Mouse Cursors"
#class ViewsComponent(ComponentTag):
#    _value_ = "Views"
#class ViewsComponent2(ComponentTag):
#    _value_ = "Views"
#class DynamicSpritesComponent(ComponentTag):
#    _value_ = "Dynamic Sprites"
#class DynamicSpritesComponent2(ComponentTag):
#    _value_ = "Dynamic Sprites"
#class OverlaysComponent(ComponentTag):
#    _value_ = "Overlays"
#class DynamicSurfacesComponent(ComponentTag):
#    _value_ = "Dynamic Surfaces"
#class ScriptModulesComponent(ComponentTag):
#    _value_ = "Script Modules"
#class RoomStatesComponent(ComponentTag):
#    _value_ = "Room States"
#class LoadedRoomStateComponent(ComponentTag):
#    _value_ = "Loaded Room State"
#class MoveListsComponent(ComponentTag):
#    _value_ = "Move Lists"
#class ManagedPoolComponent(ComponentTag):
#    _value_ = "Managed Pool"
#class PluginDataComponent(ComponentTag):
#    _value_ = "Plugin Data"

class QueuedAudioItem(pstruct.type):
    _fields_ = [
        (Int16, 'audioClipIndex'),
        (Int16, 'priority'),
        (Bool, 'repeat'),
        (Int32, 'reserved'),
    ]

class DoOnce(pstruct.type):
    def __Tokens(self):
        res = self['Count'].li
        return dyn.array(StringPrefixed, max(0, res.int()))
    _fields_ = [
        (Int32, 'Count'),
        (__Tokens, 'Tokens'),
    ]

class GameSetupStruct(pstruct.type):
    OPT_HIGHESTOPTION_321 = 39
    OPT_LIPSYNCTEXT = 99
    _fields_ = [
        (dyn.array(Int32, OPT_HIGHESTOPTION_321 + 1), 'options'),
        (Int32, 'OPT_LIPSYNCTEXT'),
        (Int32, 'playercharacter'),
        (Int32, 'dialog_bullet'),
        (Int16, 'hotdot'),
        (Int16, 'hotdotouter'),
        (Int32, 'invhotdotsprite'),
        (Int32, 'default_lipsync_frame'),
    ]

class GamePlayState(pstruct.type):
    MAXGLOBALVARS = 50
    MAXGSVALUES = 500
    MAX_WALK_AREAS = 16
    MAX_PARSED_WORDS = 15
    MAX_TIMERS = 21
    LEGACY_MAXSAVEGAMES = 50
    MAX_QUEUED_MUSIC = 10
    PLAYMP3FILE_MAX_FILENAME_LEN = 50
    MAXGLOBALSTRINGS = 51
    MAX_MAXSTRLEN = 200
    LEGACY_GAMESTATE_GAMENAMELENGTH = 100

    _fields_ = [
        (Int32, 'score'),
        (Int32, 'usedmode'),
        (Int32, 'disabled_user_interface'),
        (Int32, 'gscript_timer'),
        (Int32, 'debug_mode'),
        (dyn.array(Int32, MAXGLOBALVARS), 'globalvars'),
        (Int32, 'messagetime'),
        (Int32, 'usedinv'),
        (Int32, 'inv_top'),
        (Int32, 'inv_numdisp'),
        (Int32, 'inv_numorder'),
        (Int32, 'inv_numinline'),
        (Int32, 'text_speed'),
        (Int32, 'sierra_inv_color'),
        (Int32, 'talkanim_speed'),
        (Int32, 'inv_item_wid'),
        (Int32, 'inv_item_hit'),
        (Int32, 'speech_text_shadow'),
        (Int32, 'swap_portrait_side'),
        (Int32, 'speech_textwindow_gui'),
        (Int32, 'follow_change_room_timer'),
        (Int32, 'totalscore'),
        (Int32, 'skip_display'),
        (Int32, 'no_multiloop_repeat'),
        (Int32, 'roomscript_finished'),
        (Int32, 'used_inv_on'),
        (Int32, 'no_textbg_when_voice'),
        (Int32, 'max_dialogoption_width'),
        (Int32, 'no_hicolor_fadein'),
        (Int32, 'bgspeech_game_speed'),
        (Int32, 'bgspeech_stay_on_display'),
        (Int32, 'unfactor_speech_from_textlength'),
        (Int32, 'mp3_loop_before_end'),
        (Int32, 'speech_music_drop'),
        (Int32, 'in_cutscene'),
        (Int32, 'fast_forward'),
        (Int32, 'room_width'),
        (Int32, 'room_height'),
        (Int32, 'game_speed_modifier'),
        (Int32, 'score_sound'),
        (Int32, 'takeover_data'),
        (Int32, 'replay_hotkey_unused'),
        (Int32, 'dialog_options_pad_x'),
        (Int32, 'dialog_options_pad_y'),
        (Int32, 'narrator_speech'),
        (Int32, 'ambient_sounds_persist'),
        (Int32, 'lipsync_speed'),
        (Int32, 'close_mouth_speech_time'),
        (Int32, 'disable_antialiasing'),
        (Int32, 'text_speed_modifier'),
        (Int32, 'text_align'),
        (Int32, 'speech_bubble_width'),
        (Int32, 'min_dialogoption_width'),
        (Int32, 'disable_dialog_parser'),
        (Int32, 'anim_background_speed'),
        (Int32, 'top_bar_backcolor'),
        (Int32, 'top_bar_textcolor'),
        (Int32, 'top_bar_bordercolor'),
        (Int32, 'top_bar_borderwidth'),
        (Int32, 'top_bar_ypos'),
        (Int32, 'screenshot_width'),
        (Int32, 'screenshot_height'),
        (Int32, 'top_bar_font'),
        (Int32, 'speech_text_align'),
        (Int32, 'auto_use_walkto_points'),
        (Int32, 'inventory_greys_out'),
        (Int32, 'skip_speech_specific_key'),
        (Int32, 'abort_key'),
        (Int32, 'fade_to_red'),
        (Int32, 'fade_to_green'),
        (Int32, 'fade_to_blue'),
        (Int32, 'show_single_dialog_option'),
        (Int32, 'keep_screen_during_instant_transition'),
        (Int32, 'read_dialog_option_colour'),
        (Int32, 'stop_dialog_at_end'),
        (Int32, 'speech_portrait_placement'),
        (Int32, 'speech_portrait_x'),
        (Int32, 'speech_portrait_y'),
        (Int32, 'speech_display_post_time_ms'),
        (Int32, 'dialog_options_highlight_color'),
        (Int32, 'randseed'),
        (Int32, 'player_on_region'),
        (Int32, 'check_interaction_only'),
        (Int32, 'bg_frame'),
        (Int32, 'bg_anim_delay'),
        (Int32, 'music_vol_was'),
        (Int16, 'wait_counter'),
        (Int16, 'mbounds.Left'),
        (Int16, 'mbounds.Right'),
        (Int16, 'mbounds.Top'),
        (Int16, 'mbounds.Bottom'),
        (Int32, 'fade_effect'),
        (Int32, 'bg_frame_locked'),
        (dyn.array(Int32, MAXGSVALUES), 'globalscriptvars'),
        (Int32, 'cur_music_number'),
        (Int32, 'music_repeat'),
        (Int32, 'music_master_volume'),
        (Int32, 'digital_master_volume'),
        (dyn.block(MAX_WALK_AREAS), 'walkable_areas_on'),
        (Int16, 'screen_flipped'),
        (Int32, 'entered_at_x'),
        (Int32, 'entered_at_y'),
        (Int32, 'entered_edge'),
        (Int32, 'speech_mode'),
        (Int32, 'speech_skip_style'),
        (dyn.array(Int32, MAX_TIMERS), 'script_timers'),
        (Int32, 'sound_volume'),
        (Int32, 'speech_volume'),
        (Int32, 'normal_font'),
        (Int32, 'speech_font'),
        (Int8, 'key_skip_wait'),
        (Int32, 'swap_portrait_lastchar'),
        (Int32, 'separate_music_lib'),
        (Int32, 'in_conversation'),
        (Int32, 'screen_tint'),
        (Int32, 'num_parsed_words'),
        (dyn.array(Int16, MAX_PARSED_WORDS), 'parsed_words'),

        (dyn.clone(pstr.string, length=100), 'bad_parsed_word'),    # FIXME: this might be wrong
        (Int32, 'raw_color'),
        (dyn.array(Int16, LEGACY_MAXSAVEGAMES), 'filenumbers'),
        (Int32, 'mouse_cursor_hidden'),
        (Int32, 'silent_midi'),
        (Int32, 'silent_midi_channel'),
        (Int32, 'current_music_repeating'),
        (Int32, 'shakesc_delay'),
        (Int32, 'shakesc_amount'),
        (Int32, 'shakesc_length'),
        (Int32, 'rtint_red'),
        (Int32, 'rtint_green'),
        (Int32, 'rtint_blue'),
        (Int32, 'rtint_level'),
        (Int32, 'rtint_light'),
        (Bool, 'rtint_enabled'),
        (Int32, 'end_cutscene_music'),
        (Int32, 'skip_until_char_stops'),
        (Int32, 'get_loc_name_last_time'),
        (Int32, 'get_loc_name_save_cursor'),
        (Int32, 'restore_cursor_mode_to'),
        (Int32, 'restore_cursor_image_to'),
        (Int16, 'music_queue_size'),
        (dyn.array(Int16, MAX_QUEUED_MUSIC), 'music_queue'),
        (Int16, 'new_music_queue_size'),
        (dyn.array(QueuedAudioItem, MAX_QUEUED_MUSIC), 'new_music_queue'),
        (Int16, 'crossfading_out_channel'),
        (Int16, 'crossfade_step'),
        (Int16, 'crossfade_out_volume_per_step'),
        (Int16, 'crossfade_initial_volume_out'),
        (Int16, 'crossfading_in_channel'),
        (Int16, 'crossfade_in_volume_per_step'),
        (Int16, 'crossfade_final_volume_in'),

        (dyn.block(50), 'takeover_from'),
        (dyn.clone(pstr.string, length=PLAYMP3FILE_MAX_FILENAME_LEN), 'playmp3file_name'),
        (dyn.block(MAXGLOBALSTRINGS * MAX_MAXSTRLEN), 'globalstrings'),
        (dyn.block(MAX_MAXSTRLEN), 'lastParserEntry'),
        #(StringPrefixed, 'game_name'), # >= kGSSvgVersion_361_14
        (dyn.clone(pstr.string, length=LEGACY_GAMESTATE_GAMENAMELENGTH), 'game_name'),
        (Int32, 'ground_level_areas_disabled'),
        (Int32, 'next_screen_transition'),
        (Int32, 'gamma_adjustment'),
        (Int16, 'temporarily_turned_off_character'),
        (Int16, 'inv_backwards_compatibility'),
        (DoOnce, 'do_once_tokens'),

        (Int32, 'text_min_display_time_ms'),
        (Int32, 'ignore_user_input_after_text_timeout_ms'),
        #(Int32, 'ignore_user_input_until_time'), # < kGSSvgVersion_350_9
        (Int32, 'voice_speech_flags'),      # >= kGSSvgVersion_350_9
        #(Int32, 'dialog_options_gui_x'),        # >= kGSSvgVersion_363
        #(Int32, 'dialog_options_gui_y'),        # >= kGSSvgVersion_363
        #(Int32, 'dialog_options_textalign'),        # >= kGSSvgVersion_363
        #(Int32, 'reserve'),    # >= kGSSvgVersion_363
    ]

class InteractionVariable(pstruct.type):
    _fields_ = [
        (Int8, 'Type'),
        (Int32, 'Value'),
    ]

class Camera(pstruct.type):
    _fields_ = [
        (Int32, 'flags'),
        (Int32, 'Left'),
        (Int32, 'Top'),
        (Int32, 'Width'),
        (Int32, 'Height'),
    ]

class Viewport(pstruct.type):
    _fields_ = [
        (Int32, 'flags'),
        (Int32, 'Left'),
        (Int32, 'Top'),
        (Int32, 'Width'),
        (Int32, 'Height'),
        (Int32, 'ZOrder'),
        (Int32, 'ID'),
    ]

class RoomItems(pstruct.type):
    def __Items(self):
        res, object = self['Count'].li, self._object_
        return dyn.array(object, max(0, res.int()))

    _fields_ = [
        (Int32, 'Count'),
        (__Items, 'Items'),
    ]

@ComponentHandler.define
class GameStateComponent(pstruct.type):
    _tag_ = "Game State"
    class _intrVars(pstruct.type):
        def __vars(self):
            res = self['num'].li
            return dyn.array(InteractionVariable, max(0, res.int()))

        _fields_ = [
            (Int32, 'num'),
            (__vars, 'vars'),
        ]

    class RoomCameras(RoomItems):
        _object_ = Camera
    class RoomViewports(RoomItems):
        _object_ = Viewport

    _fields_ = [
        (GameSetupStruct, 'setup'),
        (dyn.array(RGB, 256), 'palette'),
        #(_intrVars, 'intrVars'),   # <= kGameVersion_272
        (GamePlayState, 'state'),
        (Int32, 'frames_per_second'),
        (Int32, 'loopcounter'),
        (Int32, 'ifacepopped'),
        (Int32, 'game_paused'),
        (Int32, 'cur_mode'),
        (Int32, 'cur_cursor'),
        (Int32, 'mouse_on_iface'),
        (Int32, 'viewcam_flags'),

        (RoomCameras, 'room_cameras'),
        (RoomViewports, 'room_viewports'),
    ]

class ComponentList(parray.terminated):
    _tag_ = 'Components'
    _object_ = TaggedComponent
    def isTerminator(self, component):
        res = component['tagOpen']
        string = res.str()
        return string == '</Components>'

class CommonComponents(pstruct.type):
    _fields_ = [
        (ComponentTagOpen, 'tagOpen'),
        (ComponentList, 'components'),
    ]
    def __getitem__(self, index):
        if isinstance(index, (''.__class__, u''.__class__)):
            return super(CommonComponents, self).__getitem__(index)
        return self['components'][index]
    def enumerate(self):
        for item in self['components'][:-1]:
            tag = item['tagOpen'].tagname()
            yield tag, item['component']
        return
    def iterate(self):
        for _, item in self.enumerate():
            yield item
        return

class File(pstruct.type):
    _fields_ = [
        (Signature, 'sig'),
        (Description, 'desc'),
        (UserDescription, 'user'),
        (CommonComponents, 'common'),
    ]

if __name__ == '__main__':
    import sys

    source = ptypes.prov.file(sys.argv[1], 'rb')

    z = File(source=source)
    z=z.l

