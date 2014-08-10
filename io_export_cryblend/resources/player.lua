Script.ReloadScript( "SCRIPTS/Entities/actor/BasicActor.lua");

Player = {

	AnimationGraph = "HumanMaleFullBody.xml",
	UpperBodyGraph = "HumanMaleUpperBody.xml",

	type = "Player",

	foreignCollisionDamageMult = 0.1,	
	vehicleCollisionDamageMult = 7.5,
	
	Properties = 
	{	
		-- AI-related properties
		soclasses_SmartObjectClass = "Player",
		groupid = 0,
		esFaction = "Players",
		commrange = 40; -- Luciano - added to use SIGNALFILTER_GROUPONLY
		-- AI-related properties over

		voiceType = "player",
		aicharacter_character = "Player",

		Perception =
		{
			--how visible am I
			camoScale = 1,
			--movement related parameters
			velBase = 1,
			velScale = .03,
			--ranges			
			sightrange = 50,
		}	,
		--
		fileModel = "Objects/characters/SDK_player/SDK_Player.cdf",
		clientFileModel = "Objects/characters/SDK_player/SDK_Player.cdf",
		fpItemHandsModel = "Objects/Weapons/arms_fp/arms_fp.chr",
		objFrozenModel= "Objects/characters/SDK_player/SDK_Player.cdf",
		fileHitDeathReactionsParamsDataFile = "Libs/HitDeathReactionsData/HitDeathReactions_PlayerSP.xml",
		
		CharacterSounds =
		{	
			footstepEffect = "footstep_player",		-- Footstep mfx library to use
			remoteFootstepEffect = "footstep",		-- Footstep mfx library to use for remote players
			bFootstepGearEffect = 0,				-- This plays a sound from materialfx
			footstepIndGearAudioSignal_Walk = "Player_Footstep_Gear_Walk",   -- This directly plays the specified audiosignal on every footstep
			footstepIndGearAudioSignal_Run = "Player_Footstep_Gear_Run",	-- This directly plays the specified audiosignal on every footstep
			foleyEffect = "foley_player",			-- Foley signal effect name
		},
	},

	PropertiesInstance = {
		aibehavior_behaviour = "PlayerIdle",
	},
	
	gameParams =
	{
		lookAtSimpleHeadBone = "Bip01 Head",
		canUseComplexLookIK = true,

		inventory =
		{
			items = 
			{ 
				{ name = "Zeus", equip = true },
			},
			ammo = 
			{
				{ name = "lightbullet", amount = 28},
			},
		},

		-- 
		Damage =
		{
			health = 150,
		},

		ammoCapacity =
		{
			bullet=40*7,
			explosivegrenade=10,
			scargrenade=10,
			rocket=3,
			c4explosive=4,
		},
	
		stance =
		{
			{
				stanceId = STANCE_STAND,
				normalSpeed = 1.25,
				maxSpeed = 3.5,
				walkSpeed = 1.7,
				runSpeed = 4.0,
				sprintSpeed = 6.6,
				heightCollider = 1.2,
				heightPivot = 0.0,
				size = {x=0.4,y=0.4,z=0.3},
				viewOffset = {x=0,y=-0.05,z=1.625},
				modelOffset = {x=0,y=0,z=0.0},
				name = "combat",
				useCapsule = 1,
			},
			-- -2 is a magic number that gets ignored by CActor::SetupStance
			{
				stanceId = -2,
			},
			--
			{
				stanceId = STANCE_CROUCH,
				normalSpeed = 2.6,
				maxSpeed = 2.6,
				walkSpeed = 1.75,
				runSpeed = 2.6,
				sprintSpeed = 2.6,
				customStrafeMultiplier = 1.0,
				heightCollider = 0.9,
				heightPivot = 0,
				size = {x=0.4,y=0.4,z=0.1},
				viewOffset = {x=0,y=0.1,z=1.0},
				modelOffset = {x=0,y=0,z=0},
				name = "crouch",
				useCapsule = 1,
			},
			--
			{
				stanceId = STANCE_PRONE,
				normalSpeed = 0.375,
				maxSpeed = 0.75,
				heightCollider = 0.4,
				heightPivot = 0,
				size = {x=0.35,y=0.35,z=0.001},
				viewOffset = {x=0,y=0.0,z=0.5},
				modelOffset = {x=0,y=0,z=0},
				weaponOffset = {x=0.0,y=0.0,z=0.0},
				name = "prone",
				useCapsule = 1,
			},
			--
			{
				stanceId = STANCE_SWIM,
				normalSpeed = 1.0,
				maxSpeed = 2.5,
				heightCollider = 1.0,
				heightPivot = 0,
				size = {x=0.4,y=0.4,z=0.35},
				viewOffset = {x=0,y=0.1,z=1.5},
				modelOffset = {x=0,y=0,z=0.0},
				weaponOffset = {x=0.3,y=0.0,z=0},
				name = "swim",
				useCapsule = 1,
			},
			--
			{
				stanceId = STANCE_ZEROG,
				normalSpeed = 1.75,
				maxSpeed = 3.5,
				heightCollider = 0.0,
				heightPivot = 0,
				size = {x=0.6,y=0.6,z=0.001},
				viewOffset = {x=0,y=0.0,z=0.35},
				modelOffset = {x=0,y=0,z=0.0},
				weaponOffset = {x=0.3,y=0.0,z=0},
				name = "zerog",
				useCapsule = 1,
			},
			{
				stanceId = STANCE_RELAXED,
				normalSpeed = 1.0,
				maxSpeed = 1.9,
				heightCollider = 1.2,
				heightPivot = 0.0,
				size = {x=0.4,y=0.4,z=0.2},
				modelOffset = {x=0,y=0,z=0},
				viewOffset = {x=0,y=0.10,z=1.625},
				weaponOffset = {x=0.2,y=0.0,z=1.3},
				name = "relaxed",
				useCapsule = 1,
			},
			-- -2 is a magic number that gets ignored by CActor::SetupStance
			{
				stanceId = -2,
			},
		},
		
		sprintMultiplier = 1.5,--speed is multiplied by this amount if sprint key is pressed -- 1.2 for a more counter-striky feel
		strafeMultiplier = 0.75,--speed is multiplied by this amount when strafing
		backwardMultiplier = 0.7,--speed is multiplied by this amount when going backward
		grabMultiplier = 0.5,--speed is multiplied by this amount when the player is carry the maximun amount carriable
				
		inertia = 10.0,--7.0,--the more, the faster the speed change: 1 is very slow, 10 is very fast already 
		inertiaAccel = 11.0,--same as inertia, but used when the player accel
			
		jumpHeight = 1.0,--meters
		
		slopeSlowdown = 3.0,
		
		leanShift = 0.35,--how much the view shift on the side when leaning
		leanAngle = 15,--how much the view rotate when leaning
		
		nanoSuitActive = 0,
--		thrusterAISoundRadius = 38,
		
	},
			
	modelSetup =
	{
		deadAttachments = {"head","helmet"},
	},
			
	Server = {},
	Client = {},
	squadFollowMode = 0,

	squadTarget = {x=0,y=0,z=0},
	SignalData = {},

	AI = {},
	OnUseEntityId = NULL_ENTITY,
	OnUseSlot = 0,
}

