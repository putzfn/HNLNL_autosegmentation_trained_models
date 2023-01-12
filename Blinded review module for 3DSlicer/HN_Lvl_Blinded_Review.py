# -*- coding: UTF-8 -*-
from __main__ import vtk, qt, ctk, slicer
import os
import numpy as np
import SimpleITK as sitk
import sitkUtils
import random

#
# HN_Lvl_Blinded_Review for 3D Slicer v. 4.10.2 - modifaction for other versions may be necessary 
# Florian Putz
# This is a modified version of the 3DSlicer Python module used for blinded review in https://doi.org/10.48550/arXiv.2208.13224 (currently undergoing peer review in Frontiers in Oncology). The program code has been modified to be suitable for sharing including English translation of text.
# It is recommended to additionally pseudonomize all to be rated dataset file names to exclude any unblinding.

class HN_Lvl_Blinded_Review:
  def __init__(self, parent):
    parent.title = "HN_Lvl_Blinded_Review"
    parent.categories = ["Expert Evaluation"]
    parent.dependencies = []
    parent.contributors = ["Florian Putz [FAU Erlangen]"] 
    parent.helpText = "Blinded review of expert contours and deep learning autocontours of H&N nodal levels"
    parent.acknowledgementText =""
    
    self.parent = parent
    parent.icon = qt.QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)),"icon.png"))


