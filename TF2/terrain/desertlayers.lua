local data = {}
				
function data.MakeCanyonLayer(layers, tmpMkr, config, canyonMap, distanceMap, addTo)
	local t1 = tmpMkr:Get()
	layers[#layers + 1] = {
		type = "FEATURE",
		params = {
			type = "RIDGED_NOISE",
			output = t1,
			params = {
				type = "2",
				numOctaves = 1,
				frequency = 1.0 / 400.0,
				lacunarity = 4.5,
				gain = 0.3,
				warp = .15,
			}
		}
	}		
	layers:Map(t1, t1, {0, 1}, {-0.3, 0.6}, false)
	
	local t2 = tmpMkr:Get()
	layers:Pwlerp(distanceMap, t2 , {0, 50, 100, 200}, {0, 0, 1, 1})
	
	layers:Mul(t2 , t1, t1)
	
	layers:Mul(distanceMap, t1, t1)
	
	layers[#layers + 1] = {
		type = "FEATURE",
		params = {
			type = "RIDGED_NOISE",
			output = t2,
			params = {
				type = "2",
				numOctaves = 4,
				frequency = 1.0 / 5000.0,
				lacunarity = 3.8,
				gain = 1.2,
				warp = .15,
			}
		}
	}
	layers:Mul(distanceMap, t2, t2)
	layers:Add(t1, t2, t2)
	t1 = tmpMkr:Restore(t1)
	layers:Axpy(distanceMap, t2, 1.0)
	
	local x = {
		0.0,33.6199760437012,81.5899848937988,134.479999542236,186.140060424805,
		222.21999168396,255.020046234131,322.259950637817,382.119989395142,
		419.840002059937,441.159963607788,446.89998626709,451.000022888184,
		450.179958343506,472.600555419922,504.012727737427,529.899406433105,
		562.581920623779,590.760040283203,619.39811706543,658.605003356934,
		695.737361907959,719.914960861206,722.41997718811,727.33998298645,
		729.79998588562,741.279935836792,762.599992752075,792.359972000122,1000.0,
	}
	local y = {-0.500011444091797,1.00002288818359,5.50003051757813,14.9999618530273,
		23.9999771118164,37.5,78.4999847412109,127.499961853027,137.5,
		187.5,256.49995803833,494.499969482422,523.500061035156,546.046447753906,
		565.429019927979,578.087997436523,585.103702545166,606.601810455322,
		624.086427688599,640.451049804688,685.507392883301,691.351890563965,
		695.145416259766,841.500091552734,882.499980926514,928.499984741211,
		983.499908447266,992.499923706055,1000.50001144409,999.499988555908,
	}
	local o = -20
	local s = config.canyonWidthScaling
	--local sy = 0.33
	local sy = config.canyonHeightScaling
	for i = 1, #x do 
		x[i] = x[i] * s + o + config.canyonDistanceOffset
		y[i] = y[i] * sy - 2
	end
	layers:Pwlerp(t2, t2, x, y)
	
	local t3 = tmpMkr:Get()
	layers:Gauss(t2, t3, 1, 3)
	t2 = tmpMkr:Restore(t2)
	
	layers:Mad(canyonMap, t3, addTo)
	tmpMkr:Restore(t3)
end

function data.MakeMesaLayer(layers, tmpMkr, config, canyonMap, distanceMap, whiteNoiseMap, mesaCutout, addTo)
	local t1 = tmpMkr:Get()
	
	layers:Points(t1, config.initialSeeds, -1)
	layers:Percolation(whiteNoiseMap, t1, t1, {
		seedThreshold = -0.5,
		noiseThreshold = 0.5,
		maxCluster = 40000,
	})
	local displace = tmpMkr:Get()
	
	layers:Map(distanceMap, mesaCutout, {380, 800}, {0, 1}, true)
	
	layers:Herp(mesaCutout, mesaCutout, {0, 1})
	layers:Mul(canyonMap, mesaCutout, mesaCutout)
	layers:Mul(t1, mesaCutout, t1)
	
	layers:Distance(t1, displace)
	
	local doDisplace = true
	if doDisplace then
		local t2 = tmpMkr:Get()
		layers:RidgedNoise(t2, { octaves = 4, lacunarity = 7.5, frequency = 1.0 / 500.0, gain = 0.4})
		layers:Mad(t2, displace, displace)
		tmpMkr:Restore(t2)
	end
	
	layers[#layers + 1] = {
		type = "OP",
		params = {
			type = "MESA",
			input = displace,
			output = addTo,
			params = {
				plateauHeight = config.height,
			},
		}
	}
	tmpMkr:Restore(displace)
	
	tmpMkr:Restore(t1)
end

return data