function Player:Expose()
	Net.Expose{
		Class = self,
		ClientMethods = {
			Revive							= { RELIABLE_ORDERED, POST_ATTACH },
			MoveTo							= { RELIABLE_ORDERED, POST_ATTACH, VEC3 },
			AlignTo							= { RELIABLE_ORDERED, POST_ATTACH, VEC3 },
			ClearInventory			= { RELIABLE_ORDERED, POST_ATTACH },
		},
		ServerMethods = {
			--UseEntity			 			= { RELIABLE_ORDERED, POST_ATTACH, ENTITYID, INT16, BOOL},
		},
		ServerProperties = {
		}
	};
end

function Player.Server:OnInit()
	--self.actor:SetPhysicalizationProfile("alive");
	
	self.thrusterAISoundRadius = 38;

	if AI then
		--AI related: create ai representation for the player
		CryAction.RegisterWithAI(self.id, AIOBJECT_PLAYER, self.Properties,self.PropertiesInstance);

		--AI related: player is leader of squad-mates always
		--AI.SetLeader(self.id);
	end

	self:OnInit();
end

function Player:PhysicalizeActor()
	--BasicActor.PhysicalizeActor(self);
end

function Player:OnRevive()
	BasicActor.OnRevive(self);
end

function Player:SetModel(model, arms, frozen, fp3p)
	if (model) then
		if (fp3p) then
			self.Properties.clientFileModel = fp3p;
		end
		self.Properties.fileModel = model;

		if (arms) then
			self.Properties.fpItemHandsModel = arms;
		end
		if (frozen) then
			self.Properties.objFrozenModel = frozen;
		end
		--BasicActor.PhysicalizeActor(self);
	end
end


function Player.Server:OnInitClient( channelId )
end


function Player.Server:OnPostInitClient( channelId )
	--for i,v in ipairs(self.inventory) do
		--self.onClient:PickUpItem(channelId, v, false);
	--end
	
	--if (self.inventory:GetCurrentItemId()) then
		--self.onClient:SetCurrentItem(channelId, self.inventory:GetCurrentItemId());
	--end
end


function Player.Client:Revive()
	self:ResetDofFx();
	self:ResetMotionFx();

	self.actor:Revive();
end


function Player.Client:MoveTo(pos)
	self:SetWorldPos(pos);
end


function Player.Client:AlignTo(ang)
	self.actor:SetAngles(ang);
end

function Player.Client:ClearInventory()
	self.inventory:Clear();
end

function Player.Client:OnSetPlayerId()
--	HUD:Spawn(self);
end


function Player.Client:OnInit()
	self:OnInit();
end

function Player:UpdateSounds(frameTime)
	BasicActor.UpdateSounds(self,frameTime);
	--FIXME:execute these for all actors?
	self:UpdateThrusterSounds(frameTime);
	self:UpdateAISounds(frameTime);
end

function Player.Client:OnUpdate(frameTime)
	BasicActor.Client.OnUpdate(self,frameTime);
	--if (self.inventory) then
		--self.inventory:Validate();
	--end
	
	-- Dynamic armor reduction
	--if (CryAction.IsServer() == false) then
	--	self:UpdateArmorHeat(frameTime);
	--end
	
	local item = self.inventory:GetCurrentItem();
	if (item) then
		if (self.hide_fp_item or self:IsHidden()) then
			item:Hide(1);
		elseif ((not self.hide_fp_item) and (item.weapon and (not item.weapon:IsZoomed()) and (not item.weapon:IsZooming()))) then
			item:Hide(0);
		end
	end

	--self:UpdateScreenEffects(frameTime);
	--FIXME:move to c++	
	self:UpdateDraw();
end

function Player.Server:OnUpdate(frameTime)
	BasicActor.Server.OnUpdate(self,frameTime);
		
	--FIXME:temporary
	if (self.stopEPATime and self.stopEPATime < 0) then
		self.actor:SetParams({followCharacterHead = 0,});
		self.actor:SetMovementTarget(g_Vectors.v000,g_Vectors.v000,g_Vectors.v000,1);
		self.stopEPATime = nil;
		self.hostageID = nil;
		
		self:HolsterItem(false);
						
	elseif (self.stopEPATime) then
		self.stopEPATime = self.stopEPATime - frameTime;
	end
	
end


function Player:OnInit(bIsReload)

--	AI.RegisterWithAI(self.id, AIOBJECT_PLAYER, self.Properties);
	self:SetAIName(self:GetName());
	----------------------------------------

--	self:InitSounds();
	
	self:OnReset(true, bIsReload);
	--self:SetTimer(0,1);
end


