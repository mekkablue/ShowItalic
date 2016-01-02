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
	
	def drawBackground(self, layer):
		uprightFont = layer.parent.parent
		italicFont = self.italicFontForFont(uprightFont)
		if italicFont:
			glyph = layer.parent
			if glyph:
				glyphName = glyph.name
				italicGlyph = italicFont.glyphs[glyphName]
				if italicGlyph:
					italicMaster = None
					uprightMasterID = layer.associatedMasterId
					if uprightMasterID:
						uprightMasterName = uprightFont.masters[uprightMasterID].name.replace("Italic","").strip()
						print uprightMasterName
						italicMasters = [m for m in italicFont.masters if uprightMasterName in m.name]
						if italicMasters:
							italicMaster = italicMasters[0]
					if not italicMaster:
						italicMaster = italicFont.masters[0]
					italicLayer = italicGlyph.layers[italicMaster.id]
					if italicLayer:
						NSColor.magentaColor().set()
						italicLayer.copyDecomposedLayer().bezierPath().fill()
