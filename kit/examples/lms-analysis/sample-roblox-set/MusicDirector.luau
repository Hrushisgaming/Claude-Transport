--!strict
-- MusicDirector.luau  (ModuleScript, put it in ReplicatedStorage; require it from a LocalScript)
-- State-based music for round games (lobby -> tension -> chase -> last man standing -> win/lose).
-- Written for the kit's `af.py ost build` set (one key, one BPM, loops cut to whole bars). NOT run in Studio by the kit author:
-- test it, and re-check Roblox's current audio rules (private-by-default uploads, asset permissions) before shipping.
local SoundService = game:GetService("SoundService")
local TweenService = game:GetService("TweenService")
local ContentProvider = game:GetService("ContentProvider")

-- 1. paste your uploaded asset IDs. bpm/bars come from roblox_manifest.md. loop=false for stingers.
local TRACKS = {
	lobby   = { id = "rbxassetid://0", loop = true,  bpm = 178, bars = 16, volume = 0.5 },
	tension = { id = "rbxassetid://0", loop = true,  bpm = 178, bars = 16, volume = 0.5 },
	chase   = { id = "rbxassetid://0", loop = true,  bpm = 178, bars = 24, volume = 0.6 },
	lms_intro = { id = "rbxassetid://0", loop = false, bpm = 178, bars = 0, volume = 0.65 },   -- plays ONCE, then `lms` takes over
	lms     = { id = "rbxassetid://0", loop = true,  bpm = 178, bars = 24, volume = 0.65, intro = "lms_intro" },
	win     = { id = "rbxassetid://0", loop = false, bpm = 178, bars = 0,  volume = 0.6 },
	lose    = { id = "rbxassetid://0", loop = false, bpm = 178, bars = 0,  volume = 0.6 },
}

local MusicDirector = {}
MusicDirector.__index = MusicDirector

function MusicDirector.new()
	local self = setmetatable({}, MusicDirector)
	self.group = Instance.new("SoundGroup"); self.group.Name = "Music"; self.group.Parent = SoundService
	self.sounds = {} :: { [string]: Sound }
	self.current = nil :: string?
	self.token = 0
	for name, t in TRACKS do
		local s = Instance.new("Sound"); s.Name = name; s.SoundId = t.id; s.Looped = t.loop; s.Volume = 0; s.SoundGroup = self.group; s.Parent = self.group
		self.sounds[name] = s
	end
	task.spawn(function() ContentProvider:PreloadAsync(self.group:GetChildren()) end)
	return self
end

local function fade(s: Sound, to: number, dur: number)
	TweenService:Create(s, TweenInfo.new(dur, Enum.EasingStyle.Sine), { Volume = to }):Play()
end

-- seconds until the next bar line of the CURRENT looping track (so cuts land on the beat grid); 0 while an intro/sting plays
function MusicDirector:_untilBar(): number
	local cur = self.current and TRACKS[self.current]
	local snd = self.current and self.sounds[self.current]
	if not (cur and snd and cur.loop and snd.IsPlaying) then return 0 end
	local barLen = 240 / cur.bpm
	return barLen - (snd.TimePosition % barLen)
end

-- opts.quantize: "bar" (wait for the next bar line, default for loops) or "now". opts.fade: seconds. opts.restart: restart the target from 0.
function MusicDirector:SetState(name: string, opts: { quantize: string?, fade: number?, restart: boolean? }?)
	local o = opts or {}
	local target, spec = self.sounds[name], TRACKS[name]
	if not target or not spec then warn("MusicDirector: unknown state " .. tostring(name)); return end
	if self.current == name and spec.loop and not o.restart then return end
	self.token += 1; local my = self.token
	local wait = (o.quantize ~= "now") and self:_untilBar() or 0
	task.delay(wait, function()
		if my ~= self.token then return end                       -- a newer request replaced this one
		local d = o.fade or 0.25
		for other, snd in self.sounds do                               -- fade out everything that is not the target (including a half-played intro)
			if other ~= name and snd.IsPlaying then fade(snd, 0, d); task.delay(d + 0.05, function() if self.current ~= other then snd:Pause() end end) end
		end
		self.current = name
		local intro = spec.intro and self.sounds[spec.intro]
		if intro and not o.restart and not target.IsPlaying then
			intro.TimePosition = 0; intro:Play(); fade(intro, TRACKS[spec.intro].volume, d)
			intro.Ended:Once(function()                               -- intro finished: start the loop on its first sample (same BPM, whole bars)
				if self.current == name then target.TimePosition = 0; target:Play(); fade(target, spec.volume, 0.05) end
			end)
		else
			if o.restart or not target.IsPlaying then target.TimePosition = 0; target:Play() end
			fade(target, spec.volume, d)
		end
	end)
end

-- one-shot sting (win/lose) that ducks the current music, then optionally moves to a follow-up state
function MusicDirector:Sting(name: string, thenState: string?)
	local s = self.sounds[name]; if not s then return end
	self.token += 1
	if self.current and self.sounds[self.current] then fade(self.sounds[self.current], 0, 0.15) end
	s.TimePosition = 0; s.Volume = TRACKS[name].volume; s:Play()
	s.Ended:Once(function() self.current = nil; if thenState then self:SetState(thenState, { quantize = "now", fade = 1.0 }) end end)
end

return MusicDirector

--[[ USAGE (LocalScript), adapt the remote/state names to your game:
local Director = require(game.ReplicatedStorage.MusicDirector).new()
Director:SetState("lobby", { quantize = "now", fade = 1 })
-- round starts:                     Director:SetState("tension")
-- a killer targets you:             Director:SetState("chase")
-- survivors left == 1 (LAST MAN STANDING): Director:SetState("lms", { quantize = "bar", fade = 0.15 })
-- round ends, the last survivor is free:   Director:Sting("win", "lobby")
-- you were caught:                         Director:Sting("lose", "lobby")
]]