function Player:OnReset(bFromInit, bIsReload)

	g_aimode = nil;
	self.stopEPATime = nil;
	self.hostageID = nil;
	
	BasicActor.Reset(self, bFromInit, bIsReload);
	
	self:SetTimer(0,500);
	
	self.thrusterAIVolume = 1.0;		-- Have different volume for the AI, since it needs differen scale.
	self.thrusterVolume = nil;
	self:StopThrusterSounds();
	
	if (self == g_localActor) then
		self:ResetDofFx();
		self:ResetMotionFx();
	end

	mergef(Player.SignalData,g_SignalData,1);
	
	self.Properties.esFaction = "Players";
	self.squadFollowMode = 0;
			
	-- Reset temperature camoflage.
	self.camoState = false;
	self.camoFading = false;

	self.Properties.species = 0;
	-- Reset all properties to editor set values.
	if AI then 
		AI.ResetParameters(self.id, false, self.Properties, self.PropertiesInstance) end;

	self.lastOverloadTime = nil;
	
	--FIXME:set normal cloak as default
	self:SetCloakType(1);
end


----------------------------------------------------------------------------------------------------
function Player:StopThrusterSounds()
	if (self.thrusterSound) then
		self:StopSound(self.thrusterSound);
	end
	
	self.thrusterSound = nil;
end


----------------------------------------------------------------------------------------------------
function Player:StartThrusterSounds(afterburn)
			
	if (not self.thrusterSound or not Sound.IsPlaying(self.thrusterSound)) then	
		self.thrusterSound = self:PlaySoundEvent("sounds/interface:suit:thrusters_1p", g_Vectors.v000, g_Vectors.v010, SOUND_DEFAULT_3D, 0, SOUND_SEMANTIC_PLAYER_FOLEY);
		Sound.SetSoundLoop(self.thrusterSound,1);
	end
	
	self.thrusterVolume = 1.0 + afterburn * 0.15;
	self.thrusterAIVolume = 1.0 + afterburn * 3.0;
end

function Player:UpdateThrusterSounds(frameTime)
		
	if (self.thrusterVolume and self.thrusterVolume<0.0) then
		self:StopThrusterSounds();
		self.thrusterVolume = nil;
		self.thrusterAIVolume = 0;
	elseif (self.thrusterVolume) then
		self.thrusterVolume = self.thrusterVolume - frameTime;
		self.thrusterAIVolume = self.thrusterAIVolume - frameTime;
				
		local volume = self.zeroGTable.thrusterVolume;
		
		if (not volume) then
			volume = 150;
		end
		
		Sound.SetSoundVolume(self.thrusterSound,__min(255,__max(0,volume*self.thrusterVolume))/255.0);
	end
end

-- to tweak
--#g_localActor.thrusterAISoundRadius=2
function Player:UpdateAISounds(frameTime)

	local nextAISound = (self.nextAISound or 0) - frameTime;
	self.nextAISound = nextAISound;
	
	if (nextAISound<0) then
		--AI sounds are updated each 1 seconds
		self.nextAISound = 1.0;
		
		--update the thruster sound
		if (self.thrusterVolume) then
			local soundDamp = self.actorStats.soundDamp;
			local soundRadius = self.thrusterAISoundRadius * self.thrusterAIVolume * soundDamp;
			--Log("soundDamp:"..soundDamp);
			if AI then AI.SoundEvent(self:GetWorldPos(), soundRadius, AISOUND_MOVEMENT, self.id) end
		end
	end	
end

--function Player:InitSounds()

--	self:LoadPlayerSound("follow", "Languages/voicepacks/Player/moveout",3);
--	self:LoadPlayerSound("hold", "Languages/voicepacks/Player/holdup",3);
--	self:LoadPlayerSound("executeCommand", "Languages/missiontalk/cxp/go_ahead");
--	self:LoadPlayerSound("goto", "Languages/voicepacks/Player/get_moving",3);

--end

--function Player:LoadPlayerSound(soundName,wavfile,numberSounds)
--	self["Sound_"..soundName] = {};
--	if(numberSounds and numberSounds>0) then
--		for i=1,numberSounds do
--			self["Sound_"..soundName][i] = wavfile.."_"..i..".wav";
--		end
--	else
--		self["Sound_"..soundName][1] = wavfile..".wav";
--	end
--end

function Player:SetOnUseData(entityId, slot)
--	Log("SetOnUseData "..tostring(entityId).." "..tostring(slot))
	self.OnUseEntityId = entityId
	self.OnUseSlot = slot
end

function Player:OnAction(action, activation, value)
	-- gamerules needs to get all player actions all times
	if (g_gameRules and g_gameRules.Client.OnActorAction) then
		if (not g_gameRules.Client.OnActorAction(g_gameRules, self, action, activation, value)) then
			return;
		end
	end

	if (action == "use" or action == "xi_use") then	
		self:UseEntity( self.OnUseEntityId, self.OnUseSlot, activation == "press");
	end
end

function Player:OnActionUse(press)
	self:UseEntity( self.OnUseEntityId, self.OnUseSlot, press);
end

function Player:OnUpdateView(frameTime)
--	HUD:UpdateHUD(self, frameTime, true);--not self:IsHidden());
end

function Player:ScriptEvent(event,value,str)
	
	local message = nil;
	local sound = nil;
	
	if (event == "gyroscope") then
		message = "gyroscope";
		sound = "gyro";
	elseif (event == "gravityboots") then
		message = "gravity_boots";
		sound = "gboots"; 
	end
	
	if (message) then
		if (value == 1) then
			message = message.."_on";
		else
			message = message.."_off";
		end
		
--		HUD:AddInfoMessage(message);
	end
	
	if (sound) then
		if (value == 1) then
			sound  = sound.."_on";
		else
			sound  = sound.."_off";
		end

		PlayRandomSound(self,self.zeroGTable[sound]);
	end
	
	if (event == "thrusters") then
		self:StartThrusterSounds(value);
--	elseif (event == "printhud") then
--		HUD:AddInfoMessage(str);
	elseif (event == "unfreeze_shake") then
	  self:OnUnfreezeShake(value);
	end
	
	BasicActor.ScriptEvent(self,event,value,str);
end

function Player:GrabObject(object, query)
	BasicActor.GrabObject(self, object, query);
end

