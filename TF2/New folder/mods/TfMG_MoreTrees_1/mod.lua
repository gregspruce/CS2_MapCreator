function data()
return {
	info = {
		minorVersion = 0,
		severityAdd = "NONE",
		severityRemove = "NONE",
		name = _("TfMG more trees"),
		description = _("More forests and single trees."),
	},
	runFn = function (settings)
	game.config.terrain.vegetation.forestLevel=0.7 -- 0.0 - 1.0 -- default 0.5
	game.config.terrain.vegetation.forestDensity=1 -- 0.25 - 4.0 -- default 1.0
	game.config.terrain.vegetation.singleDensity=7 -- 0.0 - 100.0 -- default 1
	game.config.terrain.vegetation.treeLine=475 -- default 470
	end
}
end
