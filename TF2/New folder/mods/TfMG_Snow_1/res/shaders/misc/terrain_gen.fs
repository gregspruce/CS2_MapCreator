#version 150
// -- added snow at higher altitudes
uniform sampler2D heightmapTex;
uniform sampler2D ambientTex;
uniform vec2 offset;
uniform vec2 tileSize;
uniform vec2 resolution;
uniform float texel;

uniform sampler2D noiseTex;
//uniform sampler2D indexTex;

uniform sampler2D levelColorTex;
uniform sampler2DArray detailColorArrayTex;
uniform sampler2DArray detailNrmlArrayTex;

in vec4 texCoord;

out vec4 color0;
out vec4 color1;

float snoise(vec2 v);

vec3 decodeNormal(vec2 color);
vec3 overlay(vec4 col0, vec3 col1);
vec3 nrmlAmb2rgb(vec4 nrmlAmb);	
float getHeightNormalSlope(sampler2D heightmapTex, vec2 tileSize, vec2 resolution, float texel, vec2 tc,
		out mat3 tangentMat, out float slope);

float getLevel(float x, float s0, float s1, float s2, float s3, float s4, float s5) {
	if (x < s1) {
		return .2 * (x - s0) / (s1 - s0);
	}

	if (x < s2) {
		return .2 + .2 * (x - s1) / (s2 - s1);
	}
	
	if (x < s3) {
		return .4 + .2 * (x - s2) / (s3 - s2);
	}
	
	if (x < s4) {
		return .6 + .2 * (x - s3) / (s4 - s3);
	}

	return .8 + .2 * (x - s4) / (s5 - s4);
}

float abNoise(vec2 tc) {
	float n0 = .5 + .5 * snoise(tc);
	float n1 = texture(noiseTex, tc).r;

	//float n = .5 * (n0 + n1);
	return .667 * n0 + .333 * n1;
}

vec3 getLevelColor(vec2 pos, vec2 dposdx, vec2 dposdy, int iLevel, float fLevel, out vec3 nrml) {
	float detailTexSize = 32.0;

	//float n = snoise(pos / 800.0);
	//float n = snoise((pos + vec2(900.0 * iLevel)) / mix(800.0, 500.0, fact1 * iLevel));
	float n = snoise((pos + vec2(900.0 * iLevel)) / mix(200.0, 50.0, iLevel / 5.0));

	float n0 = abNoise((pos - vec2(5000.0)) / 600.0);
	//float n1 = abNoise((pos + vec2(5000.0)) / 700.0);
	float n1 = n0;

	float s = smoothstep(-.25, .25, n);

	vec2 tc = pos / detailTexSize;
	vec2 dtcdx = dposdx / detailTexSize;
	vec2 dtcdy = dposdy / detailTexSize;

	float lev0 = 2.0 * iLevel;
	float lev1 = 2.0 * iLevel + 1.0;

	vec3 nrml0 = decodeNormal(textureGrad(detailNrmlArrayTex, vec3(tc, lev0), dtcdx, dtcdy).rg);
	vec3 nrml1 = decodeNormal(textureGrad(detailNrmlArrayTex, vec3(tc, lev1), dtcdx, dtcdy).rg);
	nrml = mix(nrml0, nrml1, s);

	float fact = 1.0 / 16, ofs = .125;
	vec3 col0 = texture(levelColorTex, vec2(n0, fact * (lev0 + mix(ofs, 1.0, fLevel)))).rgb;
	vec3 col1 = texture(levelColorTex, vec2(n1, fact * (lev1 + mix(.0, 1.0 - ofs, fLevel)))).rgb;
	col0 = overlay(textureGrad(detailColorArrayTex, vec3(tc, lev0), dtcdx, dtcdy), col0);
	col1 = overlay(textureGrad(detailColorArrayTex, vec3(tc, lev1), dtcdx, dtcdy), col1);

	return mix(col0, col1, s);
}