function Player.Client:OnTimer(timerId,mSec)
	if(timerId==SWITCH_WEAPON_TIMER) then 
		if AI then AI.Signal(SIGNALFILTER_GROUPONLY_EXCEPT,1,"CheckNextWeaponAccessory",self.id) end;

		-- set player combat class depending on weapon
		local item = self.inventory:GetCurrentItem();
		if(item and item.class=="LAW") then 
			if AI then AI.ChangeParameter( self.id, AIPARAM_COMBATCLASS, AICombatClasses.PlayerRPG ) end
		else	
			if AI then AI.ChangeParameter( self.id, AIPARAM_COMBATCLASS, AICombatClasses.Player ) end
		end
	else
		BasicActor.Client.OnTimer(self,timerId,mSec);
	end
end

function Player.Client:OnHit(hit, remote)
	BasicActor.Client.OnHit(self,hit,remote);
end

function Player:UseEntity(entityId, slot, press)
	assert(entityId)
	assert(slot)
	
	if ((self.actor:GetHealth() <= 0) or (self.actor:GetSpectatorMode()~=0) or (self.actorStats.isFrozen)) then
		return;
	end
	
	local entity = System.GetEntity(entityId)
	if entity then
		
		local onUsed = entity.OnUsed;
		local onUsedRelease = entity.OnUsedRelease;
		
		if (not onUsed) then
			local state = entity:GetState();
			if (state ~= "" and entity[state]) then
				onUsed = entity[state].OnUsed;
			end
		end
		
		if (not onUsedRelease) then
			local state = entity:GetState();
			if (state ~= "" and entity[state]) then
				onUsedRelease = entity[state].OnUsedRelease;
			end
		end
		
		--special case for grabbing
		if (self.grabParams.entityId) then
			if (press) then
				self.grabParams.dropTime = _time;
				return;
			elseif (self.grabParams.dropTime) then
				--drop it
				press = true;
			else
				return;
			end			
		end
		
		if (onUsed and press) then			
			onUsed(entity,self,slot);
			if AI then AI.SmartObjectEvent("OnUsed",entity.id,self.id) end;
		end
		
		if(onUsedRelease and not press) then
			onUsedRelease(entity,self,slot);
			if AI then AI.SmartObjectEvent("OnUsedRelease",entity.id,self.id) end;
		end
	end
end

function Player.Client:OnShutDown()
	BasicActor.ShutDown(self);
--	HUD:Destroy(self);
end


function Player:OnEvent( EventId, Params )
end


function Player:OnSave(save)
	BasicActor.OnSave(self, save);

--	local savedTable =self.AI_WeaponAccessoryTable;
--	if(savedTable) then 
--		save.AI_WeaponAccessoryTable = {};
--		for acc,on in pairs(savedTable) do
--			save.AI_WeaponAccessoryTable[acc] = on;
--		end
--	end

end


function Player:OnLoad(saved)
	BasicActor.OnLoad(self, saved);
--	HUD:Spawn(self);

--	self.AI.WeaponAccessoryTable = {};
--	local savedTable =saved.AI.WeaponAccessoryTable;
--	if(savedTable) then 
--		for acc,on in pairs(savedTable) do
--			self.AI.WeaponAccessoryTable[acc] = on;
--		end
--	end
	
end

function Player:OnLoadAI(saved)
	self.AI = {};
	if(saved.AI) then 
		self.AI = saved.AI;
	end
end

function Player:OnSaveAI(save)
	if(self.AI) then 
		save.AI = self.AI;
	end
end

function Player.Client:OnAnimationEvent(animation,strPar,intPar)	
	if (intPar == HOSTAGE_UNTIE) then
		if (self.hostageID) then
			local hostage = System.GetEntity(self.hostageID);
			if (hostage) then
				hostage:SetFree(self);
			end
			self.hostageID = nil;
		end
	end
	
	BasicActor.Client.OnAnimationEvent(self,animation,strPar,intPar);
end

-- weapon related methods

--FIXME
function Player:CanPickItem(item)
	return self:CanChangeItem();
end

function Player:CanChangeItem()	
	--if weapon is holstered, its not possible to switch weapons either
	if (self.holsteredItemId) then
		return false;
	end

	return true;
end

function Player:DropItem()
	local item;
	
	item = self.inventory:GetCurrentItem();
	if (item) then
		item:Drop();
	end
end

function Player:OnShoot(remote)
	-- Luciano: not called
	if (self.EPAtankId) then	
		return false;
	end
	
--	self:EnableFireControl();
	
	return true;
end

--function Player:EnableFireControl()
--	-- optimization to avoid a signal being sent everytime the player fires
--	local currentTime = System.GetCurrTime();
--	System.Log("SHHOOT CURRENT TIME ="..currentTime.." LAST FIRE TIME="..tostring(self.lastFireTime));
--	if (self.lastFireTime == nil) then
--		self.lastFireTime = currentTime;
--		AI.Signal(SIGNALFILTER_LEADER,0,"OnEnableFire",self.id);
--	elseif (currentTime - self.lastFireTime > 30) then
--		AI.Signal(SIGNALFILTER_LEADER,0,"OnEnableFire",self.id);
--		self.lastFireTime = currentTime;
--	end
--end

function Player:SetFollowMode( )
	AIBehavior.PlayerIdle:Follow(self);	
end


function Player:Goto()
--	if(self.gotoAllowed) then
--		
--		self.squadFollowMode = 0;
--		AI.Signal(SIGNALFILTER_LEADER,1,"ORD_GOTO",self.id, self.squadTarget);
--
--		self:SayOrder("goto","");
--		g_aimode	= 0;	
--
--	else
--		AI.LogEvent("GOTO not allowed");
--	end
end


