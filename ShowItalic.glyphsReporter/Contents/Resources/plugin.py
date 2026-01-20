# encoding: utf-8
from __future__ import division, print_function, unicode_literals
import objc
from Cocoa import NSAffineTransform, NSAffineTransformStruct, NSBezierPath, NSColor, NSPoint, NSControlKeyMask, NSAlternateKeyMask, NSCommandKeyMask, NSClassFromString
from GlyphsApp import Glyphs, GSAnchor
from GlyphsApp.plugins import ReporterPlugin
from math import tan, radians


class ShowItalic(ReporterPlugin):

	@objc.python_method
	def settings(self):
		self.menuName = Glyphs.localize({
			'en': 'Italic',
			'de': 'Kursive',
			'es': 'itálicas',
			'it': 'italica',
			'fr': 'italique',
			'zh': '🥂意大利体',
		})
		self.keyboardShortcut = 'i'
		self.keyboardShortcutModifier = NSControlKeyMask | NSAlternateKeyMask | NSCommandKeyMask
		self.threshold = 0.1

	@objc.python_method
	def foreground(self, layer):
		if not self.getScale() > self.threshold and self.conditionsAreMetForDrawing():
			self.drawItalic(layer, shouldFill=False, shouldFallback=False, canShowBounds=False)

	@objc.python_method
	def background(self, layer):
		if self.getScale() > self.threshold and self.conditionsAreMetForDrawing():
			self.drawItalic(layer)

	@objc.python_method
	def inactiveLayerForeground(self, layer):
		if self.getScale() > self.threshold and self.conditionsAreMetForDrawing():
			activeLayer = self.controller.activeLayer()
			if activeLayer and activeLayer.parent.name in layer.componentNames():
				for item in activeLayer.selection:
					if isinstance(item, GSAnchor):
						self.drawItalic(layer, shouldFill=False, shouldFallback=True, canShowBounds=True)
						break

	@objc.python_method
	def inactiveLayerBackground(self, layer):
		if self.getScale() > self.threshold and Glyphs.defaults["com.mekkablue.ShowItalic.drawItalicsForInactiveGlyphs"]:
			self.drawItalic(layer, shouldFill=False, shouldFallback=False, canShowBounds=(not self.conditionsAreMetForDrawing()))

	@objc.python_method
	def conditionsAreMetForDrawing(self):
		"""
		Don't activate if text or pan (hand) tool are active.
		"""
		windowController = self.controller.view().window().windowController()
		if windowController:
			tool = windowController.toolDrawDelegate()
			# textToolIsActive = tool.isKindOfClass_(NSClassFromString("GlyphsToolText"))
			handToolIsActive = tool.isKindOfClass_(NSClassFromString("GlyphsToolHand"))
			if not handToolIsActive:
				return True
		return False

	@objc.python_method
	def masterHasItalicAngle(self, thisMaster):
		try:
			if abs(thisMaster.italicAngle) < 0.01:
				return False
			else:
				return True
		except:
			import traceback
			print(traceback.format_exc())

	@objc.python_method
	def italicFontForFont(self, thisFont):
		try:
			if thisFont:
				familyName = thisFont.familyName
				listOfPossibleFamilyMembers = [f for f in Glyphs.fonts if f.familyName == familyName and f != thisFont]
				if len(listOfPossibleFamilyMembers) == 1:
					return listOfPossibleFamilyMembers[0]
				else:
					thisFontIsItalic = self.masterHasItalicAngle(thisFont.masters[0])
					listOfItalicFamilyMembers = [f for f in listOfPossibleFamilyMembers if self.masterHasItalicAngle(f.masters[0]) is not thisFontIsItalic]
					if len(listOfItalicFamilyMembers) == 1:
						return listOfItalicFamilyMembers[0]
			return None
		except Exception as e:
			print("Problem with:", thisFont)
			print(e)
			import traceback
			print(traceback.format_exc())

	@objc.python_method
	def italicMasterForCurrentMaster(self, master):
		"""
		Finds the next italic master for the currently selected font master.

		Args:
			master: GSFontMaster

		Returns: master (GSFontMaster) with the same axis values, but different ital/slnt axis value.
		"""
		if not master:
			return None

		font = master.font

		italicAxis = font.axisForTag_('ital') or font.axisForTag_('slnt')

		if not italicAxis:
			return None

		italicValues = []

		for fontMaster in font.masters:
			italicValue = fontMaster.axisValueValueForId_(italicAxis.id)
			if italicValue not in italicValues:
				italicValues.append(italicValue)

		italicValues.sort()

		if len(italicValues) < 2:
			return None

		masterItalicValue = master.axisValueValueForId_(italicAxis.id)

		# Find the master with the next biggest italic value, but identical values on the other axes.

		thisItalicValueIndex = italicValues.index(masterItalicValue)

		nextItalicValue = italicValues[thisItalicValueIndex % len(italicValues)]

		nextItalicMaster = None
		for otherMaster in font.masters:
			if otherMaster == master:
				continue
			match = True
			for axis in font.axes:
				if axis.axisTag != italicAxis.axisTag:
					if otherMaster.axisValueValueForId_(axis.id) != master.axisValueValueForId_(axis.id):
						match = False
						continue
			if master.axisValueValueForId_(italicAxis.id) != nextItalicValue:
				continue
			elif match:
				nextItalicMaster = otherMaster
				break

		return nextItalicMaster

	@objc.python_method
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
			myTransform.translateXBy_yBy_(shiftX, shiftY)
		if skew:
			skewStruct = NSAffineTransformStruct()
			skewStruct.m11 = 1.0
			skewStruct.m22 = 1.0
			skewStruct.m21 = tan(radians(skew))
			skewTransform = NSAffineTransform.transform()
			skewTransform.setTransformStruct_(skewStruct)
			myTransform.appendTransform_(skewTransform)
		return myTransform

	@objc.python_method
	def drawLine(self, start=NSPoint(), end=NSPoint(), dashed=False):
		try:
			line = NSBezierPath.bezierPath()
			line.moveTo_(start)
			line.lineTo_(end)
			line.setLineWidth_(1.0 / self.getScale())
			if dashed:
				line.setLineDash_count_phase_((1.0 / self.getScale(), 3.0 / self.getScale()), 2, 0)
			line.stroke()
		except Exception as e:
			self.logToConsole("drawLine: %s" % str(e))

	@objc.python_method
	def drawHeightSnapsForLayers(self, otherLayer, currentLayer):
		try:
			otherHeight = otherLayer.bounds.size.height
			currentHeight = currentLayer.bounds.size.height

			# only draw if there is something in BOTH layers:
			if otherHeight != 0 and currentHeight != 0:

				# measurements:
				otherShift = (currentLayer.width - otherLayer.width) * 0.5
				otherLeft = otherLayer.bounds.origin.x + otherShift
				currentLeft = currentLayer.bounds.origin.x
				otherRight = otherLeft + otherLayer.bounds.size.width
				currentRight = currentLeft + currentLayer.bounds.size.width
				otherBottom = otherLayer.bounds.origin.y
				currentBottom = currentLayer.bounds.origin.y
				otherTop = otherBottom + otherHeight
				currentTop = currentBottom + currentHeight
				margin = 10.0

				sameHeightColor = NSColor.blueColor().colorWithAlphaComponent_(0.6)
				differentHeightColor = NSColor.textColor().colorWithAlphaComponent_(0.25)

				# BOTTOMS
				if otherBottom == currentBottom:
					sameHeightColor.set()
					xMin = min(otherLeft, currentLeft) - margin
					xMax = max(otherRight, currentRight) + margin
					self.drawLine(start=NSPoint(xMin, otherBottom), end=NSPoint(xMax, otherBottom))
				else:
					differentHeightColor.set()
					self.drawLine(start=NSPoint(otherLeft - margin, otherBottom), end=NSPoint(otherRight + margin, otherBottom), dashed=True)
					self.drawLine(start=NSPoint(currentLeft - margin, currentBottom), end=NSPoint(currentRight + margin, currentBottom), dashed=True)

				# TOPS
				if otherTop == currentTop:
					sameHeightColor.set()
					xMin = min(otherLeft, currentLeft) - margin
					xMax = max(otherRight, currentRight) + margin
					self.drawLine(start=NSPoint(xMin, otherTop), end=NSPoint(xMax, otherTop))
				else:
					differentHeightColor.set()
					self.drawLine(start=NSPoint(otherLeft - margin, otherTop), end=NSPoint(otherRight + margin, otherTop), dashed=True)
					self.drawLine(start=NSPoint(currentLeft - margin, currentTop), end=NSPoint(currentRight + margin, currentTop), dashed=True)

		except Exception as e:
			self.logToConsole("drawHeightSnapsForLayers: %s" % str(e))

	@objc.python_method
	def cleanName(self, name):
		triggerWords = (
			"Italic",
			"Roman",
			"Upright",
			"Kursiv",
			"Aufrecht",
			"Recte",
		)
		for triggerWord in triggerWords:
			if triggerWord in name:
				name = name.replace(triggerWord, "").replace("  ", " ").strip()
				if name == "":
					name = "Regular"
				break
		return name

	@objc.python_method
	def drawItalic(self, layer, shouldFill=True, shouldFallback=True, canShowBounds=True):
		# set the default color:
		drawingColor = NSColor.redColor()
		exactCounterpartShown = True

		# current font:
		uprightFont = None
		if layer:
			glyph = layer.parent
			if glyph:
				uprightFont = glyph.parent

		# Find the corresponding italic master in the same font.
		fontHasItalic = False
		if italicMaster := self.italicMasterForCurrentMaster(layer.associatedFontMaster()):
			fontHasItalic = True

		# find the italic/upright counterpart for the font:
		if fontHasItalic:
			italicFont = layer.font()
		else:
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
					drawingColor = NSColor.greenColor().colorWithAlphaComponent_(0.4)

				if italicGlyph:
					if not fontHasItalic:
						# determine the same master in other font:
						# default to the first master:
						italicMaster = italicFont.masters[0]
						uprightMasterID = layer.associatedMasterId
						if not isinstance(uprightMasterID, str):
							uprightMasterID = layer.associatedMasterId()
							# background layer: associatedMasterId not wrapped

						if uprightMasterID:
							uprightMasterName = self.cleanName(uprightFont.masters[uprightMasterID].name)
							# try to find exact expected name:
							italicMasters = [m for m in italicFont.masters if uprightMasterName == self.cleanName(m.name)]
							# if that fails, pick a best guess
							if not italicMasters:
								italicMasters = [m for m in italicFont.masters if self.cleanName(m.name).startswith(uprightMasterName)]
							if italicMasters:
								italicMaster = italicMasters[0]
							elif len(uprightFont.masters) == len(italicFont.masters):
								for i, m in enumerate(uprightFont.masters):
									if m.id == uprightMasterID:
										italicMaster = italicFont.masters[i]
										break

					# find the glyph layer that corresponds to the master:
					italicLayer = italicGlyph.layers[italicMaster.id]
					if italicLayer is not None:
						displayLayer = italicLayer.completeBezierPath
						scaleFactor = uprightFont.upm / italicFont.upm
						if scaleFactor != 1.0:
							scale = self.transform(scale=scaleFactor)
							displayLayer.transformUsingAffineTransform_(scale)

						# center layer:
						widthDifference = (layer.width - italicLayer.width) * 0.5 * scaleFactor
						if widthDifference:
							horizontalShift = self.transform(shiftX=widthDifference)
							displayLayer.transformUsingAffineTransform_(horizontalShift)

						# draw height snaps on canvas:
						try:
							if canShowBounds:  # and Glyphs.versionNumber >= 3.0:
								self.drawHeightSnapsForLayers(italicLayer, layer)
						except:
							import traceback
							print(traceback.format_exc())
							pass

						# draw the layer on the canvas:
						if shouldFill:
							drawingColor.colorWithAlphaComponent_(0.25).set()
							displayLayer.fill()
						else:
							drawingColor.colorWithAlphaComponent_(0.45).set()
							displayLayer.setLineWidth_(1.5 / self.getScale())
							displayLayer.stroke()

						# display info if a different glyph is shown
						if not exactCounterpartShown and shouldFallback:
							text = f" \n \n \n \n{glyphName} not found.\nDisplaying {glyphNameWithoutSuffix} instead."
							bounds = displayLayer.bounds
							if isinstance(bounds, objc.native_selector):
								bounds = displayLayer.bounds()
							textPosition = NSPoint(bounds.origin.x + bounds.size.width / 2.0, bounds.origin.y)
							self.drawTextAtPoint(text, textPosition, fontSize=10.0, fontColor=drawingColor, align='center')

	@objc.python_method
	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__