class HN_Lvl_Blinded_ReviewWidget():
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

    #####################################
    # Set these parameters

    self.ownInitials = "raterXY" #initials or name of rater

    self.SourcePath = "<SourcePath>" #Source path for blinded data consisting of:
    self.NRRD_suffix = ".nii.gz" # 1) Image / CT datasets with NRRD_suffix
    self.Seg_suffix = "_seg.nii.gz" # 2) Segmentations with Seg_suffix
    self.TargetPath = "<TargetPath>" # Target path for saving blinded ratings as text file    
    self.LevelNameList=["Level_1a","Level_1b_left","Level_1b_right","Level_2_left","Level_2_right","Level_3_left","Level_3_right","Level_4a_left","Level_4a_right","Level_4b_left","Level_4b_right","Level_5_left","Level_5_right","Level_6a","Level_6b","Level_7a","Level_7b_left","Level_7b_right","Level_8_left","Level_8_right"] # List of levels / structures for rating
    self.LEVELTextColorList = [[128,174,128],[241,214,145],[177,122,101],[111,184,210],[216,101,79],[221,130,101],[144,238,144],[192,104,88],[220,245,20],[78,63,0],[255,250,220],[100,100,130],[200,200,235],[250,250,210],[244,214,49],[0,151,206],[216,101,79],[183,156,220],[183,214,211],[152,189,207]] # List of Level RGB contour colors

    #####################################

    self.reloadButton = qt.QPushButton("Reload Module")
    self.reloadButton.toolTip = "Reload this module."
    self.reloadButton.name = "Charting Reload"
    self.layout.addWidget(self.reloadButton)
    self.reloadButton.connect('clicked()', self.onReload)

    self.StartButton = qt.QPushButton("Start Evaluation")
    self.StartButton.toolTip = "Start this module."
    self.layout.addWidget(self.StartButton)
    self.StartButton.connect('clicked()', self.startmodule)

    ReviewandValidateCollapsibleButton = ctk.ctkCollapsibleButton()
    ReviewandValidateCollapsibleButton.text = "Please rate the definition of the following level:"
    self.layout.addWidget(ReviewandValidateCollapsibleButton)

    outputSelectorLabel = qt.QLabel("\nPlease rate the definition of the following level:\n")

    ReviewandValidateLayout = qt.QFormLayout(ReviewandValidateCollapsibleButton)

    ReviewandValidateLayout.layout().addWidget(outputSelectorLabel)
  
    self.LEVELName = qt.QLineEdit("Name of level")

    self.LEVELName.setReadOnly(True)
    self.LEVELName.setAlignment(4)
    NewFont = self.LEVELName.font
    NewFont.setWeight(99)
    NewFont.setPointSize(12)
    self.LEVELName.setFont(NewFont)
    self.LEVELName.setStyleSheet("QLineEdit { background: rgb(255, 255, 255); selection-background-color: rgb(255, 255, 255); }")

    ReviewandValidateLayout.layout().addWidget(self.LEVELName)

    outputSelectorLabel2 = qt.QLabel("\nPlease indicate the level rating in a continous fashion from 0 to 100:\n")
    ReviewandValidateLayout.layout().addWidget(outputSelectorLabel2)

    RatingGrid = qt.QGridLayout()

    self.QualSlider = qt.QSlider()
    self.QualSlider.setMaximum(100)
    self.QualSlider.setOrientation(1)
    self.QualSlider.setTickPosition(3)
    self.QualSlider.setTickInterval(1)
    self.QualSlider.setEnabled(False)
    self.QualSlider.setSliderPosition(50)
    self.QualSlider.setPageStep(1)

    self.CurrLevelRating = qt.QLineEdit("Current level rating")
    self.CurrLevelRating.setReadOnly(True)
    self.CurrLevelRating.setAlignment(4)
    self.CurrLevelRating.setText(self.QualSlider.value)
    self.QualSlider.valueChanged.connect(self.sliderchanged)
    ReviewandValidateLayout.layout().addWidget(self.CurrLevelRating)

    RatingGrid.addWidget(qt.QLabel("0"),0,0)
    RatingGrid.addWidget(self.QualSlider,0,1)
    RatingGrid.addWidget(qt.QLabel("100"),0,2)
    ReviewandValidateLayout.addRow(RatingGrid)

    self.OneButton = qt.QPushButton("Rate")
    ReviewandValidateLayout.addWidget(self.OneButton)
    self.OneButton.connect('clicked()', self.GradeOne)

    self.OneButton.setEnabled(False)

  def cleanup(self):
    self.AvailDatasetsDict = {}
    print("Module reloaded\n")

  def onReload(self,moduleName="HN_Lvl_Blinded_Review"):

    globals()[moduleName] = slicer.util.reloadScriptedModule(moduleName)

  def startmodule(self):
    self.StartButton.setEnabled(False)
    self.QualSlider.setEnabled(True)

    AllDatasetsList = []

    for key in os.listdir(self.SourcePath):
      if key[-len(self.NRRD_suffix):] == self.NRRD_suffix:
        if key[-len(self.Seg_suffix):] != self.Seg_suffix:
            AllDatasetsList.append(key)

    self.AvailDatasetsDict = {}
    self.AllDatasetRatings = {}

    for item in AllDatasetsList:
        self.AllDatasetRatings[item[:-len(self.NRRD_suffix)]]=9999 
        self.AvailDatasetsDict[item]=1

    Randomizelist = []

    for key in self.AvailDatasetsDict:
        if self.AvailDatasetsDict[key] == 1:
            Randomizelist.append(key)

    NewDataSetNRRDFileName = random.choice(Randomizelist)

    NRRDNode = slicer.util.loadVolume(self.SourcePath+NewDataSetNRRDFileName, returnNode=True)[1]
    NRRDNode.SetName("Blinded Volume")
    NRRDNode.GetScalarVolumeDisplayNode().SetAutoWindowLevel(False)
    NRRDNode.GetScalarVolumeDisplayNode().SetWindowLevel(350,40)
    
    sliceNode = slicer.app.layoutManager().sliceWidget('Red').mrmlSliceNode()
    CurrentFOV = sliceNode.GetFieldOfView()
    sliceNode.SetFieldOfView(CurrentFOV[0]*0.5,CurrentFOV[1]*0.5,CurrentFOV[2]*0.5)

    SegLabelNode = slicer.util.loadLabelVolume(self.SourcePath+NewDataSetNRRDFileName.replace(self.NRRD_suffix,self.Seg_suffix), returnNode=True)[1]
    SegLabelNode.SetName("Blinded Labelmap")
    slicer.app.layoutManager().sliceWidget("Red").sliceLogic().GetSliceCompositeNode().SetLabelVolumeID(None)

    SegNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
    SegNode.SetName("Blinded Segmentation")
    slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(SegLabelNode,SegNode)
    SegNode.GetDisplayNode().SetOpacity2DFill(0)
    SegNode.GetDisplayNode().SetOpacity2DOutline(1)
    SegNode.GetSegmentation().SetConversionParameter('Smoothing factor','0')
    SegNode.CreateClosedSurfaceRepresentation()
    SegNode.GetDisplayNode().SetPreferredDisplayRepresentationName2D("Closed surface")
    SegNode.GetDisplayNode().SetSliceIntersectionThickness(2)
    slicer.app.layoutManager().sliceWidget('Red').sliceController().rotateSliceToBackground()
    slicer.app.layoutManager().sliceWidget("Red").sliceLogic().GetSliceCompositeNode().SetLabelVolumeID(None)
    
    self.CurrentDataset = NewDataSetNRRDFileName[:-7]
    self.LEVELName.setText(self.LevelNameList[0])
    self.LEVELName.setStyleSheet("QLineEdit { background: rgb("+str(self.LEVELTextColorList[0][0])+","+str(self.LEVELTextColorList[0][1])+","+str(self.LEVELTextColorList[0][2])+");}")

    self.OneButton.setEnabled(True)

    self.AllDatasetRatings[self.CurrentDataset] = []
    

  def loadNewDataset(self):
    SaveandExport=slicer.util.findChildren(name='FileCloseSceneAction')[0]
    SaveandExport.trigger()

    Randomizelist = []

    for key in self.AvailDatasetsDict:
        if self.AvailDatasetsDict[key] == 1:
            Randomizelist.append(key)

    if len(Randomizelist) == 0:
    	print("All Datasets have been reviewed")
    	self.__d = qt.QDialog()
    	dLayout = qt.QFormLayout( self.__d )
    	buttonBox = qt.QDialogButtonBox()
    	okButton = buttonBox.addButton( buttonBox.Apply )
    	okButton.setIcon( qt.QIcon() )
    	okButton.text = 'All Datasets have been reviewed - That is great!'
    	okButton.connect( 'clicked()', self.__d.hide)
    	dLayout.addWidget( buttonBox )
    	self.__d.setModal( True )
    	self.__d.show()
    	slicer.app.layoutManager().sliceWidget('Red').sliceLogic().GetSliceCompositeNode().SetBackgroundVolumeID("")
    	return

    NewDataSetNRRDFileName = random.choice(Randomizelist)

    NRRDNode = slicer.util.loadVolume(self.SourcePath+NewDataSetNRRDFileName, returnNode=True)[1]
    NRRDNode.GetScalarVolumeDisplayNode().SetAutoWindowLevel(False)
    NRRDNode.GetScalarVolumeDisplayNode().SetWindowLevel(350,40)
    NRRDNode.SetName("Blinded Volume")

    sliceNode = slicer.app.layoutManager().sliceWidget('Red').mrmlSliceNode()
    CurrentFOV = sliceNode.GetFieldOfView()
    sliceNode.SetFieldOfView(CurrentFOV[0]*0.5,CurrentFOV[1]*0.5,CurrentFOV[2]*0.5)

    SegLabelNode = slicer.util.loadLabelVolume(self.SourcePath+NewDataSetNRRDFileName.replace(self.NRRD_suffix,self.Seg_suffix), returnNode=True)[1]
    SegLabelNode.SetName("Blinded Labelmap")

    SegNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
    SegNode.SetName("Blinded Segmentation")
    slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(SegLabelNode,SegNode)
    SegNode.GetDisplayNode().SetOpacity2DFill(0)
    SegNode.GetDisplayNode().SetOpacity2DOutline(1)
    SegNode.GetSegmentation().SetConversionParameter('Smoothing factor','0')
    SegNode.CreateClosedSurfaceRepresentation()
    SegNode.GetDisplayNode().SetPreferredDisplayRepresentationName2D("Closed surface")

    SegNode.GetDisplayNode().SetOpacity2DFill(0)
    SegNode.GetDisplayNode().SetSliceIntersectionThickness(2)
    slicer.app.layoutManager().sliceWidget('Red').sliceController().rotateSliceToBackground()
    slicer.app.layoutManager().sliceWidget("Red").sliceLogic().GetSliceCompositeNode().SetLabelVolumeID(None)
    
    self.CurrentDataset = NewDataSetNRRDFileName[:-7]
    
    self.LEVELName.setText(self.LevelNameList[0])
    self.LEVELName.setStyleSheet("QLineEdit { background: rgb("+str(self.LEVELTextColorList[0][0])+","+str(self.LEVELTextColorList[0][1])+","+str(self.LEVELTextColorList[0][2])+");}")

    self.OneButton.setEnabled(True)
    self.QualSlider.setEnabled(True)

    self.AllDatasetRatings[self.CurrentDataset] = []
    

  def Grade(self, grading):

    self.AllDatasetRatings[self.CurrentDataset].append(self.LevelNameList[len(self.AllDatasetRatings[self.CurrentDataset])]+":"+str(grading))
    self.QualSlider.setSliderPosition(50)

    text_file = open(os.path.join(self.TargetPath,"Ratings_" + self.ownInitials +".txt"), "w")

    for keys in self.AllDatasetRatings:
        text_file.write(keys+"  "+str(self.AllDatasetRatings[keys]))
        text_file.write("\n")
    text_file.close()

    if len(self.AllDatasetRatings[self.CurrentDataset]) < len(self.LevelNameList):
    	self.LEVELName.setText(self.LevelNameList[len(self.AllDatasetRatings[self.CurrentDataset])])
        self.LEVELName.setStyleSheet("QLineEdit { background: rgb("+str(self.LEVELTextColorList[len(self.AllDatasetRatings[self.CurrentDataset])][0])+","+str(self.LEVELTextColorList[len(self.AllDatasetRatings[self.CurrentDataset])][1])+","+str(self.LEVELTextColorList[len(self.AllDatasetRatings[self.CurrentDataset])][2])+");}")
    else:
        self.AvailDatasetsDict[self.CurrentDataset+self.NRRD_suffix] = 0
        self.loadNewDataset()


  def GradeOne(self):
    self.Grade(self.QualSlider.value)

  def sliderchanged(self,value):
    self.CurrLevelRating.setText(value)