function Player:SayOrder( soundName, answer, entity )
--	g_StringTemp1 = "Languages/voicepacks/Player/wait_here_"..random(1,2)..".wav";
--System.Log(">>>> player says hold >>> "..g_StringTemp1);		
	
	--local orderSound = Sound.Load3DSound(wavfile, 0, 128, 3, 43);
	local orderSoundTable = self["Sound_"..soundName];
	
	if(orderSoundTable ==nil) then
		return 
	end
	
	local numSound = count(orderSoundTable);
	if(numSound ==0) then
		return 
	end
	
	local orderSound = orderSoundTable[random(1,numSound)];
	if(answer and type(answer) == "string") then
		Player.SignalData.ObjectName = answer;
	else
		Player.SignalData.ObjectName ="";
	end
	if(orderSound) then
		ZeroVector(g_Vectors.temp_v1);
		g_Vectors.temp_v1.z = 0.6;
		
		local soundHandle = self:PlaySoundEvent(orderSound, g_Vectors.temp_v1, g_Vectors.v000, SOUND_DEFAULT_3D, 0, SOUND_SEMANTIC_AI_READABILITY);
		
		local soundLength = 500;
		if (soundHandle) then
			soundLength = Sound.GetSoundLength(soundHandle)*1000;
			if (soundLength > 2000) then
				soundLength = 2000;
			end
		end
		
		if(entity) then
			self.iSoundTimer  = Script.SetTimerForFunction(soundLength, "Player.OnEndCommandSound", entity);
		else
			self.iSoundTimer  = Script.SetTimerForFunction(soundLength, "Player.OnEndCommandSoundGroup", self);
		end
	else
		System.Log("[Player:SayOrder] Sound "..soundName.." not loaded");
	end

end

function Player:OnEndCommandSound(timerid)
	-- note: self is not the player but the entity which the signal is sent
	if AI then AI.Signal(SIGNALFILTER_SENDER,1,"ON_COMMAND_TOLD",self.id,Player.SignalData) end
end

function Player:OnEndCommandSoundGroup(timerid)
	if AI then AI.Signal(SIGNALFILTER_GROUPONLY,1,"ON_COMMAND_TOLD",self.id,Player.SignalData) end
end

--Player.SayAnswer = function (answer,timerid)
--	local answerSound = Sound.Load3DSound(answer, 0, 128, 3, 43);
--
--	if(answerSound) then
--		Sound.SetSoundPosition(answerSound, g_localActor:GetWorldPos());
--		Sound.PlaySound(answerSound);
--	end
--end

----------------------------------------------------------------------------------------------------
-- PLAYER SCREEN EFFECTS
----------------------------------------------------------------------------------------------------
function Player:UpdateScreenEffects(frameTime)
	if (self ~= g_localActor) then
		return
	end
	
	--Temperature camo effect
	local frostScale = 1;
	if (not self.camoState) then
		frostScale = -1;
	end

	if (self.camoFading == true) then
		
		local curFrost = 0;
		curFrost = System.GetScreenFx("ScreenFrost_Amount",curFrost) or 0;
		
		
		local maxFrost = 0.5;
		-- reach maxFrost in 2 seconds
		local frostRate = maxFrost / 2 * frostScale;
		local frostDelta = frostRate * frameTime;
		curFrost = curFrost + frostDelta;
		curFrost = clamp(curFrost, 0, 1);
		
		if (curFrost <= 0.01) then curFrost=0; end;
		
		System.SetScreenFx("ScreenFrost_Amount", curFrost);
		System.SetScreenFx("ScreenFrost_CenterAmount", 1-curFrost);
	
		--System.Log("FrostScale:"..frostScale);
		--System.Log("CurFrostAfter:"..curFrost);
		--System.Log("FrostRate:"..frostRate);
		
		if (curFrost == 0 or curFrost == 1) then
			self.camoFading = false;
			if (curFrost == 0) then
				System.SetScreenFx("ScreenFrost_Amount", 0);
			end
		end
	end
	--

	self.blurType = tonumber(System.GetCVar("cl_motionBlur")); 

	local stats = self.actorStats;
	local speed = stats.flatSpeed or 0;
	local minSpeed = self.gameParams.stance[1].maxSpeed;
	
	local viewBlur = self.viewBlur or 0;
	viewBlur = math.max(0.0,viewBlur - frameTime);
	self.viewBlur = viewBlur;
	
	if (viewBlur>0.001) then		
		blurAmount = self.viewBlurAmt or 0;
		self:SetMotionFxMask();
		self:SetMotionFxAmount(blurAmount, 2.5);
	elseif ((stats.onGround or 0)>0.1 and speed>minSpeed) then
		local maxSpeed = minSpeed * self.gameParams.sprintMultiplier;
		local blurAmount = (speed-minSpeed)/(maxSpeed-minSpeed)*tonumber(System.GetCVar("cl_sprintBlur"));--1.25;
		self:SetMotionFxMask("textures/player/motionblur_mask.dds");		
		self:SetMotionFxAmount(blurAmount, 2.5);
	else
		self:SetMotionFxAmount(0, 4);
	end
	
	--self:SetDofFxLimits(0, 1500, 1800, 2);
	--self:SetDofFxAmount(0, 0.5);
	self:UpdateDofFx(frameTime);
	self:UpdateMotionFx(frameTime);
end

----------------------------------------------------------------------------------------------------
function Player:SetDofFxLimits(focusmin, focusmax, focuslim, speed)
	if (not speed) then
		System.SetPostProcessFxParam("Dof_FocusRange", -1);
		System.SetPostProcessFxParam("Dof_FocusMin", focusmin);	
		System.SetPostProcessFxParam("Dof_FocusMax", focusmax);	
		System.SetPostProcessFxParam("Dof_FocusLimit", focuslim);
	else
		if (speed > 0) then
			self.dof_distance_speed = speed;
			self.target_dof_min = focusmin;
			self.target_dof_max = focusmax;
			self.target_dof_lim = focuslim;
		else
			self.dof_distance_speed = 0;
			self.current_dof_min = focusmin;
			self.current_dof_max = focusmax;
			self.current_dof_lim = focuslim;
			self.target_dof_min = focusmin;
			self.target_dof_max = focusmax;
			self.target_dof_lim = focuslim;
			System.SetPostProcessFxParam("Dof_FocusRange", -1);
			System.SetPostProcessFxParam("Dof_FocusMin", focusmin);	
			System.SetPostProcessFxParam("Dof_FocusMax", focusmax);	
			System.SetPostProcessFxParam("Dof_FocusLimit", focuslim);
		end
	end
end

