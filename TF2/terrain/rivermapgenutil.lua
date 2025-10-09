require "math"
local vec2 = require "vec2"

local data = {}

function data.MakeEmpty() 
	return {
		points = {},
		widths = {},
		depths = {},
		
		tangents = {},
		widthTangents = {},
		depthTangents = {},
		
		features = {},
		feeders = {},
	}
end

function data.MakeSubdivision(river, subdivideConfig) 
	local newRiver = data.MakeEmpty()
	
	local nSegments = subdivideConfig.nSegments
	
	for i = 1, #river.points - 1 do
		table.insert(newRiver.points, river.points[i])
		table.insert(newRiver.tangents, vec2.div(river.tangents[i], nSegments))
		table.insert(newRiver.depths, river.depths[i])
		table.insert(newRiver.depthTangents, river.depthTangents[i])
		table.insert(newRiver.widths, river.widths[i])
		table.insert(newRiver.widthTangents, river.widthTangents[i])
		table.insert(newRiver.feeders, river.feeders[i] or -1)
		table.insert(newRiver.features, river.features[i] or {})
	
		for j = 1, nSegments - 1 do
			local h = j / nSegments 
			
			local newPoint = vec2.herp(river.points[i], river.points[i+1], river.tangents[i], river.tangents[i+1], h)
			local newTangent = vec2.div(vec2.herpPrime(river.points[i], river.points[i+1], river.tangents[i], river.tangents[i+1], h), nSegments)
			local newDepth = math.lerp(river.depths[i], river.depths[i+1], h)
			local newDepthTangent = math.lerp(river.depthTangents[i], river.depthTangents[i+1], h)
			local newWidth = vec2.lerp(river.widths[i], river.widths[i+1], h)
			local newWidthTangent = vec2.lerp(river.widthTangents[i], river.widthTangents[i+1], h)
		
			table.insert(newRiver.points, newPoint)
			table.insert(newRiver.tangents, newTangent)
			table.insert(newRiver.depths, newDepth)
			table.insert(newRiver.depthTangents, newDepthTangent)
			table.insert(newRiver.widths, newWidth)
			table.insert(newRiver.widthTangents, newWidthTangent)
			table.insert(newRiver.feeders, -1)
			table.insert(newRiver.features, {})
		end
	end
	
	table.insert(newRiver.points, river.points[#river.points])
	table.insert(newRiver.tangents, vec2.div(river.tangents[#river.points], nSegments))
	table.insert(newRiver.depths, river.depths[#river.points])
	table.insert(newRiver.depthTangents, river.depthTangents[#river.points])
	table.insert(newRiver.widths, river.widths[#river.points])
	table.insert(newRiver.widthTangents, river.widthTangents[#river.points])
	table.insert(newRiver.feeders, river.feeders[#river.points] or -1)
	table.insert(newRiver.features, #river.points or {})
	
	return newRiver
end

function data.MakeLake(river, lakeConfig)
	local lake = false
	local lakeSize = 0
	local i = 4
	while i <= #river.points - 1 do
		local j = i
		local lakeStart = -1
		local lakeEnd = -1
		while j <= #river.points - 1 do
			local prob = lakeConfig.probability(river.points[j])
			if lake then
				if river.feeders[j] ~= nil and river.feeders[j] >= 0 or (1 - prob) > lakeConfig.endProbability(lakeSize) then
					lake = false
					lakeEnd = j
					break
				else 
					river.features[j].lake = true
					lakeSize = lakeSize + 1
				end
			end
			if not lake then
				if (river.feeders[j] == nil or river.feeders[j] < 0) and prob > lakeConfig.startProbability() then
					river.features[j].lake = true
					lake = true
					lakeStart = j
					lakeSize = 0
				end
				-- math.random()
			end
			j = j+1
		end
		if lakeStart >= 0 then 
			for k = lakeStart, lakeEnd do
				local s = math.mapClamp((k - lakeStart) / (lakeEnd - lakeStart), 1, 0, 1, -1)
				river.widths[k], river.depths[k] = lakeConfig.makeProfile(s)
			end
		end
		
		i = i+j
	end
end

function data.MakeCurve(river, curveConfig)
	local sign = 1
	local baseStr = curveConfig.baseStrength
	
	local lakeDist = 0
	for i = 1, #river.points - 1 do
		if river.features[i].lake or (river.feeders[i] and river.feeders[i] >= 0) or i < 2 then 
			river.features[i].lakeDist = 0
			lakeDist = 0
		else
			lakeDist = lakeDist + 1
			river.features[i].lakeDist = lakeDist
		end
	end
	lakeDist = 100
	for i = #river.points - 1, 1, -1 do
		if river.features[i].lake or (river.feeders[i] and river.feeders[i] >= 0) or i < 2 then 
			river.features[i].lakeDist = 0
			lakeDist = 0
		else
			lakeDist = lakeDist + 1
			river.features[i].lakeDist = math.min(river.features[i].lakeDist, lakeDist)
		end
	end
	
	for i = 1, #river.points - 1 do
		if river.feeders[i] < 0 and not river.features[i].lake then
			local cr = curveConfig.getCurviness(river.points[i])
			local tg = river.tangents[i]
			local str = baseStr * cr * math.randf(0.8, 1.2) * math.mapClamp(river.features[i].lakeDist, 1, 5, 0, 1)
			local of = str * math.randf(-0.2, 0.2) + (1 - str) * 0.8
			local nrml = vec2.new(-sign * str * tg.y, sign * str * tg.x)
			nrml = vec2.add(nrml, vec2.mul(of, tg))
			river.tangents[i] = nrml
			sign = -sign
			--if river.features[i].lakeDist > 1 then river.widths[i] = vec2.new(1, 1) end
		end
		river.widths[i] = vec2.mul(curveConfig.getWidthMultiplier(river.points[i]), river.widths[i])
	end
end

function data.AdjustFeeder(river, rivers, adjustConfig) 
	for i = 1, #river.points do
		local feeder = river.feeders[i]
		if feeder >= 0 then
			local d = river.depths[i]
			for j = 1, 3 do
				rivers[feeder].depths[i] = d
			end
		end
	end
end

function data.Subdivide(rivers, subdivideConfig) 
	for k, river in pairs(rivers) do
		rivers[k] = data.MakeSubdivision(river, subdivideConfig)
	end
end

function data.MakeLakes(rivers, lakeConfig) 
	for k, river in pairs(rivers) do
		data.MakeLake(river, lakeConfig)
	end
end

function data.MakeCurves(rivers, curveConfig) 
	for k, river in pairs(rivers) do
		data.MakeCurve(river, curveConfig)
	end
end

function data.AdjustFeeders(rivers, adjustConfig) 
	for k, river in pairs(rivers) do
		data.AdjustFeeder(river, rivers, adjustConfig)
	end
end

return data