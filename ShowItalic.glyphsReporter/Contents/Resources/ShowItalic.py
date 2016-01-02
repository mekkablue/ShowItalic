# encoding: utf-8

from pluginItalic import *
from AppKit import *

class ShowItalic(ReporterPluginItalic):

	def settings(self):
		self.menuName = 'Italic'
		
	def masterHasItalicAngle( self, thisMaster ):
		try:
			if thisMaster.italicAngle == 0.0:
				return False
			else:
				return True
		except Exception as e:
			self.logToConsole( "masterHasItalicAngle: %s" % str(e) )
	
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
			self.logToConsole( "italicFontForFont: %s" % str(e) )
	
	def shiftLayer( self, thisLayer, xOffset ):
		try:
			xShift = NSAffineTransform.transform()
			xShift.translateXBy_yBy_( xOffset, 0.0 )
			thisLayer.transform_checkForSelection_( xShift, False )
		except Exception as e:
			self.logToConsole( "shiftLayer: %s" % str(e) )
	
	def drawBackground(self, layer):
		# set the default color:
		drawingColor = NSColor.magentaColor()
		
		exactCounterpartShown = True
		
		# current font:
		uprightFont = layer.parent.parent
		
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
						italicMasters = [m for m in italicFont.masters if uprightMasterName in m.name]
						if italicMasters:
							italicMaster = italicMasters[0]
					
					# default to the first master:
					if not italicMaster:
						italicMaster = italicFont.masters[0]
					
					# find the glyph layer that correspnds to the master:
					italicLayer = italicGlyph.layers[italicMaster.id]
					if italicLayer:
						displayLayer = italicLayer.copyDecomposedLayer()
						
						# center layer:
						widthDifference = layer.width - displayLayer.width
						if widthDifference:
							self.shiftLayer( displayLayer, widthDifference/2.0 )
							
						# draw the layer on the canvas:
						drawingColor.set()
						try:
							# app version 2.2
							displayLayer.bezierPath().fill()
						except:
							# app version 2.3+
							displayLayer.bezierPath.fill()
						
						# display info if a different glyph is shown
						if not exactCounterpartShown:
							text = " \n \n \n \n%s not found.\nDisplaying %s instead." % ( glyphName, glyphNameWithoutSuffix )
							textPosition = NSPoint( displayLayer.bounds.origin.x+displayLayer.bounds.size.width/2.0, displayLayer.bounds.origin.y )
							self.drawTextAtPoint( text, textPosition, fontSize=10.0, fontColor=drawingColor, align='center')