----------------------------------------------------------------------------------------------------
function Player:SetDofFxMask(texName)
	if (texName) then
		System.SetPostProcessFxParam("Dof_UseMask", 1);	
		System.SetPostProcessFxParam("Dof_MaskTexName", texName);	
	else
		System.SetPostProcessFxParam("Dof_UseMask", 0);	
	end	
end

----------------------------------------------------------------------------------------------------
function Player:SetDofFxAmount(amount, speed)
	if (not speed) then
		System.SetPostProcessFxParam("Dof_BlurAmount", amount);	
		
		if (amount <= 0.075) then
			System.SetPostProcessFxParam("Dof_Active", 0);
		else
			System.SetPostProcessFxParam("Dof_Active", 1);
		end
	else
		if (speed > 0) then
			self.dof_amount_speed = speed;
			self.target_dof_amount = amount;
		else
			self.dof_amount_speed = 0;
			self.current_dof_amount = amount;
			self.target_dof_amount = amount;
		end
	end
end

----------------------------------------------------------------------------------------------------
function Player:ResetDofFx(speed)
	-- how cool would a memset in lua be ?
	if (speed) then
		self.dof_amount_speed = speed;
		self.dof_distance_speed = speed;
		self.target_dof_min = 0;
		self.target_dof_max = 2000;
		self.target_dof_lim = 2500;
		self.target_dof_amount = 0;
	else
		self.dof_amount_speed = 0;
		self.dof_distance_speed = 0;
		self.target_dof_min = 0;
		self.target_dof_max = 2000;
		self.target_dof_lim = 2500;
		self.target_dof_amount = 0;
		self.current_dof_min = 0;
		self.current_dof_max = 2000;
		self.current_dof_lim = 2500;
		self.current_dof_amount = 0;
		
		self:SetDofFxLimits(self.current_dof_min, self.current_dof_max, self.current_dof_lim);
		self:SetDofFxAmount(0);
	end
end

local DofInterpolate = function(curr, target, speed, frameTime)
	local dt = target-curr;
	if (math.abs(dt) > 0.005) then
		return curr + math.min(frameTime*speed, 1.0)*dt;
	else
		return target;
	end
end

----------------------------------------------------------------------------------------------------
function Player:UpdateDofFx(frameTime)
	if (not self.dof_amount_speed) then
		self:ResetDofFx();
	end

	
	-- update dof amount
	local curr_dof_amt = self.current_dof_amount;
	local target_dof_amt = self.target_dof_amount;
	
	if (curr_dof_amt ~= target_dof_amt) then
		self.current_dof_amount = DofInterpolate(curr_dof_amt, target_dof_amt, self.dof_amount_speed, frameTime);
		self:SetDofFxAmount(self.current_dof_amount);
	end
	
	-- update dof distances
	-- dof min
	local curr_dof_min = self.current_dof_min;
	local target_dof_min = self.target_dof_min;
	-- dof max
	local curr_dof_max = self.current_dof_max;
	local target_dof_max = self.target_dof_max;
	-- dof limit
	local curr_dof_lim = self.current_dof_lim;
	local target_dof_lim = self.target_dof_lim;
	local changelimits = false;

	if (curr_dof_min ~= target_dof_min) then
		self.current_dof_min = DofInterpolate(curr_dof_min, target_dof_min, self.dof_distance_speed, frameTime);
		changelimits = true;
	end

	if (curr_dof_max ~= target_dof_max) then
		self.current_dof_max = DofInterpolate(curr_dof_max, target_dof_max, self.dof_distance_speed, frameTime);
		changelimits = true;
	end

	if (curr_dof_lim ~= target_dof_lim) then
		self.current_dof_lim = DofInterpolate(curr_dof_lim, target_dof_lim, self.dof_distance_speed, frameTime);
		changelimits = true;
	end
	
	if (changelimits) then
		self:SetDofFxLimits(self.current_dof_min, self.current_dof_max, self.current_dof_lim);
	end
end

----------------------------------------------------------------------------------------------------
function Player:SetMotionFxAmount(amount, speed)
	if (self.blurType == 0) then
		System.SetPostProcessFxParam("MotionBlur_Active", 0);
	end
	
	-- accumulation based
	if (self.blurType == 1) then
		System.SetPostProcessFxParam("MotionBlur_Type", 0);	
		if (not speed) then
			System.SetPostProcessFxParam("MotionBlur_Amount", amount);	
			if (amount < 0.075) then
				System.SetPostProcessFxParam("MotionBlur_Active", 0);
			else
				System.SetPostProcessFxParam("MotionBlur_Active", 1);
			end
		else
			if (speed > 0) then
				self.mblur_amount_speed = speed;
				self.target_mblur_amount = amount;
			else
				self.mblur_amount_speed = 0;
				self.current_mblur_amount = amount;
				self.target_mblur_amount = amount;
				System.SetPostProcessFxParam("MotionBlur_Amount", amount);	
			end
		end
	end
	
	-- velocity based
	if (self.blurType == 2) then
		amount = clamp(amount, 0, 1);
		amount = amount*amount;
		System.SetPostProcessFxParam("MotionBlur_Type", 1);	
		System.SetPostProcessFxParam("MotionBlur_Quality", 2);	
		if (not speed) then
			--System.Log(tostring(amount));
			local sprintScale = 0;
			if (amount > 0.3) then 
				sprintScale = (amount - 0.3)/0.7;
			end
			
			local headDir = self.actor:GetHeadDir(g_Vectors.temp_v3);
			local velocity = NormalizeVector(self:GetVelocity(g_Vectors.temp_v4));
			local sprintAmount = 1-dotproduct3d(headDir, velocity);
			
			if (sprintAmount < 0) then
				sprintAmount = 0;
			end
			sprintScale = clamp(sprintScale, 0, 1);
			sprintAmount = clamp(sprintAmount, 0, 1);
			System.SetPostProcessFxParam("MotionBlur_CameraSphereScale", 8 - 6.0*sprintScale*sprintAmount);	
			System.SetPostProcessFxParam("MotionBlur_VectorsScale", 1.5);	
			System.SetPostProcessFxParam("MotionBlur_Active", 1);
		else
			if (speed > 0) then
				self.mblur_amount_speed = speed;
				self.target_mblur_amount = amount;
			else
				self.mblur_amount_speed = 0;
				self.current_mblur_amount = amount;
				self.target_mblur_amount = amount;
				System.SetPostProcessFxParam("MotionBlur_CameraSphereScale", 2*amount);	
				System.SetPostProcessFxParam("MotionBlur_VectorsScale", 1.5*amount);	
			end
		end
	end
