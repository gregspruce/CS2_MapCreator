local data = {}

data.Make = function(layers, config, mkTemp, heightMap, ridgesMap, distanceMap)
	-- #################
	-- #### PARAMS
	-- Tree types
	local shrub = 1
	local palm = 2
	local broadleaf = 5
	local forest = 3
	local anyTree = 255
	
	local treesMapping = {
		[forest] = "forest",
		[palm] = "palm",
		[shrub] = "shrub",
		[broadleaf] = "broadleaf",
		[anyTree] = "all",
	}
	
	local assetsMapping = {
		[1] = "cracked",
		[2] = "granite",
	}
	
	-- #################
	-- #### CONFIG
	
	local palmProbability = 0.7
	local shrubProbability = 0.4
	
	local coniferDensity = 0.1
	local coniferHillDensity = 0.05
	
	-- Heights
	local hillsLowLimit = 10 -- relative [m]
	local hillsMiddleLimit = 60 -- relative [m]
	local hillsHighLimit = 180 -- relative [m]

	local coniferTransitionLow = 30 -- transition size [m]
	local coniferTransitionHigh = 30 -- transition size [m]
	
	-- LEVEL 0: Single trees
	local singleTreeDensity = 0.002
	
	-- LEVEL 1: Plain trees seed density
	local seedDensity = 0.00008 - 0.0001 * config.humidity * config.humidity + 0.0001 -- increase to increase number of forest
	local plainForestDensity = 0.15 -- reduce to reduce density of forest
	local permeability = 0.51 + math.sqrt(config.humidity) * 0.12 - 0.21 -- overall size of forest
	local permeabilityVariance = 1.6 -- variability in size of forest

	local plainForestDist = { 0.7 }
	local plainForestTypes = { 0, forest }
	
	-- LEVEL 3: Hill trees
	local maxSlope = 0.5
	local hillDensityBase = 0.6
	
	local hillForestDist = { 0.35 }
	local hillForestTypes = { 0, forest }
	
	-- LEVEL 4: Water trees
	local palmBeachSteps = {0.3, 0.7}
	local palmBeachTypes = {palm, shrub, 0}
	
	local treeDistanceFromRiver = 5
	
	local maxPalmSlope = 0.2
	
	local layerBeach_gain = 1.2
	local layerBeach_lacunarity = 10.5
	
	local beachNoiseOffset = -0.3
	
	-- Stones on beach
	local layerBeach_maxDistance = 20
	
	-- #################
	-- #### NO WATER
	if config.humidity == 0 then
		local forestMap = mkTemp:Get()
		local rocksMap = mkTemp:Get()
		layers:Constant(forestMap, 0)
		layers:Constant(rocksMap, -1)
		return forestMap, treesMapping, rocksMap, assetsMapping
	end
	
	-- #################
	-- #### LEVEl 0 - scattered trees
	local tempMap = mkTemp:Get()
	layers:Map(heightMap, tempMap, {40, 100}, {singleTreeDensity, 0}, true)
	layers:WhiteNoiseNonuniform(tempMap, tempMap)
	
	-- #################
	-- #### LEVEL 1 - plains
	-- Background noise (permeability)
	-- Impermeable rivers
	local probabilityMap = mkTemp:Get()
	if config.noWater then
		layers:Constant(probabilityMap, permeability * 0.5)
	else
		layers:Map(distanceMap, distanceMap, {0, 500}, {0, 500}, true)

		layers:Pwlerp(distanceMap, probabilityMap,
			{-5, 0, 0.1, treeDistanceFromRiver, 300.1},
			{0, 0, 0.7 * permeability, permeability, permeability}
		)
	end
	-- Variance in size
	
	local yMap = mkTemp:Get()
	layers:PerlinNoise(yMap, {})
	
	layers:Map(yMap, yMap, {0, 2.5}, {1.0, permeabilityVariance}, true)
	layers:Mul(probabilityMap, yMap, probabilityMap)
	
	-- Generate permeability
	layers:WhiteNoiseNonuniform(probabilityMap, probabilityMap)
	
	-- Seeds
	if config.noWater then
		layers:Constant(yMap, 2*seedDensity)
	else
		layers:Pwlerp(distanceMap, yMap,
			{-5, 0, 0.1, 200.1, 300.1},
			{0, 0, 2*seedDensity, seedDensity, seedDensity}
		)
	end
	
	local forestMap = mkTemp:Get()
	layers:WhiteNoiseNonuniform(yMap, forestMap)
	yMap = mkTemp:Restore(yMap)
	
	-- Invert seeds  for input in percolation
	layers:Map(forestMap, forestMap, {0, 1}, {0, -1})
	
	-- Percolate
	layers:Percolation(probabilityMap, forestMap, forestMap, {
		noiseThreshold = 0.5,
		seedThreshold = -0.5,
		maxCluster = 333,
	})
	-- Embiggen
	layers:Distance(forestMap, forestMap)
	layers:Map(heightMap, probabilityMap, {20, 40}, {1, 100}, true)
	
	layers:Add(probabilityMap, forestMap, forestMap)
	
	layers:Pwconst(forestMap, forestMap, {10}, {1, 0})
	
	-- Reduce density and select trees
	local ditheringMap = mkTemp:Get()
	layers:Dithering(ditheringMap, "LOCAL")
	layers:Pwconst(ditheringMap, probabilityMap, plainForestDist, plainForestTypes)
	
	layers:Mul(forestMap, probabilityMap, forestMap)
	
	-- #################
	-- #### LEVEL 0 AND 1 MIX
	layers:Map(tempMap, tempMap, {0, 1}, {0, anyTree}, true)
	
	-- Scattered trees
	layers:Mask(tempMap, tempMap, forestMap)

	-- SLOPE CUTOFF
	local slopeMap = mkTemp:Get()
	layers:Grad(heightMap, slopeMap, 2)
	
	layers:Pwconst(slopeMap, tempMap, {maxSlope}, {1, 0})

	-- #################
	-- #### LEVEL 3 : Hill Trees
	-- Cutoff from above and below
	layers:Pwlerp(heightMap, probabilityMap,
		{0, hillsMiddleLimit, hillsHighLimit, hillsHighLimit + 40},
		{hillDensityBase, hillDensityBase, 0, 0}
	)
	
	layers:Pwlerp(ridgesMap, ridgesMap,
		{0, hillsLowLimit, hillsMiddleLimit, hillsMiddleLimit + 40},
		{0, 0, 1, 1}
	)
	
	layers:Mul(ridgesMap, probabilityMap, probabilityMap)
	
	-- Transition
	layers:WhiteNoiseNonuniform(probabilityMap, probabilityMap)
	
	do
		local xtMap = mkTemp:Get()
		layers:Mul(tempMap, probabilityMap, xtMap)
		
		-- Add and distribute forest
		layers:Pwconst(ditheringMap, probabilityMap, hillForestDist, hillForestTypes)
		layers:Mask(xtMap, probabilityMap, forestMap)
		xtMap = mkTemp:Restore(xtMap)
	end
	
	-- #################
	-- #### BEACH TREES
	layers:RidgedNoise(tempMap, { octaves = 3, lacunarity = layerBeach_lacunarity, frequency = 1.0 / 1000.0, gain = layerBeach_gain})
	
	layers:Map(tempMap, tempMap, {-1 + beachNoiseOffset, 1 + beachNoiseOffset}, {0, 1})
	
	layers:Pwlerp(distanceMap, probabilityMap, {0, 5, 200, 220}, {0, 1, 0, 0})
	
	local hmCutoff = mkTemp:Get()
	layers:Pwconst(heightMap, hmCutoff, {0.4, 15}, {0, 1, 0})
	layers:Mul(probabilityMap, hmCutoff, probabilityMap)
	hmCutoff = mkTemp:Restore(hmCutoff)
	
	layers:Mul(tempMap, probabilityMap, tempMap)
	
	layers:Pwconst(slopeMap, slopeMap, {maxPalmSlope}, {1, 0})
	
	layers:Mul(tempMap, slopeMap, tempMap)
	
	slopeMap = mkTemp:Restore(slopeMap)
	
	layers:Pwconst(ditheringMap, probabilityMap, palmBeachSteps, palmBeachTypes)
	ditheringMap = mkTemp:Restore(ditheringMap)
	
	layers:Mask(tempMap, probabilityMap, forestMap, 0.5, "GREATER")
	local probabilityMap = mkTemp:Restore(probabilityMap)
	
	-- #################
	-- #### ROCKS
	layers:WhiteNoise(tempMap, 0.005)
	
	local tmpRocksMap = mkTemp:Get()
	layers:Map(distanceMap, tmpRocksMap, { 0, layerBeach_maxDistance }, { 3.3, 0}, true)
	
	local tmpNoise2Map = mkTemp:Get()
	layers:RidgedNoise(tmpNoise2Map, {
		octaves = 3,
		lacunarity = 10.5,
		frequency = 1.0 / 1000.0,
		gain = layerBeach_gain,
	})
	
	layers:Map(tmpNoise2Map, tmpNoise2Map, { 0.2, 0.8 }, { -1, 1}, true)
	
	layers:Add(tmpRocksMap, tmpNoise2Map, tmpRocksMap)
	
	layers:Map(distanceMap, tmpNoise2Map, { 0, layerBeach_maxDistance * 2 }, { 2.0, 0}, true)
	
	layers:Mul(tmpNoise2Map, tmpRocksMap, tmpRocksMap)
	
	tmpNoise2Map = mkTemp:Restore(tmpNoise2Map)
	layers:Mul(tmpRocksMap, distanceMap, tmpRocksMap)
	
	local tmpNoise3Map = mkTemp:Get()
	
	layers:WhiteNoise(tmpNoise3Map, 0.1)
	layers:Mul(tmpNoise3Map, tmpRocksMap, tmpRocksMap)
	
	local rocksMap = mkTemp:Get()
	layers:Add(tmpRocksMap, tempMap, rocksMap)
	
	tmpRocksMap = mkTemp:Restore(tmpRocksMap)
	layers:Pwconst(rocksMap, rocksMap, {0.5}, {0, 1})
	
	layers:Distance(heightMap, distanceMap)
	layers:Pwconst(distanceMap, tmpNoise3Map, {5, 200}, {0, 1, 2})
	
	layers:Mul(tmpNoise3Map, rocksMap, rocksMap)
	
	tmpNoise3Map = mkTemp:Restore(tmpNoise3Map)
	layers:Mask(heightMap, tempMap, rocksMap, 0.0, "LESS")
	
	local tempMap = mkTemp:Restore(tempMap)
			
	return forestMap, treesMapping, rocksMap, assetsMapping
end

return data
