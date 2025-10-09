Heightmap generator for Transport Fever and Train Fever.

Generates heightmaps that are not very realistic but fun to play.
You can tweak quite a lot of parameters to generate the map that you want.
Extreme parameter values will generate maps that probably will look good but will be impossible to play.
Hold right mouse button down to rotate the map and scoll to zoom in/out.

************************************************************************************************

Usage:
1. press Preview until you see a low res map that you like
2 (optional). copy Current seed value to Seed:
3 (optional). adjust density, rougness and flatten to your preference
4 (optional). Press Preview again to see the effect of tweaking the parameters
	This step is automaticaly applied when autopreview option is checked
5. press Generate. Map is saved at the requested size, ready to play in the folder /maps/<MapName>/
Avoid using very high values for density and roughness because the game will not be able to generate towns and industries.

/mods/TfMG_Snow_1 - a mod that adds snow on mountain tops
/mods/TfMG_MoreTrees_1 - a mod that increases the number of forests and single trees
If you want lakes in lower regions of the map just adjust the water level parameter.

************************************************************************************************

Placing towns and industries:
1. Select "Place" mode near Generate
2. click on the terrain to place Unnamed towns
3. select zone type: Town, leveling area or some industry
4. Adjust zone options
5. Switch to map mode. (optional)
6. Press preview or generate

Note: Town and idustry placed are not saved between sessions

************************************************************************************************

Options explained:
		Main buttons:
- Export preset/ Import preset = saves/loads settings from a file with extension TfMG. Mask used is not saved with this file. If you give someone the settings also give him the mask if you used one.
- Reset = reset all parameters to default ones
- Exit = just quits the application

- Preview = generates a low res version of the map for preview only (fast)
- Generate = generates full resolution map and saves it in "/maps/<mapname>/" folder along with scripts used by the game (slow and depending on the options can become painfully slow)

		Map parameters:
	(main map generator options)
- MapName = name of the map as it appears in game
- MapSize = 512x512 to 4096x4096 or 16384x1024 (long map).
Map dimensions are automaticaly adjusted to be multiple of 256 and total number of pixels to not exceed 16M.
Map size is automaticaly increased by 1 pixel to conform to game specifications.
- Seed = set to 0 to generate maps with a random seed. 
Set it to Current seed value to generate same map again tweaking density,rougness and flatten.
- Mountain density: density of the mountains on map. It is recomended to not exceed 0.6
- Roughness: recomended values are between 0.3 and 0.7
- Flatten tops: flattens the top of the mountains and sometimes the game generates towns and industries on the mountain tops.
- Slope factor: adjusts middle heights. Lower values generate less pronounced slopes.
- Water level: adds lakes in lower parts of the map.
- Current seed: last seed used to generate preview.

		2nd Pass:
	(a second pass that "cuts" randomly through first pass heightmap creating ravines)
- Enable 2nd pass = enable/disable second pass entirely
- Variant = seed for 2nd pass
- Pass strength = how much the second pass affects first one. A value of 1 will cut all the way to water level, 0 will not do anything
- Density = density of the cuts
- Roughness = roughness of the cuts

		Mask options:
	(use a mask to bend the map to your will)
- Enable mask = enable/disable mask entirely
- Load mask from file = load and image to use as a heightmap mask (JPG and PNG supported only)
- Blend ammount = how much the mask will affect the result. (0.5-0.6 recommended for normal blend. Under 0.5f will somewhat invert the mask. Experiment ;) )
- Linear blend = faster and simpler mask blending. Usually less fun and lowers the average height of the map.
- Invert mask = Use inverted heights from mask (usefull with color photos)

		Time consuming options:
	(enabling/tweaking these will increase the time to generate maps by A LOT!)
- Erosion passes: land slides effect. Each pass takes more and more time!. Not reccomended with autopreview on.

		Settings:
	(general settings)
- Train Fever compatibility = Limits the map dimensions to create maps compatible with Train Fever.
- Enable autopreview when seed not 0 = Enabling this will generate preview when tweaking parameters when having a fixed seed value (not 0)

************************************************************************************************

Change log:
TfMapGen ver. 1.0
- add Export/Import settings
- saving setting on exit
- distort map by a mask image
- second pass creating ravines
- auto preview when seed not 0 for easier tweaking of parameters
- bugfix: converting to PNG when the path contains spaces.

TfMapGen ver. 0.3b
- added Erosion passes. It creates some kind of land slides all over the place.
  WARNING: Each pass takes quite a lot of time to generate so look at the estimated time.
  Leave it at 0 if you don't want/need/like the erosion option or you don't have enough patience.
TfMapGen ver. 0.21b
- added Train Fever compatibility option. Limits map sizes and creates info.lua.
TfMapGen ver. 0.2b
- added Slopes parameter. A value of 1 generates maps like version 0.1b. Lower values generate more medium heights reducing overall slopes. Easier mountain climbing ;)
 side effect: cannot generate maps without mountains at all
- added Water Level so you don't have to edit maps.lua file to get some water on the map
- reduced default roughness to 0.4. It was quite difficult to place large stations without leveling the terrain with roughness at 0.6.

TfMapGen ver. 0.1b (initial)
- 64-bit Windows only