end


----------------------------------------------------------------------------------------------------
function Player:SetMotionFxMask(texName)
	if (self.blurType == 1) then
		if (texName) then
			System.SetPostProcessFxParam("MotionBlur_UseMask", 1);	
			System.SetPostProcessFxParam("MotionBlur_MaskTexName", texName);	
		else
			System.SetPostProcessFxParam("MotionBlur_UseMask", 0);	
		end	
	end
end


----------------------------------------------------------------------------------------------------
function Player:ResetMotionFx()
	self.viewBlur = 0;
	self.viewBlurAmt = 0;

	self.mblur_amount_speed = 0;
	self.target_mblur_amount = 0;
	self.current_mblur_amount = 0;
	self:SetMotionFxAmount(0);
	System.SetPostProcessFxParam("MotionBlur_Active", 0);
end

local MBlurInterpolate = function(curr, target, speed, frameTime)
	local dt = target-curr;
	if (math.abs(dt) > 0.005) then
		return curr + math.min(frameTime*speed, 1.0)*dt;
	else
		return target;
	end
end

----------------------------------------------------------------------------------------------------
function Player:UpdateMotionFx(frameTime)
	if (not self.mblur_amount_speed) then
		self:ResetMotionFx();
	end
	
	-- update motion blur amount
	local curr_mblur_amt = self.current_mblur_amount;
	local target_mblur_amt = self.target_mblur_amount;
	
	if (not curr_mblur_amt) then
		curr_mblur_amt = 0;
	end
	
	if (curr_mblur_amt ~= target_mblur_amt) then
		self.current_mblur_amount = MBlurInterpolate(curr_mblur_amt, target_mblur_amt, self.mblur_amount_speed, frameTime);
		self:SetMotionFxAmount(self.current_mblur_amount);
	end
end


----------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------
-- FUNCTIONS TO BE REMOVED AFTER CXP GO HERE :)

--
--function Player:UpdateSquadTarget( )
--
--	local hpos = g_Vectors.temp_v1;
--	self.actor:GetHeadPos(hpos);
--	local hdir = g_Vectors.temp_v2;
--	self.actor:GetHeadDir(hdir);
--	local hdirlength = LengthVector(hdir);
--	
--	self.gotoAllowed = false;
--	self.squadmateUseMessage =nil;
--	self.aimedEntity = nil;
--	
--	if(hdirlength==0) then
--		return
--	end
--	
--	ScaleVectorInPlace(hdir,60/hdirlength);
--
--	local hitNum = Physics.RayWorldIntersection(hpos,hdir,1,ent_terrain+ent_static+ent_rigid+ent_sleeping_rigid+ent_living,self.id,NULL_ENTITY,g_HitTable);
--		
--	if(hitNum==0) then
--		return
--	end
--	local firstHit = g_HitTable[1];
-- 	if( firstHit.dist > 50) then
--		return
--	end
--	
--	self.gotoAllowed = true;
--	
--	CopyVector(self.squadTarget,firstHit.pos);
--	
--	if(firstHit.entity) then
--		-- TO DO: squadmate interaction with aimed entity
--		local aim = firstHit.entity;
--		self.aimedEntity = aim;
--		if(aim.UsableBySquadmates and aim:UsableBySquadmates()) then
--		  self.squadmateUseMessage = aim.squadmateUseMessage;
--		end
--		 
--	end
--	
--end

function Player:UpdateActorEffects(deltaTime)
	BasicActor.UpdateActorEffects(self,deltaTime);
end

function Player:UpdateDraw()	
	local stats = self.actorStats;

	--AI or thirperson, show all
	if (stats.isHidden or self.actor:GetSpectatorMode()~=0) then
		self:DrawSlot(0,0);
	elseif (self ~= g_localActor or stats.thirdPerson or stats.isOnLadder) then
		self:DrawSlot(0,1);	
		--show all
		self:HideAllAttachments(0, false, false);
		-- hide head if we are on a ladder and thirdperson is not set
		if (self == g_localActor and stats.isOnLadder and not stats.thirdPerson) then
			for i,attachment in pairs(self.modelSetup.deadAttachments) do
				self:HideAttachment(0,attachment,true,false);
			end
		end
	else
		local ghostPit = self.actor:IsGhostPit();	  
	  
		if (self.hideActor) then
			self:DrawSlot(0,0);
		elseif (stats.followCharacterHead==1 or self.grabParams.entityId or (self:IsOnVehicle() and not ghostPit)) then
			self:DrawSlot(0,1);
			--first show all
			self:HideAllAttachments(0, false, false);
			--then hide the necessary
			for i,attachment in pairs(self.modelSetup.deadAttachments) do
				self:HideAttachment(0,attachment,true,false);
			end
		elseif ((stats.firstPersonBody or 0)>0 and not ghostPit) then
			self:DrawSlot(0,1);
			--hid attachments for the body first person model
			self:HideAllAttachments(0, true, false);
		else
			self:DrawSlot(0,0);
		end
	end
end

--function Player:EntityInFront(entity)
--	BasicActor.EntityInFront(self,entity);
--end

function Player:IsSquadAlive()
	if not AI then return false end
	local count = AI.GetGroupCount(self.id);		
	for i=1,count do
		local mate = AI.GetGroupMember(self.id,i);
		if(mate and mate ~=self and not mate:IsDead()) then
			return true;
		end
	end
	return false
end

