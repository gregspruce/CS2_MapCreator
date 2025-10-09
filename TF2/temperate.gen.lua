local mapgenutil = require "terrain/mapgenutil"
local temperateassetsgen = require "terrain/temperateassetsgen"
local layersutil = require "terrain/layersutil"
local maputil = require "maputil"

function data() 

return {
	climate = "temperate.clima.lua",
	order = 0,
	name = _("Temperate"),
	params = {
		{
			key = "hilliness",
			name = _("Hilliness"),
			values = { "", "", "", "", "" },
			defaultIndex = 2,
			uiType = "SLIDER",
		},
		{
			key = "water",
			name = _("Water"),
			values = { "", "", "", "", "" },
			defaultIndex = 2,
			uiType = "SLIDER",
		},
		{
			key = "forest",
			name = _("Forest"),
			values = { "", "", "", "", "", "", "", },
			defaultIndex = 3,
			uiType = "SLIDER",
		},
	},
	updateFn = function(params)
		-- local temperateassetsgen = dofile("./res/scripts/terrain/temperateassetsgen.lua")
		-- local mapgenutil = dofile("./res/scripts/terrain/mapgenutil.lua")
		-- local layersutil = dofile("./res/scripts/terrain/layersutil.lua")
		local result = {
			parallelFactor = 32,
			heightmapLayer = "HM",
			layers = layersutil.Layer.new(),
		}

		local sameSeed = math.random(1, 100000000)
		math.randomseed(sameSeed) -- reset seed to match desert generator
		
		-- #################
		-- #### CONFIG
		local hillyness = params.hilliness / 3
		local water = params.water / 4
		local humidity = params.forest / 7

		local noWater = water == 0
		
		local riverConfig = {
			depthScale = 1.5,
			maxOrder = 2,
			segmentLength = 2400,
			bounds = params.bounds,
			baseProbability = water * water * 2,
			minDist = water > 0.5 and 2 or 3,
		}
		
		local rivers = {}
		if not noWater then
			local start = mapgenutil.FindGoodRiverStart(params.bounds)
			mapgenutil.MakeRivers(rivers, riverConfig, 120000, start.pos, start.angle)
			
			local lakeProb1 = water > 0.2 and 0.2 or 0 -- math.map(water, 0, 1, 0.0, 0.1)
			local lakeProb2 = water > 0.2 and 0.4 or 0.9 -- math.map(water, 0, 1, 0.1, 0.1)
			local lakeConfig = {
				getLakePropability = function()
					return water + 0.2
				end,
				lakeSize = water * 600, 
			}
			mapgenutil.MakeLakesOld(rivers, lakeConfig)
			
			-- local curvesConfig = {
				-- getStrength = function(position) 
					-- return 0.7
				-- end,
				-- getWidthMultiplier = function(position) 
					-- return 1
				-- end
			-- }
			-- mapgenutil.MakeCurvesOld(rivers, curvesConfig)
			
			maputil.Convert(rivers)
			maputil.ValidateRiver(rivers)
			-- maputil.PrintRiver(rivers) 
		end
	
		local ridgesConfig = {
			bounds = params.bounds, 
			probabilityLow = 0.3 + 0.7 * hillyness,
			probabilityHigh = 0.5 + 0.5 * hillyness, 
			minHeight = 0 + 80 * hillyness, 
			maxHeight = 75 + 100 * hillyness,
		}

		local valleys = {}
		local ridges = mapgenutil.MakeRidges(ridgesConfig)
		
		-- #################
		-- #### PREPARE
		local mkTemp = layersutil.TempMaker.new()
		
		-- #################
		-- #### BACKGROUND AND RIVER
		result.layers:Constant(result.heightmapLayer, .01)
		
		do -- river
			result.layers:PushColor("#0022DD")
			result.layers:River(result.heightmapLayer, rivers)
			result.layers:PopColor()
		end
		
		local noiseMap = mkTemp:Get()
		result.layers:Noise(noiseMap, 150 * hillyness)
		
		local distanceMap = mkTemp:Get()
		result.layers:Distance(result.heightmapLayer, distanceMap)
		
		-- #################
		-- #### RIDGES
		local ridgesMap
		do -- ridges
			result.layers:PushColor("#22AADD")
			local t1 = mkTemp:Get()
			result.layers:Map(distanceMap, t1, {15, 2500}, {0, 1}, true)
			result.layers:Mad(t1, noiseMap, result.heightmapLayer)
			noiseMap = mkTemp:Restore(noiseMap)
			
			local t2 = mkTemp:Get()
			result.layers:Ridge(t2, {
				valleys = valleys.points,
				ridges = ridges,
				noiseStrength = 10
			})
			
			result.layers:Map(distanceMap, t1, {50, 1500}, {0, 1}, true)
			ridgesMap = mkTemp:Get()
			result.layers:Mul(t1, t2, ridgesMap)
			t1 = mkTemp:Restore(t1)
			t2 = mkTemp:Restore(t2)

			result.layers:Add(ridgesMap, result.heightmapLayer, result.heightmapLayer)
			result.layers:PopColor()
		end
		
		-- #################
		-- #### NOISE
		local noiseStrength = 25.7
		local addNoise = true
		if addNoise then
			result.layers:PushColor("#5577DD")
			local t2 = mkTemp:Get()
			result.layers:RidgedNoise(t2, { octaves = 5, frequency = 1 / 444, lacunarity = 2.2, gain = 0.8 } )
			result.layers:Map(t2, t2, {0, 4}, {0, noiseStrength * 1.2}, false)
			
			local t1 = mkTemp:Get()
			result.layers:Map(distanceMap, t1, {0, 30}, {0, 1}, true)
			
			result.layers:Mad(t2, t1, result.heightmapLayer)
			mkTemp:Restore(t1)
			mkTemp:Restore(t2)
			result.layers:PopColor()
		end
		
		-- #################
		-- #### ASSETS
		local config =  {
			-- GENERIC
			humidity = humidity / 2.5,
			water = water,
			-- LEVEL 3
			hillsLowLimit = 20, -- relative [m]
			hillsLowTransition = 20, -- relative [m]
			-- LEVEL 4
			treeLimit = 160, -- absolute [m] (absolute maximal height)
			ridgeFactor = 0.6, -- lower means softer ridges detection, more trees (0.8)
			valleyFactor = 0.6, -- lower means softer valleys detection, more trees (0.8)
		}
		
		result.layers:PushColor("#007777")
		result.forestMap, result.treesMapping, result.assetsMap, result.assetsMapping = temperateassetsgen.Make(
			result.layers, config, mkTemp, result.heightmapLayer, ridgesMap, distanceMap
		)
		result.layers:PopColor()
		distanceMap = nil
	
		-- #################
		-- #### FINISH
		ridgesMap = mkTemp:Restore(ridgesMap)
		mkTemp:Restore(result.forestMap)
		mkTemp:Restore(result.assetsMap)
		mkTemp:Finish()
		-- maputil.PrintGraph(result)
	
		return result
	end
}

end
