local data = {}
				
data.Make = function(layers, mkTemp, config, heightMap, ridgesAndMesaMap, mesaMap, ridgesMap, canyonCutoffMap, distanceMap)
	-- PARAMS
	-- Rock types
	local sandstone = 1
	local granite = 2
	local desert_rock = 3
	local savanna_rock = 4
	local hf = 10 -- offset for granite

	local assetsMapping = {
		[sandstone] = "sandstone",
		[granite] = "desert_rock",
		[desert_rock] = "desert_rock",
		[savanna_rock] = "savanna_rock",
		[sandstone + hf] = "granite",
		[granite + hf] = "granite",
		[desert_rock + hf] = "granite",
		[savanna_rock + hf] = "granite",
	}
	-- Tree types
	local forest = 1
	local cactus = 2
	local shrub = 3
	local broadleaf = 4
	local desert = 6
	local savanna = 7
	local canyon_shrub = 8
	local mesa_shrub = 9
	local ridge_shrub = 10
	local anyTree = 255
	
	local treesMapping = {
		[forest] = "forest",
		[cactus] = "cactus",
		[shrub] = "shrub",
		[broadleaf] = "broadleaf",
		[savanna] = "savanna_shrub",
		[desert] = "desert_shrub",
		[canyon_shrub] = "canyon_shrub",
		[mesa_shrub] = "mesa_shrub",
		[ridge_shrub] = "ridge_shrub",
		[anyTree] = "all",
	}
	
	if config.humidity == -1 then
		local forestMap = mkTemp:Get()
		local rocksMap = mkTemp:Get()
		layers:Constant(forestMap, 0)
		layers:Constant(rocksMap, -1)
		return forestMap, treesMapping, rocksMap, assetsMapping
	end
	
	-- Global settings
	local mesaHeightStart = 85
	local mesaHeightEnd = 110
	local mesaHeightMidPoint = 0.2
	local mesaHeightMidPointValue = 0.7
	local ridgeHeightStart = 160
	local ridgeHeightEnd = 190
	local treeLimitStart = 240
	local treeLimitEnd = 290
	
	-- Slopes
	local maxRiverSlope = 0.5
	local maxHillSlope = 0.6
	
	-- Heights
	local hillsLowLimit = 20 -- relative [m]
	local hillsHighLimit = 80 -- relative [m]
	
	local coniferLimit = 70 -- relative [m]
	local treeLimit = 200 -- absolute [m]

	local coniferTransitionLow = 30 -- transition size [m]
	local coniferTransitionHigh = 30 -- transition size [m]

	-- LEVEL -1: Scattered trees
	local scatteredTreesProbability = 0.002
	
	-- LEVEL 1a and 1b: Plain trees seed density
	local plainForestBaseDensity = 0.75 -- reduce to reduce density of forest
	local plainTreesHeightCutoffStart = mesaHeightStart
	local plainTreesHeightCutoffEnd = mesaHeightEnd
	local plainTreesSlopeCutoff = 0.6
	
	local savannaTreeCutoff = 0.1 + 0.3 * config.humidity -- savanna shrub area size
	local savannaTreesDist = { 0.95 + config.humidity * 0.05 } -- savanna shrub density (1 = zero, 0 = full)
	local savannaTreesTypes = { 0, savanna }
	local savannaRockDensity = 0.01 -- notice trees override rocks, density might be lower
	local desertTreeCutoff = 0.3 + 0.1 * config.humidity -- desert shrub area size
	local desertTreesDist = { 0.3 + config.humidity * 0.05 } -- desert shrub density (0 = zero, 1 = full)
	local desertTreesTypes = { 0, desert }
	local desertRockDensity = 0.6 -- notice trees override rocks, density might be lower
	
	-- LEVEL 0: River trees
	local treeMaxDistanceFromRiver = 400
	local treePremeabilityDecayFromRiver = 20
	local treeMinDistanceFromRiver = 20
	local startPermeability = 0.62
	local maxPermeability = 0.61
	local seedDensity = 0.003 - 0.0001 * config.humidity * config.humidity
	local seedDensity2 = 0.002 - 0.0001 * config.humidity * config.humidity
		
	local riverTreeDensity = 0.3
	
	local riverTree1Dist = {0.5, 0.6}
	local riverTree1Type = {0, cactus, forest}
	local riverTree2Dist = {0.5, 0.6}
	local riverTree2Type = {0, cactus, shrub}
	local canyonTree2Dist = {0.5}
	local canyonTree2Type = {0, canyon_shrub}
	
	local noiseParam = {
		frequency = 1 / 1000,
		lowerCutoff = 0.3,
		upperCutoff = 0.5,
	}
	-- Canyon trees
	local canyonTreesDistanceMin = 15
	local canyonTreesDistanceMax = 30

	-- LEVEL 2: Hill trees
	local treeHillsLowDensity = 0.7 -- density in lower layer
	local treeHillsHighDensity = 0.4 -- density in upper layer
	local hillsBroadleavesRatio = .5
	
	local treeHillsDist = {0.6, 0.7}
	local treeHillsTypes = {0, cactus, broadleaf}
	
	-- LEVEL 3: extra shrubs on top of mesas
	local mesaTopTree1Dist = {0.8}
	local mesaTopTree1Type = {0, mesa_shrub}
	local mesaTopTreeDensity = 0.8
	
	-- LEVEL 4: extra shrubs on top of rodges
	local sandstoneHeightLimit = 125
	
	local ridgeTopTree1Dist = {0.6}
	local ridgeTopTree1Type = {0, ridge_shrub}
	local ridgeTopTreeDensity = 0.8
	
	-- River bank
	local layerRiverBank_maxDistance = 20
	local layerRiverBank_gain = 1.2
	local layerRiverBank_density = 3.3
	
	-- PRECOMPUTATIONS
	local tempMap = mkTemp:Get()
	layers:WhiteNoise(tempMap, scatteredTreesProbability)
	
	layers:Map(tempMap, tempMap, {0, 1}, {0, anyTree},  true)
	
	-- Precompute SLOPE CUTOFF
	local slopeMap = mkTemp:Get()
	layers:Grad(heightMap, slopeMap, 2)
	
	-- LEVEL 1a - plains: savanna and desert mix
	-- Same noise as color
	local abNoiseMap = mkTemp:Get()
	layers:RidgedNoise(abNoiseMap, { octaves = 4, frequency = 1.0 / 1200.0, lacunarity = 4.5, gain = 0.9})
	
	local ditheringMap = mkTemp:Get()
	layers:Dithering(ditheringMap, "LOCAL")
	
	-- CUTOFF
	-- Reduce density
	local maskMap = mkTemp:Get()
	do -- mask
		-- Cutoff height
		local tmMap = mkTemp:Get()
		layers:Pwlerp(heightMap, tmMap, { plainTreesHeightCutoffStart - 10, plainTreesHeightCutoffStart, plainTreesHeightCutoffEnd, plainTreesHeightCutoffEnd + 10 }, {1, 1, 0, 0})
		layers:WhiteNoiseNonuniform(tmMap, maskMap)
		layers:Map(tmMap, maskMap, {0, 1}, {0, plainForestBaseDensity})
		
		-- Cutoff slope
		layers:Pwconst(slopeMap, tmMap, { plainTreesSlopeCutoff }, {1, 0})
		layers:Mul(tmMap, maskMap, maskMap)
		layers:Mul(canyonCutoffMap, maskMap, maskMap)
		mkTemp:Restore(tmMap)
	end -- mask is a masked dither
	
	local forestMap = mkTemp:Get()
	local rocksMap = mkTemp:Get()
	layers:WhiteNoise(rocksMap, 0.005)
	do -- mix
		local cutoffMap = mkTemp:Get()
		local typesMap = mkTemp:Get()
		local wnMaskMap = mkTemp:Get()
		local wnMap = mkTemp:Get()
		layers:Copy(maskMap, wnMaskMap)
		layers:Mul(ditheringMap, maskMap, maskMap)

		layers:Map(abNoiseMap, cutoffMap, { 0.25, 0.7 }, {0, 1}, true)
		layers:Pwconst(cutoffMap, cutoffMap, { 1 - desertTreeCutoff }, {0, 1})
		layers:Pwconst(maskMap, typesMap, desertTreesDist, desertTreesTypes)
		layers:Mul(cutoffMap, typesMap, forestMap)
		--- rocks
		layers:WhiteNoise(wnMap, desertRockDensity)
		layers:Mul(wnMaskMap, wnMap, wnMap)
		layers:Mul(cutoffMap, wnMap, wnMap)
		layers:Pwconst(wnMap, wnMap, {0.5}, {0, desert_rock})
		layers:Mask(wnMap, wnMap, rocksMap)
		
		layers:Map(abNoiseMap, cutoffMap, { 0.25, 0.7 }, {0, 1}, true)
		layers:Pwconst(cutoffMap, cutoffMap, { savannaTreeCutoff }, {1, 0})
		layers:Pwconst(maskMap, typesMap, savannaTreesDist, savannaTreesTypes)
		layers:Mul(cutoffMap, typesMap, typesMap)
		layers:Mask(typesMap, typesMap, forestMap)
		-- rocks
		layers:WhiteNoise(wnMap, savannaRockDensity)
		layers:Mul(wnMaskMap, wnMap, wnMap)
		layers:Mul(cutoffMap, wnMap, wnMap)
		layers:Pwconst(wnMap, wnMap, {0.5}, {0, savanna_rock})
		layers:Mask(wnMap, wnMap, rocksMap)
		
		mkTemp:Restore(typesMap)
		mkTemp:Restore(cutoffMap)
		mkTemp:Restore(wnMap)
		mkTemp:Restore(wnMaskMap)
	end
	maskMap = mkTemp:Restore(maskMap)
	
	-- LEVEL 1 MIX
	layers:Mask(tempMap, tempMap, forestMap)

	-- Slope cutoff
	local slopeCutoffMap = mkTemp:Get()
	layers:Pwconst(slopeMap, slopeCutoffMap, {maxRiverSlope}, {1, 0})
	local slopeCutoff2Map = mkTemp:Get()
	layers:Pwconst(slopeMap, slopeCutoff2Map, {maxHillSlope}, {1, 0})
	slopeMap = mkTemp:Restore(slopeMap)

	-- LEVEL 2 : Hill Trees
	-- Cutoff from above and below
	do
		-- Transition
		local M = mkTemp:Get()
		layers:RidgedNoise(M, { octaves = 5, frequency = 1.0 / 2200.0, lacunarity = 2.5, gain = 25.9})
		
		layers:Map(M, M, {0, 1}, {0, 8}, false)
		layers:Add(ridgesMap, M, tempMap)
		layers:Add(heightMap, M, M)
		layers:Pwconst(tempMap, tempMap, {hillsLowLimit, hillsHighLimit}, {0, 1, 0})
		local probabilityMap = mkTemp:Get()
		layers:Map(M, probabilityMap, {hillsLowLimit, hillsHighLimit}, {treeHillsLowDensity, treeHillsHighDensity}, true)
		M = mkTemp:Restore(M)
		layers:WhiteNoiseNonuniform(probabilityMap, probabilityMap, 0.6)
		
		layers:Mul(slopeCutoff2Map, probabilityMap, probabilityMap)
		slopeCutoff2Map = mkTemp:Restore(slopeCutoff2Map)
		
		layers:Mul(tempMap, probabilityMap, probabilityMap)
		
		-- ADD BROADLEAVES
		layers:Pwconst(ditheringMap, tempMap, treeHillsDist, treeHillsTypes)
		
		layers:Mask(probabilityMap, tempMap, forestMap)
		
		probabilityMap = mkTemp:Restore(probabilityMap)
		tempMap = mkTemp:Restore(tempMap)
	end

	-- LEVEL 0: river trees
	local probabilityMap = mkTemp:Get()
	if not config.noWater then 
		local xMap = mkTemp:Get()
		local yMap = mkTemp:Get()
		layers:Pwconst(canyonCutoffMap, canyonCutoffMap, {0.4}, {0, 1})
	
		-- Prepare permeability
		-- Impermermeable river
		layers:Pwconst(distanceMap, xMap, {treeMinDistanceFromRiver}, {0, 1})
		-- Impermeable slope
		layers:Mul(xMap, slopeCutoffMap, xMap)
		-- Less perm at distance
		layers:Pwlerp(distanceMap, yMap, 
			{0, treePremeabilityDecayFromRiver, treeMaxDistanceFromRiver, treeMaxDistanceFromRiver+20}, 
			{startPermeability, maxPermeability, 0, 0}
		)
		layers:Mul(xMap, yMap, xMap) -- MASK and fading permeability probabiltiy
		
		layers:WhiteNoiseNonuniform(xMap, xMap)
		layers:SetSeed(math.random() * 10000)
		-- Invert white noise for input in percolation
		layers:Map(xMap, xMap, {0, 1}, {1, 0}, true)
		
		-- Type 2: prepare
		-- Seeds
		layers:Pwconst(ditheringMap, yMap, {1 - seedDensity2}, {0, -1})
	
		layers:Percolation(xMap, yMap, probabilityMap, {
			seedThreshold = -0.5, -- if seedsmap < seedThresold then is seed
			noiseThreshold = 0.5, -- if permmap < noiseThreshold then impermeable otherwise permeable
			maxCluster = 40000,
		})
		
		-- Type 2
		local zMap = mkTemp:Get()
		layers:Pwconst(ditheringMap, zMap, riverTree2Dist, riverTree2Type)
		layers:Mul(canyonCutoffMap, probabilityMap, probabilityMap)
		layers:Mask(probabilityMap, zMap, yMap)
		
		layers:Mask(yMap, yMap, forestMap, 0, "GREATER")
		
		mkTemp:Restore(zMap)
		mkTemp:Restore(yMap)
		
		-- Canyon inner vegetation (type 2)
		layers:Map(canyonCutoffMap, canyonCutoffMap, {0, 1}, {1, 0}, true)
		
		local yMap = mkTemp:Get()
		
		local distanceMask = mkTemp:Get()
		
		layers:RidgedNoise(distanceMask, { octaves = 3, frequency = 1.0 / 2200.0, lacunarity = 3.5, gain = 2.9})
		
		layers:Add(distanceMap, distanceMask, distanceMask)
		layers:Pwconst(distanceMask, distanceMask, {canyonTreesDistanceMin, canyonTreesDistanceMax}, {0, 1, 0}, true)
		layers:Mul(canyonCutoffMap, distanceMask, canyonCutoffMap)
		distanceMask = mkTemp:Restore(distanceMask)
		
		layers:Pwconst(ditheringMap, yMap, canyonTree2Dist, canyonTree2Type)
		layers:Mask(canyonCutoffMap, yMap, forestMap, 0, "GREATER")
		
		-- Seeds
		layers:Pwconst(ditheringMap, yMap, {seedDensity}, {-1, 0})
	
		layers:Percolation(xMap, yMap, probabilityMap, { -- perm, seeds, output
			noiseThreshold = 0.5, -- if permmap < noiseThreshold then impermeable otherwise permeable
			seedThreshold = -0.5, -- if seedsmap < seedThresold then is seed
			maxCluster = 40000,
		})
		
		-- Type 1: add	
		layers:Pwconst(ditheringMap, yMap, riverTree1Dist, riverTree1Type)
		layers:Mask(probabilityMap, yMap, forestMap)
		
		mkTemp:Restore(yMap)
		canyonCutoffMap = mkTemp:Restore(canyonCutoffMap)
	end
	local probabilityMap = mkTemp:Restore(probabilityMap)
	
	do
		-- LEVEL 3: shrubs on top of mesa/canyon/ridges
		local mesaMap2 = mkTemp:Get()
		layers:Pwlerp(heightMap, mesaMap2, 
			{mesaHeightStart - 10, mesaHeightStart, (mesaHeightStart * (1 - mesaHeightMidPoint) + mesaHeightMidPoint * mesaHeightEnd), 
				mesaHeightEnd, ridgeHeightStart, ridgeHeightEnd, ridgeHeightEnd + 10}, 
			{0, 0.0, mesaHeightMidPointValue, 1.0, 1.0, 0.0, 0.0}
		)
		local noiseMap = mkTemp:Get()
		layers:Map(abNoiseMap, noiseMap, {0.2, 1.0}, {1.0, 0.0}, true)
		abNoiseMap = mkTemp:Restore(abNoiseMap)
		
		layers:Mul(noiseMap, slopeCutoffMap, noiseMap)
		do 
			local tempMap = mkTemp:Get()

			layers:Pwconst(noiseMap, tempMap, mesaTopTree1Dist, mesaTopTree1Type)
			
			local maskMap = mkTemp:Get()
			layers:Mul(ditheringMap, mesaMap2, maskMap)
			layers:Pwconst(maskMap, maskMap, {mesaTopTreeDensity }, {0, 1})
			layers:Mask(maskMap, tempMap, forestMap)
			maskMap = mkTemp:Restore(maskMap)
			mkTemp:Restore(tempMap)
		end
		-- LEVEL 4: shrubs on top of ridges
		layers:Pwlerp(heightMap, mesaMap2, {ridgeHeightStart - 10, ridgeHeightStart, ridgeHeightEnd, 
			treeLimitStart, treeLimitEnd, treeLimitEnd+10},
			{0.0, 0.0, 1.0, 1.0, 0.0, 0.0}, true)
		do 
			local tempMap = mkTemp:Get()

			layers:Pwconst(noiseMap, tempMap, ridgeTopTree1Dist, ridgeTopTree1Type)
			noiseMap = mkTemp:Restore(noiseMap)
			
			local maskMap = mkTemp:Get()
			layers:Mul(ditheringMap, mesaMap2, maskMap)
			layers:Pwconst(maskMap, maskMap, {ridgeTopTreeDensity}, {0, 1})
			ditheringMap = mkTemp:Restore(ditheringMap)
			
			layers:Mask(maskMap, tempMap, forestMap)
			maskMap = mkTemp:Restore(maskMap)
			mkTemp:Restore(tempMap)
		end
		local mesaMap2 = mkTemp:Restore(mesaMap2)
	end
	
	local slopeCutoffMap = mkTemp:Restore(slopeCutoffMap)

	-- ROCKS - Stones on river bank
	local tempRocksMap = mkTemp:Get()
	layers:Map(distanceMap, tempRocksMap, { 0, layerRiverBank_maxDistance }, { layerRiverBank_density, 0}, true)
	
	local noise2Map = mkTemp:Get()
	layers:RidgedNoise(noise2Map, { octaves = 3, lacunarity = 10.5, frequency = 1.0 / 1000.0, gain = layerRiverBank_gain})
	
	layers:Map(noise2Map, noise2Map, { 0.2, 0.8 }, { -1, 1}, true)
	
	layers:Add(tempRocksMap, noise2Map, tempRocksMap)
	
	layers:Map(distanceMap, noise2Map, { 0, layerRiverBank_maxDistance * 2 }, { 2.0, 0}, true)
	
	layers:Mul(noise2Map, tempRocksMap, tempRocksMap)
	noise2Map = mkTemp:Restore(noise2Map)
	
	layers:Mul(tempRocksMap, distanceMap, tempRocksMap)
	layers:Pwconst(tempRocksMap, tempRocksMap, {0.5}, {0, 1})
	
	do
		local noise3Map = mkTemp:Get()
		layers:WhiteNoise(noise3Map, 0.25)
		layers:Mul(noise3Map, tempRocksMap, tempRocksMap)
		mkTemp:Restore(noise3Map)
	end
	
	layers:Add(tempRocksMap, rocksMap, rocksMap)
	tempRocksMap = mkTemp:Restore(tempRocksMap)
	
	do
		local tempMap = mkTemp:Get()
		layers:Pwconst(ridgesAndMesaMap, tempMap, {sandstoneHeightLimit}, {0, hf})
		
		layers:Add(rocksMap, tempMap, rocksMap)
		mkTemp:Restore(tempMap)
	end
	
	do
		local tempMap = mkTemp:Get()
		layers:Pwconst(distanceMap, tempMap, {1}, {0, 1})
		layers:Mul(tempMap, rocksMap, rocksMap)
		layers:Mul(tempMap, forestMap, forestMap)
		
		mkTemp:Restore(tempMap)
	end
	
	return forestMap, treesMapping, rocksMap, assetsMapping
end

return data