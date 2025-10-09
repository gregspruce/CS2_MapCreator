local data = {}

local Layer = {}
Layer.__index = Layer

function Layer.new()
	local tb = {}
	tb.colors = {}
  return setmetatable(tb, Layer)
end

function Layer.SetSeed(layers, seed)
	layers[#layers].seed = seed
	return layers
end

function Layer.Distance(layers, from, to, thr)
	layers[#layers + 1] = {
		type = "OP",
		params = {
			type = "DISTANCE",
			input = from,
			output = to,
			params = {
				threshold = thr,
			}
		}
	}
	return layers
end

function Layer.Copy(layers, from, to)
	layers[#layers + 1] = {
		type = "OP",
		params = {
			type = "MAP",
			input = from,
			output = to,
			params = {
				clamp = false,
			}
		}
	}
	return layers
end

function Layer.Constant(layers, to, val)
	layers[#layers + 1] = {
		type = "FEATURE",
		params = {
			type = "CONSTANT",
			output = to,
			params = {
				value = val,
			}
		}
	}
	return layers
end

function Layer.Map(layers, from, to, mapFrom, mapTo, clamp)
	if clamp == nil then clamp = false end
	layers[#layers + 1] = {
		type = "OP",
		params = {
			type = "MAP",
			input = from, 
			output = to,
			params = {
				mapFrom = mapFrom,
				mapTo = mapTo,
				clamp = clamp
			}
		}
	}
	return layers
end

function Layer.Dithering(layers, to, type)
	layers[#layers + 1] = {
		type = "FEATURE",
		params = { 
			type = "DITHERING",
			output = to,
			params = {
				type = type,
			}
		}
	}
	return layers
end

function Layer.River(layers, to, rivers)
	layers[#layers + 1] = {
		type = "FEATURE",
		params = {
			type = "RIVER",
			output = to,
			params = {
				rivers = rivers
			}
		}
	}
	return layers
end

function Layer.Add(layers, a, b, c)
	layers[#layers + 1] = {
		type = "MIX",
		params = {
			type = "ADD",
			input1 = a,
			input2 = b,
			output = c,
		}
	}
	return layers
end

function Layer.Noise(layers, o, size)
	layers[#layers + 1] = {
		type = "FEATURE",
		params = {
			type = "NOISE",
			output = o,
			params = {
				size = size,
			},
		}
	}
	return layers
end

function Layer.Mad(layers, a, b, c)
	layers[#layers + 1] = {
		type = "MIX",
		params = {
			type = "MAD",
			input1 = a,
			input2 = b,
			output = c,
		}
	}
	return layers
end

function Layer.Mul(layers, a, b, c)
	layers[#layers + 1] = {
		type = "MIX",
		params = {
			type = "MUL",
			input1 = a,
			input2 = b,				
			output = c,
		}
	}
	return layers
end

function Layer.Herp(layers, a, b, points, tangents)
	layers[#layers + 1] = {
		type = "OP",
		params = {
			type = "HERP",
			input = a,
			output = b,
			params = {
				points = points,
				tangents = tangents
			}
		}
	}
	return layers
end
		
function Layer.Gauss(layers, a, b, sigma, size)
	assert(a ~= b)
	assert(size == nil or size % 2 == 1)
	layers[#layers + 1] = {
		type = "OP",
		params = {
			type = "GAUSS",
			input = a,
			output = b,
			params = {
				sigma = sigma,
				size = size,
			}
		}
	}
	return layers
end
		
function Layer.Axpy(layers, a, b, alpha)
	layers[#layers + 1] = {
		type = "OP",
		params = {
			type = "AXPY",
			input = a,
			output = b,
			params = {
				alpha = alpha,
			}
		}
	}
	return layers
end

function Layer.WhiteNoise(layers, o, probability)
	layers[#layers + 1] = {
		type = "FEATURE",
		params = {
			type = "WHITE_NOISE",
			output = o,
			params = {
				probability = probability,
			}
		}
	}
	return layers
end			
		
function Layer.Pwlerp(layers, a, b, x, y)
	layers[#layers + 1] = {
		type = "OP",
		params = {
			type = "PWLERP",
			input = a,
			output = b,
			params = {
				x = x,
				y = y,
			}
		}
	}
	return layers
end
			
function Layer.Points(layers, b, points, value)
	layers[#layers + 1] = {
		type = "FEATURE",
		params = {
			type = "POINTS",
			output = b,
			params = {
				points = points,
				value = value,
			},
		}
	}
	return layers
end
			
function Layer.Percolation(layers, a, b, c, params)
	layers[#layers + 1] = {
		type = "MIX",
		params = {
			type = "PERCOLATION",
			input1 = a,
			input2 = b,
			output = c,
			params = params,
		}
	}
	return layers
end

function Layer.Data(layers, a, map, filter)
	layers[#layers + 1] = {
		type = "FEATURE",
		params = {
			type = "DATA",
			output = a,
			params = {
				map = map,
				filter = filter,
			}
		}
	}	
	return layers
end

function Layer.Grad(layers, a, b, dir)
	layers[#layers + 1] = {
		type = "OP",
		params = {
			type = "GRADIENT",
			input = a,
			output = b,
			params = {
				direction = dir,
			},
		}
	}
	return layers
end

function Layer.Pwconst(layers, a, b, x, y)
	layers[#layers + 1] = {
		type = "OP",
		params = {
			type = "PWCONST",
			input = a,
			output = b,
			params = {
				x = x,
				y = y,
			}
		}
	}
	return layers
end

function Layer.WhiteNoiseNonuniform(layers, i, o, probability)
	layers[#layers + 1] = {
		type = "OP",
		params = {
			type = "WHITE_NOISE",
			input = i,
			output = o,
			params = {
				probability = probability,
			}
		}
	}
	return layers
end		

function Layer.Laplace(layers, i, o)
	layers[#layers + 1] = {
		type = "OP",
		params = {
			type = "LAPLACE",
			input = i,
			output = o,
			params = {
			}
		}
	}
	return layers
end	

function Layer.AmbientOcclusion(layers, i, o, d)
	layers[#layers + 1] = {
		type = "OP",
		params = {
			type = "AMB",
			input = i,
			output = o,
			params = {
				distance = d
			}
		}
	}
	return layers
end		

function Layer.Mask(layers, a, b, c, value, type)
	layers[#layers + 1] = {
		type = "MIX",
		params = { 
			type = "MASK",
			input1 = a,
			input2 = b,
			output = c,
			params = {
				value = value,
				type = type,
			}
		}
	}
	return layers
end	

function Layer.Ridge(layers, o, params)
	layers[#layers + 1] = {
		type = "FEATURE",
		params = {
			type = "RIDGE",
			output = o,
			params = {
				tex = params.tex or "res/textures/terrain/ridge.tga",
				valleys = params.valleys,
				ridges = params.ridges,
				noiseStrength = params.noiseStrength or 10
			},
		},
	}
	return layers
end

function Layer.Compare(layers, a, b, o, type)
	layers[#layers + 1] = {
		type = "MIX",
		params = {
			type = "COMP",
			input1 = a,
			input2 = b,
			output = o,
			params = {
				type = type or "GREATER",
			},
		},
	}
	return layers
end

function Layer.CutoffNoise(layers, o, params)
	layers[#layers + 1] = {
		type = "FEATURE",
		params = {
			type = "NOISE",
			output = o,
			params = {
				frequency = params.frequency,
				size = params.scale, 
				lowerCutoff = params.lowerCutoff,
				upperCutoff = params.upperCutoff,
			}
		}
	}	
	return layers
end

function Layer.PerlinNoise(layers, o, params)
	layers[#layers + 1] = {
		type = "FEATURE",
		params = {
			type = "GRADIENT_NOISE",
			output = o,
			params = {
				type = "perlin",
				frequency = params.frequency,
			}
		}
	}	
end

function Layer.GradientNoise(layers, o, params)
	layers[#layers + 1] = {
		type = "FEATURE",
		params = {
			type = "GRADIENT_NOISE",
			output = o,
			params = {
				type = "gradient",
				numOctaves = params.octaves,
				frequency = params.frequency,
				lacunarity = params.lacunarity,
				gain = params.gain,
				warp = params.warp
			}
		}
	}	
	return layers
end

function Layer.RidgedNoise(layers, o, params)
	layers[#layers + 1] = {
		type = "FEATURE",
		params = {
			type = "RIDGED_NOISE",
			output = o,
			params = {
				numOctaves = params.octaves,
				frequency = params.frequency,
				lacunarity = params.lacunarity,
				gain = params.gain,
			}
		}
	}	
	return layers
end

function Layer.Gradient(layers, input, output, tempMap)
	layers[#layers + 1] = {
		type = "OP",
		params = {
			type = "GRADIENT",
			input = input,
			output = output,
		}
	}
	layers[#layers + 1] = {
		type = "MIX",
		params = {
			type = "MUL",
			input1 = output,
			input2 = output,
			output = output,
		}
	}
	layers[#layers + 1] = {
		type = "OP",
		params = {
			type = "GRADIENT",
			input = input,
			output = tempMap,
			params = {
				direction = 1
			}
		}
	}
	layers[#layers + 1] = {
		type = "MIX",
		params = {
			type = "MAD",
			input1 = tempMap,
			input2 = tempMap,
			output = output,
		}
	}
	return layers
end	

function Layer.PushColor(layers, color)
	layers.colors[#layers+1] = color
end

function Layer.PopColor(layers)
	layers.colors[#layers+1] = -1
end

local TempMaker = {}
TempMaker.__index = TempMaker

function TempMaker.new()
	local tb = {}
	tb.counter = 0
	tb.free = {}
	tb.trace = {}
	tb.doDebug = false
	tb.make = function(id) 
		if tb.doDebug then tb.trace[id] = debug.traceback() end
		return "__t_" .. id 
	end
	tb.unmake = function(str) return tonumber(str:sub(5)) end
	return setmetatable(tb, TempMaker)
end

function TempMaker.Get(tmp)
	if #tmp.free > 0 then 
		local f = tmp.free[#tmp.free]
		tmp.free[#tmp.free] = nil
		return tmp.make(f)
	else 
		tmp.counter = tmp.counter + 1
		return tmp.make(tmp.counter)
	end
end

function TempMaker.Restore(tmp, str)
	local val = tmp.unmake(str)
	
	if val == tmp.counter then tmp.counter = tmp.counter - 1 
	else tmp.free[#tmp.free + 1] = val end
end

function TempMaker.RestoreAll(tmp, layers)
	tmp:Restore(layers.backgroundMaterial)
	
	for k,v in pairs(layers.layers) do
		tmp:Restore(v.map)
	end
end

function TempMaker.Finish(tmp)
	if tmp.doDebug and tmp.counter > 0 then
		local occupied = {}
		for k, v in pairs(tmp.free) do
			occupied[v] = false
		end
		local leaked = {}
		for i = 1, tmp.counter do
			if occupied[i] == nil then
				table.insert(leaked, i)
			end
		end
		if #leaked > 0 then
			print(string.format("Warning: %d resources have leaked, you did not free all temporaries.", #leaked))
		end
		for k, v in pairs(leaked) do
			print("Resrouce " .. v .. " leaked, traceback at Get:")
			print(tmp.trace[v])
		end
	end
end

data.Layer = Layer
data.TempMaker = TempMaker

return data
