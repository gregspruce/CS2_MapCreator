local data = {}

data.Make = function(layers, humidity, ridgesMap, distanceMap, probabilityMap, tempMap, forestMap, rocksMap)
	local conifer = 1
	local shrub = 2
	local hills = 3
	local broadleaf = 4
	local river = 5
	local plains = 6
	local anyTree = 255
	
	local treesMapping = {
		[hills] = "hills",
		[conifer] = "conifer",
		[shrub] = "shrub",
		[broadleaf] = "broadleaf",
		[river] = "river",
		[plains] = "plains",
		[anyTree] = "single",
	}
	
	if humidity == 0 then
		layers:Constant(forestMap, 0)
		layers:Constant(rocksMap, -1)
		return
	end
	
	local coniferLimit = 100
	local treeLimit = 200
	local l = 0.6

	-- LEVEl 0 - scattered trees
	layers:Map(ridgesMap, tempMap, {40, 100}, {0.002, 0})
	layers:WhiteNoiseNonuniform(tempMap, tempMap)
	
	-- LEVEL 1 - plains
	-- Background noise
	layers:WhiteNoise(probabilityMap, 0.51 + math.sqrt(humidity) * 0.12 - 0.19)
	
	-- Seeds
	layers:WhiteNoise(forestMap, 0.00008 - 0.0001 * humidity * humidity + 0.0001)
	
	-- Invert seeds  for input in percolation
	layers:Map(forestMap, forestMap, {0, 1}, {0, -1})
	
	-- Percolate
	layers:Percolation(probabilityMap, forestMap, forestMap, {
		noiseThreshold = 0.5,
		seedThreshold = -0.5,
		maxCluster = 333,
	})
	
    -- Embiggen
	layers:Map(forestMap, forestMap, {0, 1}, {1, 0}, false)
	layers:Distance(forestMap, forestMap)
	
	layers:Map(ridgesMap, probabilityMap, {20, 40}, {1, 100}, true)
	
	layers:Add(probabilityMap, forestMap, forestMap)
	
    layers:Pwlerp(forestMap, forestMap, {0, 10, 10.1, 20}, {broadleaf, broadleaf, 0, 0})
    -- Reduce density
	layers:WhiteNoise(probabilityMap, 0.6)
	
	layers:Mul(probabilityMap, forestMap, forestMap)
    
    -- LEVEL 0 AND 1 MIX
    layers:Map(tempMap, tempMap, {0, 1}, {0, broadleaf}, true)
	
	layers:Add(forestMap, tempMap, forestMap)
	
	-- LEVEL 3 : Trees
	-- SLOPE CUTOFF
	layers:Grad("HM", tempMap, 2)
	
	layers:Pwlerp(tempMap, tempMap, {0, 1, 1, 4}, {1, 1, 0, 0})
	
	-- HEIGHT CUTOFF
	layers:Pwlerp(ridgesMap, "CUTOFF",
		 {0, coniferLimit, coniferLimit + 0.1, treeLimit, treeLimit + 0.1, treeLimit + 20},
         {0, 0, 1, 1, 0, 0}
    )
	-- EDGE DETECTIION
	layers:Laplace("HM", rocksMap)
	
    layers:Pwlerp(rocksMap, rocksMap,
		{-3, -l-0.1, -l, l, l+0.1, 3},
        {conifer, conifer, 0, 0, conifer, conifer}
	)
	-- BLEND SLOPE, HEIGHT AND RIDGE
	layers:Mul(rocksMap, "CUTOFF", rocksMap)
	layers:Mad(rocksMap, tempMap, forestMap)
	
	-- ROCKS
	layers:WhiteNoise(rocksMap, 0.001)

	return treesMapping
end

return data