-- 
-- Protypes for some suit features.
--
function Player:SuitOverloadProto()

	if( self.lastOverloadTime ) then
		local	dt = _time - self.lastOverloadTime;
		if( dt < 30.0 ) then
			self:PlaySoundEventEx("sounds/interface:suit:temperature_beep", 0, 1, {x=0,y=0,z=0}, 0, 0, 0, SOUND_SEMANTIC_NANOSUIT);
			return;
		end
	end
	self.lastOverloadTime = _time;

	HUD:AddInfoMessage("overloading_suit");

	self:PlaySoundEventEx("Sounds/interface:suit:nano_suit_energy_pulse_1p", 0, 1, {x=0,y=0,z=0}, 0, 0, 0, SOUND_SEMANTIC_NANOSUIT);

	Script.SetTimerForFunction(1000, "Player.OnSuitOverload",self);
end

function Player:OnSuitOverload(timerid)

	-- add camera shake
	self.actor:CameraShake(20, 2.0, 0.07, g_Vectors.v000);

	-- paralyze all aliens in close proximity.
	local pos = self:GetWorldPos();
	local radius = 75;

	local entities = System.GetPhysicalEntitiesInBox(pos, radius);
	
	if (entities) then
		-- calculate damage for each entity
		for i,entity in ipairs(entities) do

			local sameSpecies = false;
			if( self.Properties.species and entity.Properties.species ) then
				if( self.Properties.species == entity.Properties.species ) then
					sameSpecies = true;
				end
			end

			if (entity ~= self and not sameSpecies) then

				-- Use radial test (got entities in box).
				local	dir = g_Vectors.temp_v1;
				SubVectors( dir, entity:GetPos(), pos );
				local	dist = LengthVector(dir);
				dir.z = dir.z + dist * 0.1;
				NormalizeVector( dir );

				if( dist < radius ) then

					local	strength = (dist / radius);

					if( entity.MakeParalyzed ) then
						-- make the alien paralyzed.
						entity:MakeParalyzed( dir, strength );
					else
						-- push it to some direction.
						entity:AddImpulse(-1, pos, dir, 50 * (strength * 0.5 + 0.5), 1);
					end
				end
			end
		end
	end
end

-------------------------------------------------------------------------------
--[[ MR: not used so far
function Player:OnPreFreeze(freeze, vapor)	
	if (freeze and g_gameRules and not g_gameRules:IsMultiplayer()) then	  
    local ratio = self.actor:GetHealth() / self.actor:GetMaxHealth();
	  if (ratio > 0.5) then
	    return false; -- don't allow freezing above health ratio
	  end		
	end	
	
	return true;
end
--]]

-------------------------------------------------------------------------------
function Player:OnFrost(shooterId, weaponId, frost)
  -- this adds the frost amount to the player (only needed in SP so far)  
  if (g_gameRules and not g_gameRules:IsMultiplayer() and frost > 0) then
    
    local oldAmt = self.actor:GetFrozenAmount();
    self.actor:AddFrost(frost);	  
	  local newAmt = self.actor:GetFrozenAmount();
	  
	  --Log("frost: %.3f, old: %.2f, new: %.2f", frost, oldAmt, newAmt);
	  
	  -- trigger sound feedback
	  if (newAmt < 1.0 and self.actor:IsLocalClient()) then
  	  if (not self.playerFrostSounds) then
  	    self.playerFrostSounds = {0.2, 0.4, 0.6, 0.8};
  	  end
  	  
  	  local currTime = System.GetCurrTime();
      
      if (currTime - (self.lastFrostSound or 0) > 0.1) then
    	  for i,val in ipairs(self.playerFrostSounds) do
    	    if (oldAmt < val and newAmt >= val) then    	      
    	      self:PlaySoundEvent("sounds/interface:hud:freeze_burst", g_Vectors.v000, g_Vectors.v010, 0, 0, SOUND_SEMANTIC_HUD);
    	      self.lastFrostSound = currTime;
    	      break;
    	    end
    	  end    	  
    	end
  	end
	end
end;

-------------------------------------------------------------------------------
function Player:OnUnfreezeShake(deltaFreeze)  
  if (not self.lastUnfreezeShake) then
	  self.lastUnfreezeShake = 0;
	end
  
  if (deltaFreeze>0) then
    -- next stage reached
    self:PlaySoundEvent("sounds/interface:hud:freeze_player", g_Vectors.v000, g_Vectors.v010, SOUND_2D, 0, SOUND_SEMANTIC_HUD);    
    
    local effect = "breakable_objects.frozen_human.vapor_gun";        
    local item = self.inventory:GetCurrentItem();
    if (item) then
      local slot = item:LoadParticleEffect(-1, effect, {} );
    end    
  else    
    local currTime = System.GetCurrTime();
    if (currTime - self.lastUnfreezeShake > 0.25) then    
      self:PlaySoundEvent("sounds/interface:suit:frozen_trying_to_unfreeze", g_Vectors.v000, g_Vectors.v010, SOUND_2D, 0, SOUND_SEMANTIC_NANOSUIT);    
      self.lastUnfreezeShake = currTime;
    end
  end    
  
end

--function Player:CurrentItemChanged(newItemId,lastItemId)
--
--	local item = System.GetEntity(newItemId);
--	if(item) then 
--		-- notify squadmates about the attachments on new weapon
--		local weapon = item.weapon;
--		local entityAccessoryTable = SafeTableGet(self.AI, "WeaponAccessoryTable");
--		if(weapon and entityAccessoryTable) then 
--			if(weapon:GetAccessory("Silencer") or item.class == "Fists") then
--				entityAccessoryTable["Silencer"] = 1;
--				self.AI.Silencer = true;
--			else
--				entityAccessoryTable["Silencer"] = 0;
--				self.AI.Silencer = false;
--			end
--			
--			if(weapon:GetAccessory("SCARIncendiaryAmmo")) then
--				entityAccessoryTable["SCARIncendiaryAmmo"] = 2;
--				entityAccessoryTable["SCARNormalAmmo"] = 0;
--			elseif(weapon:GetAccessory("SCARNormalAmmo")) then
--				entityAccessoryTable["SCARIncendiaryAmmo"] = 0;
--				entityAccessoryTable["SCARNormalAmmo"] = 2;
--			end
--			-- use a timer to avoid repeated spamming notifications
--			self:SetTimer(SWITCH_WEAPON_TIMER,2000);
--		end
--	end
--end


CreateActor(Player);
Player:Expose();