void main() {
	float snowSlope = .6; // max = rockSlope0
	float snowStart = .5;
	float snowEnd = .7;
	vec3 snowCol = vec3(.9,.9,.9);
	
	mat3 tangentMat;
	float slope;
	float height = getHeightNormalSlope(heightmapTex, tileSize, resolution, texel, texCoord.xy, tangentMat, slope);

	float ambient = texture(ambientTex, texCoord.xy).r;

	vec2 pos = tileSize * (offset + texCoord.xy);
	vec2 dposdx = dFdx(pos);
	vec2 dposdy = dFdy(pos);

	float rockSlope0 = .882;		// .25
	float rockSlope1 = 1.169;		// .35


	//float heightLevel = getLevel(min(height, 650.0), .0, 210.0, 350.0, 490.0, 590.0, 650.0);
	float heightLevel = getLevel(min(height, 600.0), .0, 230.0, 360.0, 470.0, 550.0, 600.0);
	float slopeLevel = getLevel(min(slope / rockSlope0, 1.0), .0, .3, .5, .7, .85, 1.0);
	float ambientLevel = getLevel(1.0 - ambient, .0, .2, .4, .55, .7, 1.0);

	//float level01 = max(heightLevel, max(slopeLevel, ambientLevel));
	float level01 = min(max(heightLevel, ambientLevel) + .2 * slopeLevel, 1.0);

	int iLevel = min(int(5.0 * level01), 4);
	float fLevel = 5.0 * level01 - float(iLevel);


	//float tol = .05;
	//float tol = .015 + .015 * iLevel;	// 0.015 - 0.075
	float tol = .333;

	vec3 col, nrml;

	//col = vec3(.25);
	//nrml = vec3(.0, .0, 1.0);

	if (iLevel > 0 && fLevel < tol) {
		vec3 nrml0, nrml1;
		vec3 col0 = getLevelColor(pos, dposdx, dposdy, iLevel - 1, 1.0, nrml0);
		vec3 col1 = getLevelColor(pos, dposdx, dposdy, iLevel, fLevel, nrml1);
		//float s = smoothstep(-tol, tol, fLevel);
		float s = .5 + .5 * fLevel / tol;
		col = mix(col0, col1, s);
		nrml = mix(nrml0, nrml1, s);
	} else if (iLevel < 4 && fLevel > 1.0 - tol) {
		vec3 nrml0, nrml1;
		vec3 col0 = getLevelColor(pos, dposdx, dposdy, iLevel, fLevel, nrml0);
		vec3 col1 = getLevelColor(pos, dposdx, dposdy, iLevel + 1, .0, nrml1);
		//float s = smoothstep(1.0 - tol, 1.0 + tol, fLevel);
		float s = .5 * (fLevel - (1.0 - tol)) / tol;
		col = mix(col0, col1, s);
		nrml = mix(nrml0, nrml1, s);
	} else {
		col = getLevelColor(pos, dposdx, dposdy, iLevel, fLevel, nrml);
	}

	if (slope > rockSlope0) {
		float rockInt = min((slope - rockSlope0) / (rockSlope1 - rockSlope0), 1.0);

		//float n4 = texture(noise, 71.1 * tc).r;
		//rockInt = min(pow(2.0 * n4 * rockInt + rockInt, 20.0), 1.0);

		vec3 rockNrml;
		vec3 rockCol = getLevelColor(pos, dposdx, dposdy, 5, rockInt, rockNrml);

		col = mix(col, rockCol, rockInt);
		nrml = mix(nrml, rockNrml, rockInt);

		//col = vec3(.7, .0, .0);
	} else {
		if (heightLevel>=snowStart) {
			if (heightLevel>=snowEnd) {
				col=snowCol;
			} else {
				float mixSnow = (heightLevel-snowStart)/(snowEnd-snowStart);
				float mixSlope = 1.0;
				if (slope>snowSlope) mixSlope = (rockSlope0 - slope) / (rockSlope0 - snowSlope);
				col = mix(col,snowCol, mixSnow * mixSlope);
			}
		}
	}

	//col = vec3(1.0 - .2 * iLevel);

	//col = overlay(texture(detailColorArrayTex, vec3(pos / 4096.0, .0)), col);
	//col *= 1.0 + .1 * snoise(pos / 16.0);

	color0.rgb = col;
	color1.rgb = nrmlAmb2rgb(vec4(tangentMat * nrml, ambient));
}
