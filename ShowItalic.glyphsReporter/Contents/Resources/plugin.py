# encoding: utf-8

import math
from GlyphsApp import *
from GlyphsApp.plugins import *
import traceback

class ShowItalic(ReporterPlugin):

	def settings(self):
		self.menuName = Glyphs.localize({
			'en': u'Italic',
			'de': u'Kursive',
			'es': u'itálicas',
			'fr': u'italique'
		})
		
	def masterHasItalicAngle( self, thisMaster ):
		try:
			if abs(thisMaster.italicAngle) < 0.01:
				return False
			else:
				return True
		except:
			print traceback.format_exc()
	
	def italicFontForFont( self, thisFont ):
		try:
			if thisFont:
				familyName = thisFont.familyName
				listOfPossibleFamilyMembers = [ f for f in Glyphs.fonts if f.familyName == familyName and f != thisFont ]
				if len(listOfPossibleFamilyMembers) == 1:
					return listOfPossibleFamilyMembers[0]
				else:
					thisFontIsItalic = self.masterHasItalicAngle(thisFont.masters[0])
					listOfItalicFamilyMembers = [f for f in listOfPossibleFamilyMembers if self.masterHasItalicAngle(f.masters[0]) is not thisFontIsItalic]
					if len(listOfItalicFamilyMembers) == 1:
						return listOfItalicFamilyMembers[0]
			return None
		except Exception as e:
			print traceback.format_exc()
	
	def shiftLayer( self, thisLayer, xOffset ):
		try:
			xShift = NSAffineTransform.transform()
			xShift.translateXBy_yBy_( xOffset, 0.0 )
			thisLayer.transform_checkForSelection_( xShift, False )
		except:
			print traceback.format_exc()
	
	def transform(self, shiftX=0.0, shiftY=0.0, rotate=0.0, skew=0.0, scale=1.0):
		"""
		Returns an NSAffineTransform object for transforming layers.
		Apply an NSAffineTransform t object like this:
			Layer.transform_checkForSelection_doComponents_(t,False,True)
		Access its transformation matrix like this:
			tMatrix = t.transformStruct() # returns the 6-float tuple
		Apply the matrix tuple like this:
			Layer.applyTransform(tMatrix)
			Component.applyTransform(tMatrix)
			Path.applyTransform(tMatrix)
		Chain multiple NSAffineTransform objects t1, t2 like this:
			t1.appendTransform_(t2)
		"""
		myTransform = NSAffineTransform.transform()
		if rotate:
			myTransform.rotateByDegrees_(rotate)
		if scale != 1.0:
			myTransform.scaleBy_(scale)
		if not (shiftX == 0.0 and shiftY == 0.0):
			myTransform.translateXBy_yBy_(shiftX,shiftY)
		if skew:
			skewStruct = NSAffineTransformStruct()
			skewStruct.m11 = 1.0
			skewStruct.m22 = 1.0
			skewStruct.m21 = math.tan(math.radians(skew))
			skewTransform = NSAffineTransform.transform()
			skewTransform.setTransformStruct_(skewStruct)
			myTransform.appendTransform_(skewTransform)
		return myTransform
	
	def background(self, layer):
		self.drawItalic(layer)
	
	def inactiveLayers(self, layer):
		if Glyphs.defaults[com.mekkablue.ShowItalic.drawItalicsForInactiveGlyphs]:
			self.drawItalic(layer, shouldFill=False, shouldFallback=False)
	
	def drawItalic(self, layer, shouldFill=True, shouldFallback=True):
		# set the default color:
		drawingColor = NSColor.colorWithRed_green_blue_alpha_(1.0, 0.1, 0.3, 0.3)
		
		exactCounterpartShown = True
		
		# current font:
		uprightFont = None
		if layer:
			glyph = layer.parent
			if glyph:
				uprightFont = glyph.parent
		
		# find the italic/upright counterpart for the font:
		italicFont = self.italicFontForFont(uprightFont)
		if italicFont:
			glyph = layer.parent
			if glyph:
				glyphName = glyph.name
				
				# find the same glyph in the other font:
				italicGlyph = italicFont.glyphs[glyphName]
				
				# default to unsuffixed version of glyph if exact name does not exist:
				if not italicGlyph and "." in glyphName:
					glyphNameWithoutSuffix = glyphName[:glyphName.find(".")]
					italicGlyph = italicFont.glyphs[glyphNameWithoutSuffix]
					exactCounterpartShown = False
					# change color, so user knows it is not an exact counterpart:
					drawingColor = NSColor.greenColor()
				
				if italicGlyph:
					# determine the same master in other font:
					italicMaster = None
					uprightMasterID = layer.associatedMasterId
					if uprightMasterID:
						uprightMasterName = uprightFont.masters[uprightMasterID].name.replace("Italic","").strip()
						italicMasters = [m for m in italicFont.masters if m.name.startswith(uprightMasterName)]
						if italicMasters:
							italicMaster = italicMasters[0]
					
					# default to the first master:
					if not italicMaster:
						italicMaster = italicFont.masters[0]
					
					# find the glyph layer that corresponds to the master:
					italicLayer = italicGlyph.layers[italicMaster.id]
					if not italicLayer is None:
						displayLayer = NSBezierPath.bezierPath()
						try:
							# app version 2.2
							displayLayer.appendBezierPath_(italicLayer.bezierPath())
							for component in italicLayer.components:
								displayLayer.appendBezierPath_( component.bezierPath() )
						except:
							# app version 2.3+
							displayLayer.appendBezierPath_(italicLayer.bezierPath)
							for component in italicLayer.components:
								displayLayer.appendBezierPath_( component.bezierPath )
							
						# center layer:
						widthDifference = layer.width - italicLayer.width
						if widthDifference:
							horizontalShift = self.transform( shiftX=widthDifference/2.0 )
							displayLayer.transformUsingAffineTransform_( horizontalShift )
							
						# draw the layer on the canvas:
						drawingColor.set()
						if shouldFill:
							displayLayer.fill()
						else:
							displayLayer.setLineWidth_( 5.0 * self.getScale() ** -0.9 )
							displayLayer.stroke()
						
						# display info if a different glyph is shown
						if not exactCounterpartShown and shouldFallback:
							text = " \n \n \n \n%s not found.\nDisplaying %s instead." % ( glyphName, glyphNameWithoutSuffix )
							textPosition = NSPoint( displayLayer.bounds.origin.x+displayLayer.bounds.size.width/2.0, displayLayer.bounds.origin.y )
							self.drawTextAtPoint( text, textPosition, fontSize=10.0, fontColor=drawingColor, align='center')
