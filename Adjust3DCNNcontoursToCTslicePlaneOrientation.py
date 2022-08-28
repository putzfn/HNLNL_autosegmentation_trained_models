# -*- coding: UTF-8 -*-
from __main__ import vtk, qt, ctk, slicer
import os
from slicer.ScriptedLoadableModule import *
import logging
import numpy as np
from datetime import date
from scipy.stats import mode

#
# Adjust3DCNNcontoursToCTslicePlaneOrientation
# This is postprocessing script is implemented as python module for 3D Slicer v4.10.2

class Adjust3DCNNcontoursToCTslicePlaneOrientation:
  def __init__(self, parent):
    parent.title = "Adjust3DCNNcontoursToCTslicePlaneOrientation"
    parent.categories = ["Postprocessing"]
    parent.dependencies = []
    parent.contributors = ["Florian Putz [FAU Erlangen]"] 
    parent.helpText = ""
    parent.acknowledgementText =""
    
    self.parent = parent
    parent.icon = qt.QIcon("C:\SlicerRadiomics.png")

class Adjust3DCNNcontoursToCTslicePlaneOrientationWidget(ScriptedLoadableModuleTest):
  def __init__(self, parent = None):

    if not parent:
      self.parent = slicer.qMRMLWidget()
      self.parent.setLayout(qt.QVBoxLayout())
      self.parent.setMRMLScene(slicer.mrmlScene)
    else:
      self.parent = parent
    self.layout = self.parent.layout()
    if not parent:
      self.setup()
      self.parent.show()


  def setup(self):
    self.reloadButton = qt.QPushButton("Reload Module")
    self.reloadButton.toolTip = "Reload this module."
    self.reloadButton.name = "Charting Reload"
    self.layout.addWidget(self.reloadButton)
    self.reloadButton.connect('clicked()', self.onReload)

    # Collapsible button
    sampleCollapsibleButton = ctk.ctkCollapsibleButton()
    sampleCollapsibleButton.text = "Make labels consistent with CT slice plane orientation"
    self.layout.addWidget(sampleCollapsibleButton)

    sampleFormLayout = qt.QFormLayout(sampleCollapsibleButton)

    LabelTestButton = qt.QPushButton("Start processing datasets")
    sampleFormLayout.addWidget(LabelTestButton)
    LabelTestButton.connect('clicked(bool)', self.MakeConsistentwithSlicePlaneOrientation)

  def cleanup(self):
    print("Module closed\n")

  def onReload(self,moduleName="Adjust3DCNNcontoursToCTslicePlaneOrientation"):

    globals()[moduleName] = slicer.util.reloadScriptedModule(moduleName)

    global filenames
    filenames = []

  def Area(self,current2Dslice,Label):
    return current2Dslice[current2Dslice==Label].astype(int).sum()/Label

  def MakeConsistentwithSlicePlaneOrientation(self):

    global filenames
    volumesLogic = slicer.modules.volumes.logic()
      
    filenames = []

    TargetPath = "Enter TargetPath"

    SourcePath_NNLabels = "Enter Source Path with nnUnet ensemble label predictions"

    NNLabel_suffix = ".nii.gz"

    for key in os.listdir(SourcePath_NNLabels):
        filenames.append(key)

    for eachNNLabelFile in filenames:

      SaveandExport=slicer.util.findChildren(name='FileCloseSceneAction')[0]
      SaveandExport.trigger()

      AutoSegNode = slicer.util.loadLabelVolume(SourcePath_NNLabels+eachNNLabelFile)

      AutoSegArray = slicer.util.arrayFromVolume(AutoSegNode)

      mutuallyexclusivelabels2 = [[18,5],[17,4],[5,7],[4,6],[7,9],[6,8]]
      mutuallyexclusivelabels3 = [[11,9,13],[10,8,12]]
      mutuallyexclusivelabels4 = [[14,1,2,3]]

      for eachrow in range (AutoSegArray.shape[0]):
        current2Dslice = AutoSegArray[eachrow]

        for eachMutualExclusiveLabelPair in mutuallyexclusivelabels2:
            if self.Area(current2Dslice,eachMutualExclusiveLabelPair[0])>0 and self.Area(current2Dslice,eachMutualExclusiveLabelPair[1])>0:
                print ("Observed conflict between "+str(eachMutualExclusiveLabelPair[0])+" and "+str(eachMutualExclusiveLabelPair[1])+" in slice row "+str(eachrow))
                if self.Area(current2Dslice,eachMutualExclusiveLabelPair[0])>=self.Area(current2Dslice,eachMutualExclusiveLabelPair[1]):
                    AutoSegArray[eachrow][AutoSegArray[eachrow]==eachMutualExclusiveLabelPair[1]] = eachMutualExclusiveLabelPair[0]
                else:
                    AutoSegArray[eachrow][AutoSegArray[eachrow]==eachMutualExclusiveLabelPair[0]] = eachMutualExclusiveLabelPair[1]    

        for eachMutualExclusiveLabelPair in mutuallyexclusivelabels3:
            if self.Area(current2Dslice,eachMutualExclusiveLabelPair[0])>0 and (self.Area(current2Dslice,eachMutualExclusiveLabelPair[1])>0 or self.Area(current2Dslice,eachMutualExclusiveLabelPair[2])>0):
                print ("Observed conflict between "+str(eachMutualExclusiveLabelPair[0])+" and ("+str(eachMutualExclusiveLabelPair[1])+" or " + str(eachMutualExclusiveLabelPair[2]) +  ") in slice row "+str(eachrow))
                if self.Area(current2Dslice,eachMutualExclusiveLabelPair[0])>=(self.Area(current2Dslice,eachMutualExclusiveLabelPair[1])+self.Area(current2Dslice,eachMutualExclusiveLabelPair[2])):
                    AutoSegArray[eachrow][AutoSegArray[eachrow]==eachMutualExclusiveLabelPair[1]] = eachMutualExclusiveLabelPair[0]
                    AutoSegArray[eachrow][AutoSegArray[eachrow]==eachMutualExclusiveLabelPair[2]] = eachMutualExclusiveLabelPair[0]
                else:
                    upperslice = AutoSegArray[eachrow+1].copy()
                    for i in range(20):
                        j = i + 1
                        if (j!=eachMutualExclusiveLabelPair[1]) and (j!=eachMutualExclusiveLabelPair[2]):
                            upperslice[upperslice == j] = 0

                    AutoSegArray[eachrow][AutoSegArray[eachrow]==eachMutualExclusiveLabelPair[0]] = upperslice[AutoSegArray[eachrow]==eachMutualExclusiveLabelPair[0]]


        for eachMutualExclusiveLabelPair in mutuallyexclusivelabels4:
            if self.Area(current2Dslice,eachMutualExclusiveLabelPair[0])>0 and (self.Area(current2Dslice,eachMutualExclusiveLabelPair[1])>0 or self.Area(current2Dslice,eachMutualExclusiveLabelPair[2])>0 or self.Area(current2Dslice,eachMutualExclusiveLabelPair[3])>0):
                print ("Observed conflict between "+str(eachMutualExclusiveLabelPair[0])+" and ("+str(eachMutualExclusiveLabelPair[1])+" or " + str(eachMutualExclusiveLabelPair[2])+" or " + str(eachMutualExclusiveLabelPair[3]) +  ") in slice row "+str(eachrow))
                if self.Area(current2Dslice,eachMutualExclusiveLabelPair[0])>=(self.Area(current2Dslice,eachMutualExclusiveLabelPair[1])+self.Area(current2Dslice,eachMutualExclusiveLabelPair[2])+self.Area(current2Dslice,eachMutualExclusiveLabelPair[3])):
                    AutoSegArray[eachrow][AutoSegArray[eachrow]==eachMutualExclusiveLabelPair[1]] = eachMutualExclusiveLabelPair[0]
                    AutoSegArray[eachrow][AutoSegArray[eachrow]==eachMutualExclusiveLabelPair[2]] = eachMutualExclusiveLabelPair[0]
                    AutoSegArray[eachrow][AutoSegArray[eachrow]==eachMutualExclusiveLabelPair[3]] = eachMutualExclusiveLabelPair[0]
                else:
                    upperslice = AutoSegArray[eachrow+1].copy()
                    uppersliceMode = upperslice.copy()

                    for i in range(20):
                        j = i + 1
                        if (j!=eachMutualExclusiveLabelPair[1]) and (j!=eachMutualExclusiveLabelPair[2]) and (j!=eachMutualExclusiveLabelPair[3]):
                            uppersliceMode[uppersliceMode == j] = 0

                    for eachcolumn in range(uppersliceMode.shape[1]):
                        currentcolumn = uppersliceMode.T[eachcolumn]
                        currentcolumnNonZero = currentcolumn[currentcolumn>0]
                        if len(mode(currentcolumnNonZero)[0])>0:
                            uppersliceMode.T[eachcolumn][uppersliceMode.T[eachcolumn]==0] = mode(currentcolumnNonZero)[0]
                        else:
                            uppersliceMode.T[eachcolumn] = 0

                    for i in range(20):
                        j = i + 1
                        if (j!=eachMutualExclusiveLabelPair[1]) and (j!=eachMutualExclusiveLabelPair[2]) and (j!=eachMutualExclusiveLabelPair[3]):
                            upperslice[upperslice == j] = uppersliceMode[upperslice == j]

                    AutoSegArray[eachrow][AutoSegArray[eachrow]==eachMutualExclusiveLabelPair[0]] = upperslice[AutoSegArray[eachrow]==eachMutualExclusiveLabelPair[0]]

        # Remove Slices with combined Area <= 10
        threshold = 10

        current2DsliceBinary = (AutoSegArray[eachrow] > 0).astype(int)
        if current2DsliceBinary.sum() <= threshold:
            AutoSegArray[eachrow] = 0

        # Remove Slices with reduction in area compared to upperslice > 80%
    
        if current2DsliceBinary.sum() > threshold:
            bottom2DsliceBinary = (AutoSegArray[eachrow-1] > 0).astype(int)
            upper2DsliceBinary = (AutoSegArray[eachrow+1] > 0).astype(int)

            if ((bottom2DsliceBinary.sum()==0) and (current2DsliceBinary.sum()/float(upper2DsliceBinary.sum())<=0.2)):
                AutoSegArray[eachrow] = 0
                print(str(current2DsliceBinary.sum()/float(upper2DsliceBinary.sum())))

      slicer.util.updateVolumeFromArray(AutoSegNode,AutoSegArray)

      slicer.util.saveNode(AutoSegNode, TargetPath+eachNNLabelFile, properties={})
