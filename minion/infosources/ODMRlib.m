(* ::Package:: *)

ClearAll[$ODMRcontrolHost,$ODMRcontrolProgram,$ODMRcontrolProcess,
	$ODMRsharedMemoryLinkName,$ODMRgroupUser,$ODMRgroupUserId,$ODMRgroupId,$ODMRgroup,
	$ODMRmicrowaveSequencesDirectory,$ODMRmicrowaveSequencesRemoteDirectory,
	$ODMRmicrowaveSequencesDirectoryMounted,$ODMRnumCounters,$ODMRlink,$ODMRstage,
	$ODMRcounter,$ODMRlaser,$ODMRsmiq,$ODMRawg,$ODMRLinkLock,$ODMRLinkLocked,
	$ODMRLockLink,$ODMRfpgaClock,$ODMRdetectionDelay,
	ConstructMathLinkConnectionString,InitODMR,DeinitODMR,
	GetCounterCountingTime,SetCounterCountingTime,CountCounters,GetCounterPredelay,
	SetCounterPredelay,GetOutputs,SetOutputs,GetTriggerMask,SetTriggerMask,
	GetTriggerInvertMask,SetTriggerInvertMask,GetNumberOfCounts,SetNumberOfCounts,
	GetNumberOfTriggeredCountingBins,SetNumberOfTriggeredCountingBins,
	GetTriggeredCountingAddress,SetTriggeredCountingAddress,
	GetTriggeredCountingBinRepetitions,SetTriggeredCountingBinRepetitions,
	GetTriggeredCountingBinRepetitionCounter,SetSplitTriggeredCountingBins,
	GetSplitTriggeredCountingBins,EnableTriggeredCounting,DisableTriggeredCounting,
	TriggerCounter,	ReadTriggeredCountingData,ResetTriggeredCountingData,
	TrackConfocalMaximum,TrackerContext,TrackerContextQ,CountAndTrack,
	ScanConfocalImage,CropConfocalImage,TransposeConfocalImage,PlotConfocalImage,
	ConfocalImageColorLegend,ReadStage,MoveStage,GPIBcmd,GPIBqueryNumber,SerialCmd,
	SerialQueryNumber,SerialTMCqueryNumber,ScanConfocalVolume,FindNV,ReadAWGwfm,
	WriteAWGwfm,ConstructMicrowaveSequence,EnableAOM,DisableAOM,SetLaserControlMode,
	GetLaserControlMode,SetLaserCurrent,GetLaserCurrent,SetLaserPower,GetLaserPower,
	GetLaserTemperature,GetLaserPSUtemperature,GetAWGwfmDuration,GetAWGwfmDurationAndClockRate,
	ODMRTrace,ODMRautoTrack,ODMRcw,ODMRpulsed,ODMRrabi,MountMicroWaveSequencesDirectory,
	UnmountMicroWaveSequencesDirectory,MicroWaveSequencesDirectoryMountedQ,ODMRmultiLineFit];
$ODMRcontrolHost="nfp26";
$ODMRcontrolProgram="/home/nfp/git/ODMRtools/ODMRLink/Default/ODMRLink";
$ODMRsharedMemoryLinkName="ODMRLink_shm";
$ODMRgroupUser="nfp";
$ODMRmicrowaveSequencesDirectory="/home/nfp/tekawg520";
$ODMRmicrowaveSequencesRemoteDirectory="/home/nfp/tekawg520";
$ODMRmicrowaveSequencesDirectoryMounted=False;
$ODMRfpgaClock=80*^6;
$ODMRnumCounters=2;
$ODMRdetectionDelay=287.5*^-9;
$ODMRgpibDefaultTimeout=12;
{$ODMRgroupUserId,$ODMRgroupId,$ODMRgroup}=
	{#[[1,1]],#[[2,1]],#[[2,2]]}&[{"uid","gid"}/.#]&[
		Switch[#1,"uid"|"gid",#1->ToExpression@StringSplit[#2, "(" | ")"], 
			_,#1->#2]&@@StringSplit[#,"="]&/@ 
		StringSplit[ReadList["!id "<>$ODMRgroupUser,String][[1]]]];

ConstructMathLinkConnectionString[host_String,ports:{Integer__}]:=
	StringJoin[Transpose[{Take[#,Length[#]-1],ConstantArray[",",Length[#]-1]}],#[[-1]]]&[
		ToString[#]<>"@"<>host&/@ports];
Options[InitODMR]={LocalControlPorts->{50503,50504},RemoteControlPorts->{50503,50504},
	RemoteControlProgramPath->$ODMRcontrolProgram,RemoteControlHost->$ODMRcontrolHost,
	CounterDevice->"/dev/ttyUSB2",CounterBaudrate->4000000,
	LaserControlDevice->"/dev/ttyUSB0",LaserControlBaudrate->19200,
	MicrowaveGPIBidentifier->"smiq06b",PulseSequencerGPIBidentifier->"awg520"};
InitODMR[o:OptionsPattern[]]:=
	Module[{localPorts=OptionValue[LocalControlPorts],remotePorts=OptionValue[RemoteControlPorts],
			controlProgram=OptionValue[RemoteControlProgramPath],
			remoteHost=OptionValue[RemoteControlHost]},
		$ODMRcontrolProcess=If[$VersionNumber<10,Run[#<>" &"],StartProcess@StringSplit[#]]&@
			If[remoteHost=="localhost",
				"sudo -u "<>$ODMRgroupUser<>" "<>controlProgram
				<>" -linkcreate -linkprotocol SharedMemory -linkname "
				<>$ODMRsharedMemoryLinkName,
				"sudo -u "<>$ODMRgroupUser<>" ssh -o ExitOnForwardFailure=yes"
				<>StringJoin[" -L localHost:"<>ToString[#[[1]]]<>
					":localhost:"<>ToString[#[[2]]]&/@Transpose[{localPorts,remotePorts}]]
				<>" "<>$ODMRcontrolHost<>" "<>controlProgram
				<>" -linkcreate -linkprotocol TCPIP -linkname "
				<>ConstructMathLinkConnectionString["localhost",remotePorts]];
		Pause[1];
		$ODMRlink = If[remoteHost=="localhost",
				LinkConnect[$ODMRsharedMemoryLinkName,LinkProtocol->"SharedMemory"],
				LinkConnect[ConstructMathLinkConnectionString["localhost",localPorts],
					LinkProtocol->"TCPIP"]];
		Install[$ODMRlink];
		$ODMRstage = MCLInitHandle[];
		$ODMRcounter = SerialOpen[OptionValue[CounterDevice],OptionValue[CounterBaudrate]];
		$ODMRlaser = SerialOpen[OptionValue[LaserControlDevice],OptionValue[LaserControlBaudrate]];
		$ODMRsmiq=GPIBFindDevice[OptionValue[MicrowaveGPIBidentifier]];
		$ODMRawg=GPIBFindDevice[OptionValue[PulseSequencerGPIBidentifier]];
		MoveStage[GetStageRange[]/2];
		ResetTriggeredCountingData[];
		SetTriggeredCountingBinRepetitions[1];
		SetCounterPredelay[0];
		SetCounterCountingTime[0.01];
		SetTriggerMask[{0,0,0,0,1}];
		GPIBcmd[$ODMRsmiq,"*RST"];
		GPIBcmd[$ODMRawg,"*RST"];
		GPIBcmd[$ODMRawg,"DISPLAY:BRIGHTNESS 0.1"];
		GPIBcmd[$ODMRawg,":ROSCILLATOR:SOURCE EXTERNAL"];
		GPIBcmd[$ODMRawg,"SOURCE1:MARKER1:DELAY 0"];
		GPIBcmd[$ODMRawg,"SOURCE1:MARKER1:VOLTAGE:LOW 0"];
		GPIBcmd[$ODMRawg,"SOURCE1:MARKER1:VOLTAGE:HIGH 1"];
		GPIBcmd[$ODMRawg,"SOURCE1:MARKER2:DELAY 0"];
		GPIBcmd[$ODMRawg,"SOURCE1:MARKER2:VOLTAGE:LOW 0"];
		GPIBcmd[$ODMRawg,"SOURCE1:MARKER2:VOLTAGE:HIGH 2"];
		GPIBcmd[$ODMRawg,"SOURCE2:MARKER1:DELAY 0"];
		GPIBcmd[$ODMRawg,"SOURCE2:MARKER1:VOLTAGE:LOW 0"];
		GPIBcmd[$ODMRawg,"SOURCE2:MARKER1:VOLTAGE:HIGH 1"];
		GPIBcmd[$ODMRawg,"SOURCE2:MARKER2:DELAY 0"];
		GPIBcmd[$ODMRawg,"SOURCE2:MARKER2:VOLTAGE:LOW 0"];
		GPIBcmd[$ODMRawg,"SOURCE2:MARKER2:VOLTAGE:HIGH 2"];
		EnableAOM[];
		{$ODMRcontrolProcess,$ODMRlink,$ODMRstage,$ODMRcounter,$ODMRlaser,$ODMRsmiq,$ODMRawg}
];
DeinitODMR[]:=(
	If[NumberQ[$ODMRawg],GPIBCloseDevice[$ODMRawg];$ODMRawg=.];
	If[NumberQ[$ODMRsmiq],GPIBCloseDevice[$ODMRsmiq];$ODMRsmiq=.];
	If[NumberQ[$ODMRlaser],SerialClose[$ODMRlaser];$ODMRlaser=.];
	If[NumberQ[$ODMRcounter],SerialClose[$ODMRcounter];$ODMRcounter=.];
	If[NumberQ[$ODMRstage],MCLReleaseHandle[$ODMRstage];$ODMRstage=.];
	If[Head[$ODMRlink]===LinkObject,LinkClose[$ODMRlink];$ODMRlink=.];
	(*If[Head[$ODMRcontrolProcess]===ProcessObject,$ODMRcontrolProcess=.]*);
	If[$ODMRmicrowaveSequencesDirectoryMounted,UnmountMicroWaveSequencesDirectory[]];
);
$ODMRLockLink[f_]:=
	If[$ODMRLinkLocked===True,f,
		CriticalSection[{$ODMRLinkLock},
			Module[{r},$ODMRLinkLocked=True;r=f;$ODMRLinkLocked=False;r]]];
SetAttributes[$ODMRLockLink,HoldFirst];

GetOutputs[]:=
	$ODMRLockLink[
		PadRight[Reverse@IntegerDigits[#,2],8]&@
		ToCharacterCode@SerialWriteAndRead[$ODMRcounter,1,1,"o"]];
SetOutputs[l:{(0|1)..}]:=
	$ODMRLockLink[
		SerialWrite[$ODMRcounter,"O"<>FromCharacterCode@
			FromDigits[Reverse@l,2]];]/;Length[l]<=8;
GetTriggerMask[]:=
	$ODMRLockLink[
		PadRight[Reverse@IntegerDigits[#,2],8]&@First@
		ToCharacterCode@SerialWriteAndRead[$ODMRcounter,1,1,"m"]];
SetTriggerMask[l:{(0|1)..}]:=
	$ODMRLockLink[
		SerialWrite[$ODMRcounter,"M"<>FromCharacterCode@
			FromDigits[Reverse@l,2]];]/;Length[l]<=8;
GetTriggerInvertMask[]:=
	$ODMRLockLink[
		PadRight[Reverse@IntegerDigits[#,2],8]&@First@
		ToCharacterCode@SerialWriteAndRead[$ODMRcounter,1,1,"q"]];
SetTriggerInvertMask[l:{(0|1)..}]:=
	$ODMRLockLink[
		SerialWrite[$ODMRcounter,"Q"<>FromCharacterCode@
			FromDigits[Reverse@l,2]];]/;Length[l]<=8;
GetCounterCountingTime[]:=
	$ODMRLockLink[(
		FromDigits[Reverse@ToCharacterCode@#,256]&@
		SerialWriteAndRead[$ODMRcounter,4,4,"t"]+1)/$ODMRfpgaClock];
SetCounterCountingTime[t_?NumberQ]:=
	$ODMRLockLink[
		SerialWrite[$ODMRcounter,"T"<>FromCharacterCode@PadRight[
			Reverse@IntegerDigits[Ceiling[Clip[t*$ODMRfpgaClock-1,{0,2^32-1}]],256],4]];];
GetCounterPredelay[]:=
	$ODMRLockLink[
		FromDigits[Reverse@ToCharacterCode@#,256]&@
		SerialWriteAndRead[$ODMRcounter,4,4,"p"]/$ODMRfpgaClock];
SetCounterPredelay[t_?NumberQ]:=
	$ODMRLockLink[
		SerialWrite[$ODMRcounter,"P"<>FromCharacterCode@PadRight[
			Reverse@IntegerDigits[Ceiling[Clip[t*$ODMRfpgaClock,{0,2^32-1}]],256],4]];];
GetNumberOfCounts[]:=
	$ODMRLockLink[
		FromDigits[Reverse@ToCharacterCode@#,256]&@
		SerialWriteAndRead[$ODMRcounter,4,4,"l"]];
SetNumberOfCounts[t_Integer?NonNegative]:=
	$ODMRLockLink[
		SerialWrite[$ODMRcounter,"L"<>FromCharacterCode@PadRight[
			Reverse@IntegerDigits[Ceiling[Clip[t,{0,2^32-1}]],256],4]];];
GetNumberOfTriggeredCountingBins[]:=
	$ODMRLockLink[
		FromDigits[Reverse@ToCharacterCode@#,256]&@
		SerialWriteAndRead[$ODMRcounter,2,2,"b"]+1];
SetNumberOfTriggeredCountingBins[t_Integer?Positive]:=
	$ODMRLockLink[
		SerialWrite[$ODMRcounter,"B"<>FromCharacterCode@PadRight[
			Reverse@IntegerDigits[Ceiling[Clip[t-1,{0,2^12-1}]],256],2]];];
GetTriggeredCountingAddress[]:=
	$ODMRLockLink[
		FromDigits[Reverse@ToCharacterCode@#,256]&@
		SerialWriteAndRead[$ODMRcounter,2,2,"a"]];
SetTriggeredCountingAddress[t_Integer?NonNegative]:=
	$ODMRLockLink[
		SerialWrite[$ODMRcounter,"A"<>FromCharacterCode@PadRight[
			Reverse@IntegerDigits[Ceiling[Clip[t,{0,2^12-1}]],256],2]];];
GetTriggeredCountingBinRepetitions[]:=
	$ODMRLockLink[
		FromDigits[Reverse@ToCharacterCode@#,256]&@
		SerialWriteAndRead[$ODMRcounter,2,2,"k"]+1];
SetTriggeredCountingBinRepetitions[t_Integer?Positive]:=
	$ODMRLockLink[
		SerialWrite[$ODMRcounter,"K"<>FromCharacterCode@PadRight[
			Reverse@IntegerDigits[Ceiling[Clip[t-1,{0,2^16-1}]],256],2]];];
GetTriggeredCountingBinRepetitionCounter[]:=
	$ODMRLockLink[
		FromDigits[Reverse@ToCharacterCode@#,256]&@
		SerialWriteAndRead[$ODMRcounter,2,2,"j"]];
EnableTriggeredCounting[]:=
	$ODMRLockLink[SerialWrite[$ODMRcounter,"R"];];
DisableTriggeredCounting[]:=
	$ODMRLockLink[SerialWrite[$ODMRcounter,"r"];];
SetSplitTriggeredCountingBins[x:(True|False)]:=
	$ODMRLockLink[
		SerialWrite[$ODMRcounter,"F"<>FromCharacterCode[#]]&@
		If[x,BitSet[#,0],BitClear[#,0]]&@
		FromDigits[Reverse@ToCharacterCode@#,256]&@
		SerialWriteAndRead[$ODMRcounter,1,1,"f"]];
GetSplitTriggeredCountingBins[]:=
	$ODMRLockLink[
		Equal[BitGet[#,0],1]&@FromDigits[Reverse@ToCharacterCode@#,256]&@
		SerialWriteAndRead[$ODMRcounter,1,1,"f"]];
Options[ReadTriggeredCountingData]:=
	{NumberOfTriggeredCountingBins->Automatic,SplitTriggeredCountingBins->Automatic};
ReadTriggeredCountingData[o:OptionsPattern[]]:=
	$ODMRLockLink[
		Module[{t=If[#===Automatic,GetNumberOfTriggeredCountingBins[],#]&@
					OptionValue[NumberOfTriggeredCountingBins],
				s=If[#===Automatic,GetSplitTriggeredCountingBins[],#]&@
					OptionValue[SplitTriggeredCountingBins]},
		If[s,Flatten[Transpose[Map[PadRight[Reverse@IntegerDigits[#,512],2]&,#,{2}],{1,3,2}],1],#]&[
			(FromDigits[Reverse@#,256]&/@Partition[#,3])&/@Partition[#,$ODMRnumCounters*3]&@
			ToCharacterCode@SerialWriteAndRead[$ODMRcounter,
				$ODMRnumCounters*3*t,$ODMRnumCounters*3*t,"d"]]]];
ResetTriggeredCountingData[]:=
	$ODMRLockLink[SerialWrite[$ODMRcounter,"0"];];
TriggerCounter[]:=
	$ODMRLockLink[SerialWrite[$ODMRcounter,"!"]];
CountCounters[]:=
	$ODMRLockLink[
		FromDigits[Reverse@#,256]&/@Partition[ToCharacterCode[#],4]&
		@SerialWriteAndRead[$ODMRcounter,8,8,"C"]];
CountCounters[numSamples_Integer?NonNegative]:=
	$ODMRLockLink[
		ODMRGatherTrace[$ODMRcounter,numSamples]];

TrackConfocalMaximum[counterId_Integer,{x0_?NumericQ,y0_?NumericQ,z0_?NumericQ},stepSize_?Positive,
		st_?NonNegative,iFactor_?Positive,numSamples_Integer?NonNegative]:=
	$ODMRLockLink[
		ODMRTrackMaximum[$ODMRstage,$ODMRcounter,1,N@{x0,y0,z0},N@stepSize,N@st,N@iFactor,numSamples]
	];
ReadStage[]:=$ODMRLockLink[MCLSingleReadXYZ[$ODMRstage]];
MoveStage[{x_?NumericQ,y_?NumericQ,z_?NumericQ}]:=
	$ODMRLockLink[MCLMonitorXYZ[{x,y,z},$ODMRstage]];
GetStageRange[]:=$ODMRLockLink[MCLGetCalibrationXYZ[$ODMRstage]];

Options[ScanConfocalImage]=
	{CountingTime->0.003,SettlingTime->0.001,BacktraceTime->(10#&),ZigZagScan->False,
		ImageMergingFunction->Total,TiltCorrection->False,
		PreviewFunction->(PlotConfocalImage[ReplacePart[#1[[1]],1->Total[#1[[All,1]]]]]&)};
ScanConfocalImage[xAxis:1|2|3,xmin_?NumericQ,xmax_?NumericQ,nx_Integer?Positive,
		yAxis:1|2|3,ymin_?NumericQ,ymax_?NumericQ,ny_Integer?Positive,z_?NumericQ,
		options:OptionsPattern[]]:=
	$ODMRLockLink[
		Module[{x0,y0,z0,dt0,dt=OptionValue[CountingTime],st=OptionValue[SettlingTime],
			bt=OptionValue[BacktraceTime],zAxis=Complement[{1,2,3},{xAxis,yAxis}][[1]],
			abort=False,imageData=ConstantArray[{0,0},{ny,nx}],zigZag=OptionValue[ZigZagScan],
			i=0,y,dz,previewFunction=OptionValue[PreviewFunction],
			mergingFunction=OptionValue[ImageMergingFunction],
			tiltCorrection=(#/.False->None)&/@
				Switch[#,{(_?NumericQ)|False|None,(_?NumericQ)|False|None},#,
					(_?NumericQ)|False|None,{#,#},_,{None,None}]&@
				OptionValue[TiltCorrection],
			orderAxes,
			generateImagesFromData=Function[data,
				Switch[{xAxis,yAxis},{2,1}|{3,1|2},TransposeConfocalImage[#],_,#]&
				@ConfocalImage[#,{"area"->{xmax-xmin,ymax-ymin}*10^-6,
					"offset"->{xmin,ymin}*10^-6,{"X","Y","Z"}[[Complement[Range[3],
						{xAxis,yAxis}][[1]]]]->z},""]&/@Transpose[data,{2,3,1}]]},
			If[Head[bt]===Function,bt=bt[st]];
			{x0,y0,z0}=MCLSingleReadXYZ[$ODMRstage];
			dt0=GetCounterCountingTime[];
			SetCounterCountingTime[dt];
			orderAxes=Function[axes,Function[xyz,#[[2]]&/@SortBy[Transpose[{axes,xyz}],First]]]@
				{xAxis,yAxis,zAxis};
			Monitor[
				For[i=1,i<=ny,i++,
					y=ymin+(i-1/2)*(ymax-ymin)/ny;
					dz=If[NumericQ[#],(y-(ymin+ymax)/2)*Tan[#],0]&@tiltCorrection[[2]];
					If[abort,Break[]];
					imageData[[i]]=Module[{d=If[zigZag,2Mod[i,2]-1,1]},
						If[d<0,Reverse[#],#]&@
						If[NumericQ[#],
							ODMRScanLine[$ODMRstage,$ODMRcounter,
								N@orderAxes@{xmin+(xmax-xmin)/(2*nx),
									y,z+dz-(xmax-xmin)/2*Tan[#]},
								N@orderAxes@{xmax-(xmax-xmin)/(2*nx),
									y,z+dz+(xmax-xmin)/2*Tan[#]},
								nx,N@If[zigZag,st,bt],N@st],
							ODMRScanLine[$ODMRstage,$ODMRcounter,
								xAxis,
								Sequence@@(If[d<0,Reverse[#],#]&[
									N@{xmin+(xmax-xmin)/(2*nx),
										xmax-(xmax-xmin)/(2*nx)}]),
								nx,
								Sequence@@(
									N@Switch[{xAxis,yAxis},
										{1,2}|{2,3}|{3,1},{y,z+dz},
										{2,1}|{3,2}|{1,3},{z+dz,y}]),
								N@If[zigZag,st,bt],N@st],
						]&@tiltCorrection[[1]]/dt]
				],{Button["abort",abort=True],
					previewFunction[generateImagesFromData[imageData],i/ny]}];
			SetCounterCountingTime[$ODMRcounter,dt0];
			MCLSingleWriteXYZ[{x0,y0,z0},$ODMRstage];
			Function[images,If[mergingFunction=!=Null,
				MapAt[Map[mergingFunction,Transpose[First/@images,{3,1,2}],{2}]&,
					images[[1]],1],
				images]]@generateImagesFromData[imageData]
		]]/;xAxis!=yAxis;
CropConfocalImage[a_ConfocalImage,newOffset:{_?NumericQ,_?NumericQ},
		newArea:{_?NumericQ,_?NumericQ}]:=
	MapIndexed[
		Switch[#2[[1]],
			1,Function[{off,area},
				Take[Drop[#,Ceiling[(off/area)[[1]]Length[#]]],Floor[(newArea/area)[[1]]Length[#]]]&
				/@Take[Drop[#,Ceiling[(off/area)[[2]]Length[#]]],Floor[(newArea/area)[[2]] Length[#]]]
			][newOffset-("offset"/.a[[2]]),"area"/.a[[2]]],
			2,#1/.{("offset"->_)->("offset"->newOffset),("area"->_)->("area"->newArea),
				("pixels"->l_):>("pixels"->(l-{1,1}) newArea/("area"/.a[[2]])+{1,1})},
			_,#1]&
		,a];
TransposeConfocalImage[a_ConfocalImage]:=
	MapIndexed[Switch[#2[[1]],
		1,Transpose[#1],
		2,#1/.r:("area"|"offset"->{_,_}):>MapAt[Reverse,r,2],_,#1]&,a];

GPIBcmd[dev_Integer?NonNegative,cmd_String,bufferSize:(_Integer?NonNegative):0]:=
	$ODMRLockLink[
		GPIBSend[dev,cmd];
		If[bufferSize>0,GPIBReceive[dev,bufferSize]]];
GPIBqueryNumber[dev_Integer?NonNegative,name_String]:=
	$ODMRLockLink[
		ToExpression@StringReplace[StringTrim@
		GPIBcmd[dev,name<>"?",1024],"E"|"e"->"*^"]];
SerialCmd[dev_Integer?NonNegative,cmd_String]:=
	$ODMRLockLink[SerialWriteLine[dev,cmd];SerialReadLine[dev]];
SerialQueryNumber[dev_Integer?NonNegative,name_String]:=
	$ODMRLockLink[
		ToExpression@StringReplace[StringTrim@
		SerialCmd[dev,name<>"?"],"E"|"e"->"*^"]];
SerialTMCqueryNumber[dev_Integer?NonNegative,name_String]:=
	$ODMRLockLink[
		ToExpression@StringReplace[StringTrim@
		SerialTMCcmd[dev,name<>"?",1024],"E"|"e"->"*^"]];
(*Module[{
	nb=NotebookOpen[
		"/home/john/git/Academic/Bachelorarbeit/Bilder/ImageConstructionFunctions.nb"]},
	NotebookEvaluate[nb];NotebookClose[nb]];*)
Options[PlotConfocalImage]=Join[{MinCounts->Min,MaxCounts->Max,
		ColorFunction->(ColorData["SunsetColors"][Clip[#1,{0,1}]]&),
		ColorScaleFunction->Identity},Options[Graphics]];
PlotConfocalImage[data_ConfocalImage,options:OptionsPattern[]]:=
	Function[{imageData,dataUnit,offset,area,lengthUnit,axes,min,max},
		Module[{cf=Function[{f,g,h},f[g[h[#1]]]&][OptionValue[ColorFunction],
					OptionValue[ColorScaleFunction],If[min!=max,(#-min)/(max-min)&,1/2&]]},
			{Graphics[Raster[Map[List@@cf[#]&,imageData,{2}],{offset,offset+area}],
				Sequence@@FilterRules[{options},Options[Graphics]],
				ImageSize->96/25.4 100,Frame->True,
				FrameLabel->({"x","y","z"}[[#]]<>"("<>lengthUnit<>")"&/@axes)],
			ConfocalImageColorLegend[{min,max},ColorFunction->cf,BarLabel->dataUnit]}]
	][10^-3 #1,"kCounts",10^6 #2,10^6 #3,"\[Mu]m",#4,
	10^-3Function[{f,d},If[NumericQ[f],f,f[d]]][OptionValue[MinCounts],#1],
	10^-3Function[{f,d},If[NumericQ[f],f,f[d]]][OptionValue[MaxCounts],#1]]&[
		#[[1]],"offset"/.#[[2]],"area"/.#[[2]],Complement[Range[3],
			Cases[#[[2]],(x:("X"|"Y"|"Z")->_):>Position[{"X","Y","Z"},x][[1,1]]]]]&[data];
SetAttributes[PlotConfocalImage,Listable];
ConfocalImageColorLegend[r:_?NumericQ|{_?NumericQ,_?NumericQ},
		o:OptionsPattern[{AspectRatio->10,BarLabel->None,ColorSteps->100,RasterColorMap->False,
			ColorFunction->Automatic}]]:=
	Module[{range=If[Length[r]==2,r,{0,r}],ar=OptionValue[AspectRatio],
			steps=OptionValue[ColorSteps],cf=OptionValue[ColorFunction],
			rasterColorMap=OptionValue[RasterColorMap],nullRange},
		If[nullRange=range[[1]]==range[[2]],range={0,1}];
		If[cf===Automatic,cf=If[nullRange,Black&,
			ColorData["SunsetColors"][(#-range[[1]])/(range[[2]]-range[[1]])]&]];
		Graphics[If[rasterColorMap,
			Inset[ImageResize[Image[#,FilterRules[{o},Options[Image]]],steps{1/ar,1}],
				{0,range[[1]]},{0,0},{1,range[[2]]-range[[1]]}],#]&
			@Raster[Transpose@{List@@cf[#]&
					/@Range[range[[1]]+1/(2steps),range[[2]]-1/(2steps),(range[[2]]-range[[1]])/steps]},
				Transpose@{{0,1},range}],FilterRules[{o},Options[Graphics]],
			PlotRange->{{0,1},range},Frame->True,FrameTicks->{{None,All},{None,None}},
			FrameLabel->{{None,OptionValue[BarLabel]},{None,None}},PlotRangePadding->None,
			ImageMargins->None,ImagePadding->Automatic,AspectRatio->ar]
	];
ScanConfocalVolume[xmin_?NumericQ,xmax_?NumericQ,
		nx_Integer?Positive,ymin_?NumericQ,ymax_?NumericQ,ny_Integer?Positive,zmin_?NumericQ,zmax_?NumericQ,
		nz_Integer?Positive,dt_?Positive,st_?NonNegative,o:OptionsPattern[]]:=
	$ODMRLockLink[Module[{x0,y0,z0,dt0,ig=0,data,btt=BackTraceTime/.{o}/.BackTraceTime->10st},
			{x0,y0,z0}=MCLSingleReadXYZ[$ODMRstage];
		MCLSingleWriteXYZ[{xmin,ymin,zmin},$ODMRstage];
			dt0=GetCounterCountingTime[];
			SetCounterCountingTime[dt];
			If[Head[btt]===Function,btt=btt[st]];
			data=Monitor[
				Function[{z,i},
					ig=i;
					Transpose@ODMRScanArea[$ODMRstage,$ODMRcounter,
2,N@ymin,N@ymax,ny,1,N@xmin,N@xmax,nx,N@z,N@btt,N@btt,N@st]/dt
				]@@#&/@Transpose[{#,Range[Length[#]]}]&
				@Range[zmin,zmax,(zmax-zmin)/(nz-1)],ProgressIndicator[ig/ny]];
			SetCounterCountingTime[$ODMRcounter,dt0];
			MCLSingleWriteXYZ[{x0,y0,z0},$ODMRstage];
			data
		]
	];
Options[FindNV]=
	{NumSamplesPerDirection->11,CountingTime->0.025,SettlingTime->0.001,
		BackTraceTime->(10#&),ScanVolumeSize->{1,1,2},FindCycles->7/3,
		MaxCoordinateError->0.25,MaxCoordinateCorrection->{0.5,0.5,1},MinimumRSquared->0.75};
FindNV[{x0s_?NumericQ,y0s_?NumericQ,z0s_?NumericQ},o:OptionsPattern[]]:=
	$ODMRLockLink[Module[
		{i,dt0=GetCounterCountingTime[],dt=OptionValue[CountingTime],st=OptionValue[SettlingTime],
			btt=OptionValue[BackTraceTime],minRSquared=OptionValue[MinimumRSquared],
			n,w,\[Sigma]s={0.5,0.5,1},x,y,z,
			\[Sigma]x,\[Sigma]y,\[Sigma]z,xyz,x0,y0,z0,bg,snr,\[Phi],
			data=Null,fit=Null,image=Null,repetitions=Ceiling[3*OptionValue[FindCycles]],
			maxCoordinateError=OptionValue[MaxCoordinateError],
			maxCoordinateCorrection=OptionValue[MaxCoordinateCorrection],
			quit=False,resultList={,,}},
	{n,w} = Switch[#,{_?Positive,_?Positive,_?Positive},#,{_?Positive,_?Positive},{#[[1]],#[[1]],#[[2]]},
			_?Positive,{#,#,#}]&@OptionValue[#]&/@{NumSamplesPerDirection, ScanVolumeSize};
	SetCounterCountingTime[dt];
	xyz = {x0s,y0s,z0s};
	If[Head[btt]===Function,btt=btt[st]];
	Monitor[For[i=1,i<=repetitions,i++,
		If[quit,Break[]];
		Module[{xAxis,yAxis,zAxis=3-Mod[i-1,3],u,v,u0,v0,\[Sigma]u,\[Sigma]v},
		{xAxis,yAxis}=Complement[Range[3],{zAxis}];
		{{u,v},{u0,v0},{\[Sigma]u,\[Sigma]v}}=Function[axis,#[[axis]]]/@{xAxis,yAxis}&/@
			{{x,y,z},{x0,y0,z0},{\[Sigma]x,\[Sigma]y,\[Sigma]z}};
	        data=Map[Total,#,{2}]&@Transpose@ODMRScanArea[$ODMRstage,$ODMRcounter,
			yAxis,N@(xyz-w/2)[[yAxis]],N@(xyz+w/2)[[yAxis]],n[[yAxis]],
			xAxis,N@(xyz-w/2)[[xAxis]],N@(xyz+w/2)[[xAxis]],n[[xAxis]],
			N@xyz[[zAxis]],N@btt,N@btt,N@st]/dt;
		resultList[[zAxis]]={,};
		image = Function[{xRange,yRange},
				PlotConfocalImage[ConfocalImage[data,
					{"area"->{xRange[[2]]-xRange[[1]],yRange[[2]]-yRange[[1]]}*10^-6, 
						"offset"->{xRange[[1]],yRange[[1]]}*10^-6,
						{"X","Y","Z"}[[zAxis]]->xyz[[zAxis]]}], 
					ImageSize->60*96/25.4,AspectRatio->1]]@@
				Transpose[{(xyz-w/2)[[{xAxis,yAxis}]],(xyz+w/2)[[{xAxis,yAxis}]]}];
		resultList[[zAxis]]={image,};
		fit = Quiet@NonlinearModelFit[#,
			bg*(1+(snr-1)*E^(-(1/2)*((u-u0)^2/\[Sigma]u^2+(v-v0)^2/\[Sigma]v^2
			+(u-u0)*(v-v0)*Tan[2*\[Phi]*Pi/180]*(1/\[Sigma]u^2-1/\[Sigma]v^2)))),
			{{u0,xyz[[xAxis]]},{v0,xyz[[yAxis]]},
				{\[Sigma]u,\[Sigma]s[[xAxis]]},{\[Sigma]v,\[Sigma]s[[yAxis]]},{\[Phi],0},
				{bg,Mean[#[[3]]&/@#]},{snr,2}},{u,v}]&@Flatten[#, 1]&@Map[Append@@#&,#,{2}]&
			@Transpose[{Table[{ix,iy},
				{iy,(xyz-w/2)[[yAxis]],(xyz+w/2)[[yAxis]],(w/(n-1))[[yAxis]]},
				{ix,(xyz-w/2)[[xAxis]],(xyz+w/2)[[xAxis]],(w/(n-1))[[xAxis]]}],data},{3,1,2}];
		resultList[[zAxis]]={MapAt[Show[#,Function[{u,v,\[Sigma]u,\[Sigma]v,\[Phi]},
			Graphics[{Green,Translate[#,{u[[1]],v[[1]]}]&@Rotate[#,\[Phi][[1]]*Pi/180]&/@
				{Circle[{0,0},Subtract@@@Abs@{\[Sigma]u,\[Sigma]v}],
					Circle[{0,0},Plus@@@Abs@{\[Sigma]u,\[Sigma]v}]}}]]
			@@Take[fit["ParameterTableEntries"],5,2]
			]&,image,1],{fit["ParameterTable"],fit["RSquared"],
				RootMeanSquare@fit["FitResiduals"]}};
		If[fit["RSquared"]>=minRSquared,xyz = ReplacePart[xyz,Flatten[#]]&[
			If[#[[2,2]]<=maxCoordinateError\[And]
					Abs[#[[2,1]]-xyz[[#[[1]]]]]<=maxCoordinateCorrection[[#[[1]]]],
				{#[[1]]->#[[2,1]]},{}]&/@ 
			Transpose[{{xAxis,yAxis},Take[#,2]}]]&@fit["ParameterTableEntries"]];
	]],{Button["quit",quit=True],ProgressIndicator[i/repetitions],xyz,resultList}];
	MoveStage[xyz];
	Pause[st];
	data = Total@Mean@CountCounters[10]/dt;
	SetCounterCountingTime[dt0];
	{xyz, data}]];

MountMicroWaveSequencesDirectory[]:=
	If[Length[#]>0,StringJoin[Riffle[#,"\n"]],$ODMRmicrowaveSequencesDirectoryMounted=True;]&@
		ReadList["!"<>
			"sudo -u "<>$ODMRgroupUser<>" sshfs -o uid="<>ToString[$ODMRgroupUserId]
			<>" -o gid="<>ToString[$ODMRgroupId]<>" -o allow_other "<>$ODMRcontrolHost
			<>":"<>$ODMRmicrowaveSequencesRemoteDirectory
			<>" "<>$ODMRmicrowaveSequencesDirectory
			<> " 2>&1",String];
UnmountMicroWaveSequencesDirectory[]:=
	If[Length[#]>0,StringJoin[Riffle[#,"\n"]],$ODMRmicrowaveSequencesDirectoryMounted=False;]&@
		ReadList["!"<>
			"sudo -u "<>$ODMRgroupUser<>" fusermount -u "<>$ODMRmicrowaveSequencesDirectory
			<> " 2>&1",String];
MicroWaveSequencesDirectoryMountedQ[]:=
	Switch[Length[#],0,False,1,True,_,$Failed[#]]&@Select[#,StringMatchQ[#, 
		$ODMRcontrolHost<>":"<>$ODMRmicrowaveSequencesRemoteDirectory
		<>" on "<>$ODMRmicrowaveSequencesDirectory
		<>" type fuse.sshfs (rw,nosuid,nodev,allow_other,user="<>$ODMRgroupUser<>")"]&]&@
	ReadList["!mount", String];
ReadAWGwfm[fileName_String,o:OptionsPattern[{MarkerCount->2}]]:=
	Module[{file,d,l,data},
		If[!MicroWaveSequencesDirectoryMountedQ[],MountMicroWaveSequencesDirectory[]];
		If[!FileExistsQ[FileNameJoin[{$ODMRmicrowaveSequencesDirectory,fileName}]],
			Print["file does not exist"];Return[{}]];
		file=OpenRead[FileNameJoin[{$ODMRmicrowaveSequencesDirectory,fileName}],BinaryFormat->True];
		data=BinaryReadList[file];
		Close[file];
		Switch[FromCharacterCode[data[[1;;12]]],
			"MAGIC 1000\r\n",
			If[FromCharacterCode[data[[13]]]!="#",Print["no length descriptor"];Return[{}]];
			If[!DigitQ@FromCharacterCode[data[[14]]],
				Print["no length of length digit"];Return[{}]];
			d=ToExpression@FromCharacterCode[data[[14]]];
			l=ToExpression[FromCharacterCode@data[[14+1;;14+d]]];
			AWGwfm[MapAt[Sequence@@#&,#,2]&/@Transpose[
				{ImportString[FromCharacterCode@Flatten[#1],"Real32"],
				(Function[p,BitGet[#,p]]/@Range[0,Clip[OptionValue[MarkerCount],{0,8}]-1]&/@#2)}]&
				@@Transpose[{#[[1;;4]],#[[5]]}&/@Partition[data[[15+d;;14+d+l]],5]],
				If[Length[#]>=2,Switch[ToUpperCase[#[[1]]],
				"CLOCK","CLOCK"->ToExpression[StringReplace[#[[2]],"e"|"E"->"*^"]],_,]]&[
					StringSplit[#]]&/@StringSplit[FromCharacterCode@data[[15+d+l;;]],"\n"]
						//DeleteCases[#,Null]&],
			"MAGIC 3002\r\n",
			Module[{lines=StringTrim/@StringSplit[FromCharacterCode[data[[13;;]]],"\r\n"],numLines},
				If[StringMatchQ[lines[[1]],RegularExpression["LINES [0-9]+"]],
					numLines=ToExpression[StringSplit[lines[[1]]][[2]]],
					Print["invalid number of lines descriptor, ignoring..."];
					numLines=0;While[numLines<Length[lines]-1\[And]
						StringMatchQ[lines[[numLines+2]],
							RegularExpression["\".*\"\\s*,\\s*\".*\"\\s*,\\s*[0-9]+\\s*,"
								<>"\\s*(0|1)\\s*,\\s*(0|1)\\s*,\\s*([0-9]+|-1)"]],
						numLines++]];
				If[numLines<Length[lines]-1,Print["ignoring logic jump specifications..."]];
				AWGseq@MapIndexed[
					If[StringMatchQ[#1,
						RegularExpression["\".*\"\\s*,\\s*\".*\"\\s*,\\s*[0-9]+\\s*,"
								<>"\\s*(0|1)\\s*,\\s*(0|1)\\s*,\\s*([0-9]+|-1)"]],
						{#1,#3,Sequence@@(ToExpression/@StringSplit[StringTrim[#4],","])}&
							@@StringSplit[#1,"\""],
						Print["invalid line("<>ToExpression[#2[[1]]+2]<>"): "<>#1];Return[{}]]&,
					lines[[2;;numLines+1]]]
			],
			_,Print["no magic code"];{}]
	];
WriteAWGwfm[fileName_String,AWGwfm[data:{_List...}/;And@@((And@@(NumberQ/@#))&/@data),
			options:{(_Rule|_RuleDelayed)...}:{}]]:=
	Module[{file},
		If[!MicroWaveSequencesDirectoryMountedQ[],MountMicroWaveSequencesDirectory[]];
		file=OpenWrite[FileNameJoin[{$ODMRmicrowaveSequencesDirectory,fileName}],BinaryFormat->True];
		BinaryWrite[file,"MAGIC 1000\r\n"];
		BinaryWrite[file,StringJoin["#",ToString[StringLength[#]],#]&@ToString[5Length[data]]];
		BinaryWrite[file,StringJoin@Transpose[
			{Partition[Characters@ExportString[#1,"Real32"],4],
				Characters@ExportString[FromDigits[Boole[#>=0.5]&/@Reverse[#],2]&/@#2,
					"Integer8"]}]&@@Transpose[{#[[1]],Rest[#]}&/@data]];
		Switch[ToUpperCase[#[[1]]],
			"CLOCK",BinaryWrite[file,"CLOCK "<>ToString[#[[2]],CForm]<>"\r\n"]]&/@options;
		Close[file]
	];
WriteAWGwfm[fileName_String,
		AWGseq[seq:{{_String,_String,_Integer?(0<=#<=65536&),0|1,0|1,_Integer?(-1<=#<=8000&)}...},
		options:OptionsPattern[]]]:=
	Module[{file},
		If[!MicroWaveSequencesDirectoryMountedQ[],MountMicroWaveSequencesDirectory[]];
		file=OpenWrite[FileNameJoin[{$ODMRmicrowaveSequencesDirectory,fileName}],BinaryFormat->True];
		BinaryWrite[file,"MAGIC 3002\r\n"];
		BinaryWrite[file,"LINES "<>ToString[Length[seq]]<>"\r\n"];
		BinaryWrite[file,"\""<>#1<>"\", \""<>#2<>"\","<>ToString[#3]<>","<>ToString[#4]<>
			 ","<>ToString[#5]<>","<>ToString[#6]<>"\r\n"]&@@#&/@seq;
		Close[file]
	];
GetAWGwfmDurationAndClockRate[fileName_String,options:OptionsPattern[ClockRate->Automatic]]:=
	Module[{fCache={}, i, cf = "",duration={0,0},dcf,clock=OptionValue[ClockRate]},
			dcf=Function[f,cf=f;i=Position[fCache,f->_,1];
				If[Length[i]>0,
					fCache[[i[[1,1]],2]], 
	        			(fCache=Append[fCache,f->#];#)&@(duration+=#;#)&@
					Switch[Head[#],
						AWGwfm,If[clock==Automatic,
							clock="CLOCK"/.#[[2]]/."CLOCK"->Automatic];
						Length[#[[1]]],
						AWGseq,Total[Function[{f1, f2, r, t, g, l},
							r(dcf/@{f1,f2})]@@#&/@#[[1]]],
						_,Print["invalid file: "<>f];{0,0}]&@ReadAWGwfm[f]]];
		Monitor[dcf[fileName],{cf,duration,fCache}]//{#/clock,clock}&
	  ];
GetAWGwfmDuration[fileName_String,options:OptionsPattern[{ClockRate->Automatic}]]:=
	First@GetAWGwfmDurationAndClockRate[fileName,options];
Options[ConstructMicrowaveSequence]=
	{ClockRate->100*^6,PreMicrowaveDelay->1*^-6,MicrowaveSwitchDelay->13*^-9,
	PulseModulationDelay->235*^-9,IQModulationDelay->65*^-9,UseMicrowaveSwitch->True,
	PostMicrowaveDelay->10*^-9,LaserPulseLength->3*^-6,LaserDelay->236*^-9,
	ChannelMap->{"laser"->{{0,0,0},{0,1,0}},"mwPulse"->{{0,0,0},{0,0,1}},
		"mwSwitch"->{{0,0,1},{0,0,0}},"trigger"->{{0,1,0},{0,0,0}},
		"mwI"->{{1,0,0},{0,0,0}},"mwQ"->{{0,0,0},{1,0,0}}},
	TriggerOffset->0,TriggerPulseLength->Automatic,KeepLaserOn->False,
	Repetitions->1000,OptimizeLaserOnOff->True,ShowPlots->False,
	AppendRepetitionsToSequenceFileName->True};
ConstructMicrowaveSequence[microwavePattern:{{_?NumericQ,__Function}..},
		fileNamePrefix_String,options:OptionsPattern[]]:=
	Module[{
		clockRate=OptionValue[ClockRate],
		preMicrowaveDelay=OptionValue[PreMicrowaveDelay],
		microwaveSwitchDelay=OptionValue[MicrowaveSwitchDelay],
		pulseModulationDelay=OptionValue[PulseModulationDelay],
		useMicrowaveSwitch=(OptionValue[UseMicrowaveSwitch]===True),
		iqModulationDelay=OptionValue[IQModulationDelay],
	  	postMicrowaveDelay=OptionValue[PostMicrowaveDelay],
		laserPulseLengths=OptionValue[LaserPulseLength],
		laserdelay=OptionValue[LaserDelay],
		keepLaserOn=(OptionValue[KeepLaserOn]===True),
		channelMap=OptionValue[ChannelMap],
		repetitions=OptionValue[Repetitions],
		optimizeLaserOnOff=(OptionValue[OptimizeLaserOnOff]===True),
		showPlots=OptionValue[ShowPlots]===True,
		n=Length[microwavePattern],
		microwaveDurations=FoldList[Plus,0,First/@microwavePattern],
		triggerOffsets=OptionValue[TriggerOffset],
		triggerPulseLength=If[#===Automatic,1/OptionValue[ClockRate],#]&@
			OptionValue[TriggerPulseLength],
		x,pulse=Function[{s,w},Function[t,Piecewise[{{1,s<=t<s+w}},0]]]},
		laserPulseLengths=If[ListQ[#],Take[PadRight[#,n,#[[-1]]],n],ConstantArray[#,n]]&@
			laserPulseLengths;
		laserPulseDurations=FoldList[Plus,0,laserPulseLengths];
		triggerOffsets=Switch[#,{(_?NumericQ)..},ConstantArray[#,n],
			{(_List|_?NumericQ)..},If[ListQ[#],#,{#}]&/@#,
			_?NumericQ,ConstantArray[{#},n]]&@triggerOffsets;
		Array[Function@@
			Module[{t=(x-1)/clockRate},
				{x,If[keepLaserOn,"laser",0]+Sum[
				Function[s,"laser"*If[keepLaserOn,0,pulse[s,laserPulseLengths[[i]]][t]]
					+"trigger"*Total[pulse[s+#,triggerPulseLength][t]&/@
						triggerOffsets[[i]]]][
					i*(preMicrowaveDelay+postMicrowaveDelay)
							+laserPulseDurations[[i]]
							+microwaveDurations[[i+1]]]
				+Function[s,
					If[useMicrowaveSwitch,
						pulse[s-microwaveSwitchDelay,microwavePattern[[i,1]]][t]
							*"mwSwitch",
						pulse[s-pulseModulationDelay,microwavePattern[[i,1]]][t]
							*"mwPulse"]
						*microwavePattern[[i,2]][t-s]
					+pulse[s-iqModulationDelay,microwavePattern[[i,1]]][t]*
						("mwI"*If[Length[microwavePattern[[i]]]>=3,
								microwavePattern[[i,3]][t-s],0]
						+"mwQ"*If[Length[microwavePattern[[i]]]>=4,
								microwavePattern[[i,4]][t-s],0])
					+If[!useMicrowaveSwitch,
						pulse[s-microwaveSwitchDelay,microwavePattern[[i,1]]][t]
							*"mwSwitch",
						pulse[s-pulseModulationDelay,microwavePattern[[i,1]]][t]
							*"mwPulse"]
						*If[Length[microwavePattern[[i]]]>=5,
							microwavePattern[[i,5]][t-s],0]][
					i*preMicrowaveDelay+(i-1)*postMicrowaveDelay+laserPulseDurations[[i]]
					+microwaveDurations[[i]]+laserdelay
					],{i,1,n}]/.channelMap//PiecewiseExpand}], 
		          Floor[(n*(postMicrowaveDelay+preMicrowaveDelay)+laserPulseDurations[[n+1]]
					+microwaveDurations[[n+1]])*clockRate]]
		//AWGwfm[PadRight[#,Max[4 Ceiling[Length[#]/4],256],
				If[optimizeLaserOnOff,{#[[1]]},{{0,0,0}}]],
			{"CLOCK"->clockRate}]&@If[optimizeLaserOnOff,RotateRight[#],#]&/@Transpose[#]&
		//{WriteAWGwfm@@#&/@Transpose[{{fileNamePrefix<>"Ch1.wfm",fileNamePrefix<>"Ch2.wfm"}, #}], 
 			WriteAWGwfm[fileNamePrefix<>
				If[OptionValue[AppendRepetitionsToSequenceFileName]===True,
					ToString[repetitions],""]<>".seq", 
				AWGseq[{{fileNamePrefix<>"Ch1.wfm",fileNamePrefix<>"Ch2.wfm", 
					repetitions,1,0,0}}]],
			If[showPlots,ListLinePlot[Transpose[#[[1]]],PlotRange->All, 
				PlotStyle -> {Black, Green, Red}]&/@#,Sequence[]]}&
];

EnableAOM[o:OptionsPattern[{MicrowaveSwitchEnabled->False}]]:=
	(GPIBcmd[$ODMRawg,"AWGCONTROL:STOP"];
	GPIBcmd[$ODMRawg,"SOURCE2:FUNCTION:USER \"/"<>
		If[OptionValue[MicrowaveSwitchEnabled]===True,
			"laserAndMicrowaveOn.seq","laserOn.seq"]<>"\",\"NET1\""];
	GPIBcmd[$ODMRawg,"AWGCONTROL:RMODE CONTINUOUS"];
	GPIBqueryNumber[$ODMRawg,":FREQ"];
	GPIBcmd[$ODMRawg,"AWGCONTROL:RUN"];);
DisableAOM[o:OptionsPattern[{MicrowaveSwitchEnabled->False}]]:=
	(GPIBcmd[$ODMRawg,"AWGCONTROL:STOP"];
	GPIBcmd[$ODMRawg,"SOURCE2:FUNCTION:USER \"/"<>
		If[OptionValue[MicrowaveSwitchEnabled]===True,
			"laserOffAndMicrowaveOn.seq","laserOff.seq"]<>"\",\"NET1\""];
	GPIBcmd[$ODMRawg,"AWGCONTROL:RMODE CONTINUOUS"];
	GPIBqueryNumber[$ODMRawg,":FREQ"];
	GPIBcmd[$ODMRawg,"AWGCONTROL:RUN"];);

SetLaserControlMode[x_String/;StringMatchQ[x,"current"|"power",IgnoreCase->True]]:=
	(SerialCmd[$ODMRlaser,"CONTROL="<>x];);
GetLaserControlMode[]:=SerialCmd[$ODMRlaser,"CONTROL?"];
SetLaserCurrent[r_?NumericQ]:=(SerialCmd[$ODMRlaser,"CURRENT="<>ToString[100r,CForm]];)/;0<=r<=1;
GetLaserCurrent[]:=ToExpression@StringSplit[SerialCmd[$ODMRlaser,"SETCURRENT1?"],"%"][[1]]/100;
SetLaserPower[r_?NumericQ]:=(SerialCmd[laser,"POWER="<>ToString[1000*r,CForm]];)/;0<=r;
GetLaserPower[]:=ToExpression@StringSplit[SerialCmd[$ODMRlaser,"POWER?"],"mW"][[1]]/1000;
GetLaserTemperature[]:=ToExpression@StringSplit[SerialCmd[$ODMRlaser,"LASTEMP?"],"C"][[1]];
GetLaserPSUtemperature[]:=ToExpression@StringSplit[SerialCmd[$ODMRlaser,"PSUTEMP?"],"C"][[1]];

(*{state,xyz,steps,factors,minCountsToTrack,samplesPerAxis,buffer}*)

TrackingContextQ[x_]:=MatchQ[x,
	TrackingContext[{1|2|3,1|2|3},			(*state*)
		{_?NumericQ,_?NumericQ,_?NumericQ},	(*xyz*)
		{{_?NumericQ,_?NumericQ,_?NumericQ},	(*steps*)
		{_?NumericQ,_?NumericQ,_?NumericQ},	(*steps*)
		{_?NumericQ,_?NumericQ,_?NumericQ}},	(*steps*)
		_?NumericQ,				(*minCountsToTrack*)
		{_?NumericQ|{___?NumericQ},_?NumericQ|{___?NumericQ},
			_?NumericQ|{___?NumericQ}}]];	(*buffer*)
Options[CountAndTrack]=
	{TrackerStepSize->0.025,TrackerMinimumStepSize->0.010,TrackerMinCountsToTrack->5*^3,
		CountingTime->Automatic,TrackerMinSamplesPerAxis->10,
		TrackerDiscriminationFactors->{1.02,1.02,1.03},
		TrackerStepFactor->0.1,FixedAxes->None,CountingFunction->CountCounters};
CountAndTrack[numSamples:(_Integer?NonNegative):0,options:OptionsPattern[]]:=
	CountAndTrack[numSamples,TrackingContext[{1,1},ReadStage[],
		OptionValue[TrackerStepSize]IdentityMatrix[3],
		OptionValue[TrackerMinCountsToTrack]*GetCounterCountingTime[],
		{{},{},{}}]
	];
CountAndTrack[numSamples:(_Integer?NonNegative):1,
		trackingContext:TrackingContext[state_,xyz_,steps_,minCountsToTrack_,buffers_]?TrackingContextQ,
		options:OptionsPattern[]]:=
	If[numSamples>0,
		Module[{factor=If[ListQ[#],#[[state[[1]]]],#]&@OptionValue[TrackerDiscriminationFactors],
				c=OptionValue[CountingFunction][numSamples],
				fixedAxes=Switch[#,All,{True,True,True},{_?BooleanQ,_?BooleanQ,_?BooleanQ},#,
					_,{False,False,False}]&@OptionValue[FixedAxes],
				step=steps[[state[[1]]]],
				samplesPerAxis=OptionValue[TrackerMinSamplesPerAxis],
				buffer=buffers[[state[[2]]]]},
			If[!fixedAxes[[state[[1]]]],
				Switch[state[[2]],
					1,MoveStage[xyz];
					buffer=Join[buffer,Total/@c];
					{c,If[Length[buffer]>=samplesPerAxis,
						ReplacePart[#,{{1,2}->2,{5,1}->Mean[buffer]}],
						ReplacePart[#,{5,1}->buffer]]&@trackingContext},
					2,MoveStage[xyz+step];
					buffer=Join[buffer,Total/@c];
					{c,If[Length[buffer]>=samplesPerAxis,
						ReplacePart[#,{{1,2}->3,{5,2}->Mean[buffer]}],
						ReplacePart[#,{5,2}->buffer]]&@trackingContext},
					3,MoveStage[xyz-step];
					buffer=Join[buffer,Total/@c];
					{c,If[Length[buffer]>=samplesPerAxis,
						ReplacePart[#,{{1,1}->1+Mod[#[[1,1]],3],
							2->#[[2]]+Boole[Min[#[[5]]]>=minCountsToTrack]*
								If[#[[5,3]]>factor*#[[5,2]],step,
									If[#[[5,1]]>factor*#[[5,2]],-step,0]],
							5->{{},{},{}}}]&
						@ReplacePart[#,{{1,2}->1,{5,3}->Mean[buffer]}],
						ReplacePart[#,{5,3}->buffer]]&@trackingContext},
					_,],
				{c,ReplacePart[trackingContext,1->{1+Mod[state[[1]],3],1}]}
			]
		]
		,trackingContext];

Options[ODMRautoTrack]=Join[{TrackerStepSize->0.025,TrackerMinimumStepSize->0.010,
			TrackerCountingTime->0.05,TrackerCountingSamples->10,
			TrackerDiscriminationFactors->{1.02,1.02,1.03},TrackerStepFactor->0.1,
			TrackerMinCountsToStop->20*^3,TrackerMinCountsToTrack->5*^3,
			TrackerMinRuns->3,TrackerMaxRuns->100,FindAndTrack->False,MaxFindStep->{1.5,1.5,3},
			TrackerMaxPositionVariation->0.025,TrackerMaxCountsVariation->0.021,
			SettlingTime->0.001,FixedAxes->None,StepMonitorFunction->(Null&)},
			Options[FindNV]];
ODMRautoTrack[{x0_?NumericQ,y0_?NumericQ,z0_?NumericQ},o:OptionsPattern[]]:=
	Module[{dt=OptionValue[TrackerCountingTime],n=OptionValue[TrackerCountingSamples],
			min=OptionValue[TrackerMinRuns],max=OptionValue[TrackerMaxRuns],
			\[Delta]=OptionValue[TrackerMaxCountsVariation],
			\[Eta]=OptionValue[TrackerMaxPositionVariation],
			minCounts=OptionValue[TrackerMinCountsToStop],
			minCountsToTrack=OptionValue[TrackerMinCountsToTrack],
			stepSize=OptionValue[TrackerStepSize],
			maxFindStep=Switch[#,{_,_,_},#,{_,_},{#[[1]],#[[1]],#[[2]]},_,{#,#,2#}]&@
				OptionValue[MaxFindStep],
			st=OptionValue[SettlingTime],stepMonitor=OptionValue[StepMonitorFunction],
			fixedAxes=Boole[!#]&/@Switch[#,
				All,{True,True,True},
				{_?BooleanQ,_?BooleanQ,_?BooleanQ},#,
				_,{False,False,False}]&@OptionValue[FixedAxes],
			df=Mean[OptionValue[TrackerDiscriminationFactors]],
			dt0=GetCounterCountingTime[],data,i=0,x=x0,y=y0,z=z0,c=0,d=0,e=0,quit=False,
			find=OptionValue[FindAndTrack]},
		SetCounterCountingTime[dt];
		MoveStage[{x,y,z}];
		Monitor[
			While[i<max\[And]quit===False,
				If[find,
					If[Norm[(#[[1]]-{x,y,z})/maxFindStep]<=1,{{x,y,z},c}=#,
						Print["find failed: "<>ToString[#[[1]]]<>" too far from "<>
							ToString[{x,y,z}]]]&@
					FindNV[{x,y,z},Sequence@@FilterRules[{o},Options[FindNV]],
						FindCycles->1];
					find=False;
				];
				data=MapAt[#/dt&,#,2]&/@
					ODMRTrackMaximum[$ODMRstage,$ODMRcounter,0,N@{x,y,z},
						fixedAxes*{stepSize,stepSize,stepSize},st,df,n];
				i++;
				If[Min[#[[2]]]>=minCountsToTrack,
					{{x,y,z},c}=Mean/@#;
					d=StandardDeviation[Last/@data];
					e=Module[{m=Mean[#]},Sqrt@Mean[Dot[#-m,#-m]&/@#]]&[First/@data];
					If[MatchQ[stepMonitor,_Function|_Symbol],stepMonitor[{x,y,z},c,d,e]];
					If[i>=min\[And]d/c<\[Delta]\[And]e<\[Eta]\[And]c>=minCounts,Break[]];
				]&@Transpose@data;
		];,{ProgressIndicator[i/max],Button["enough",quit=True],Button["fail",quit=$Failed],
			Button["find",find=True],{x,y,z},N@c,N@d,N@e}]
		SetCounterCountingTime[dt0];
		If[i>=min\[And]d/c<\[Delta]\[And]e<\[Eta]\[And]c>=minCounts\[Or]quit===True,{{x,y,z},c},$Failed]
];

Options[ODMRTrace]=Join[{HistoryLength->1000,LiveHistoryLength->1000,ReturnPlottedHistory->True,
			TrackerStepSize->0.025,TrackerMinimumStepSize->0.010,TrackerMinCountsToTrack->10*^3,
			CountingTime->0.010,CountingSamples->10,TrackerDiscriminationFactors->{1.02,1.02,1.03},
			TrackerStepFactor->0.1,TrackerEnabled->False,FixedAxes->None,ScannedImageData->Null,
			MaxTraceTime->\[Infinity],LaserPowerMeter->Null,LaserControlMode->"power",
			LaserPowerMeterFactor->0.34545454545454546`},Options[PlotConfocalImage]];
ODMRTrace[xyz0:{_?NumericQ,_?NumericQ,_?NumericQ}|Null:Null,options:OptionsPattern[]]:=
	Module[{
			historyLength=OptionValue[HistoryLength],
			liveHistoryLength=OptionValue[LiveHistoryLength],
			dt=OptionValue[CountingTime],
			numSamples=OptionValue[CountingSamples],
			stepSize=OptionValue[TrackerStepSize],
			minimumStepSize=OptionValue[TrackerStepSize],
			minCountsToTrack=OptionValue[TrackerMinCountsToTrack],
			iFactors=OptionValue[TrackerDiscriminationFactors],
			track=(OptionValue[TrackerEnabled]===True),
			fixedAxes=Switch[#,
				All,{True,True,True},
				{_?BooleanQ,_?BooleanQ,_?BooleanQ},#,
				_,{False,False,False}]&@OptionValue[FixedAxes],
			maxTraceTime=If[NumericQ[#]\[Or]#===\[Infinity],#,0]&@OptionValue[MaxTraceTime],
			sFactor=OptionValue[TrackerStepFactor],imageData=OptionValue[ScannedImageData],
			laserPowerMeter=OptionValue[LaserPowerMeter],
			laserPowerMeterFactor=OptionValue[LaserPowerMeterFactor],
			laserControlMode=OptionValue[LaserControlMode]},
		Module[{history={},historyIndices=Range[-liveHistoryLength,-1],laserPowerMeterValue=0,
			x,y,z,dt0=GetCounterCountingTime[],laserPower=GetLaserPower[],
			laserPowerToSet=Switch[laserControlMode,"power"|"POWER",1000*GetLaserPower[],
				_,100*GetLaserCurrent[]],
			setLaserPower=False,c,t,selectedTraces={0},buffers=Array[0&,{3,3}],
			traceStartTime=SessionTime[],state={1,1},
			steps=Transpose[({{stepSize,0,0},{0,stepSize,0},{0,0,stepSize}})],
			factors=iFactors,quit=False,stageRange=GetStageRange[],
			countingFunction=Function[Cases[CountCounters[numSamples],{__?NumericQ}]],
			singleDirectionTrackFunction=Function[{state,xyz,step,factor,buffer,counter},
				Module[{c},Switch[state,
					1,MoveStage[xyz];buffer[[2]]=Total@Mean[c=counter[]];{2,c,xyz,step,factor},
					2,MoveStage[xyz+step];buffer[[3]]=Total@Mean[c=counter[]];{3,c,xyz,step,factor},
					3,MoveStage[xyz-step];buffer[[1]]=Total@Mean[c=counter[]];
						{1,c,xyz+Boole[buffer[[2]]>=minCountsToTrack*dt]*
							If[buffer[[3]]>factor buffer[[2]],step,
								If[buffer[[1]]>factor buffer[[2]],-step,0]],
							step,factor},
					_,]],{HoldAll}],
			images,showImage=True},
		SetCounterCountingTime[dt];
		SetLaserControlMode[laserControlMode];
		images = Function[imageData,
			Module[{image,imageAxes,imageRange,imageZaxis,imageZvalue},Switch[imageData,
				_ConfocalImage,
				{imageZaxis,imageZvalue}=If[Length[#]>0,#[[1]],{3,ReadStage[][[3]]}]&
					@Cases[imageData[[2]],HoldPattern[x:("X"|"Y"|"Z")->y_?NumericQ]:>
						{Switch[x,"X",1,"Y",2,"Z",3],y}];
				imageAxes=Complement[Range[3],{imageZaxis}];
				image=PlotConfocalImage[imageData,Sequence@@FilterRules[{options},
					Options[PlotConfocalImage]]];
				imageRange={0,#[[2]]}+#[[1]]&/@
					Transpose[10^6{"offset","area"}/.imageData[[2]]];,
				_Graphics|{_Graphics,Graphics[_Raster,___]},
				image=Switch[#,_Graphics,{#},{_Graphics,Graphics[_Raster,___]},#]&@imageData;
				imageRange=PlotRange/.AbsoluteOptions[image[[1]],PlotRange];
				imageAxes=Switch[#,"x(\[Mu]m)",1,"y(\[Mu]m)",2,"z(\[Mu]m)",3]&/@
					(FrameLabel/.Options[image[[1]],FrameLabel]);
				imageZaxis=Complement[Range[3],imageAxes][[1]];
				imageZvalue=ReadStage[][[imageZaxis]];
			];{image,imageRange,imageAxes,imageZaxis,imageZvalue}]]/@
			Switch[#,_ConfocalImage|_Graphics,{#},{(_ConfocalImage|_Graphics)..},#,_,{}]&@
				OptionValue[ScannedImageData];
		{x,y,z} = If[xyz0=!=Null,xyz0,
			ReplacePart[#,Rule@@#[[1]]&/@GatherBy[images[[All,4;;5]],First]]&@ReadStage[]];
		Monitor[Monitor[Module[{
				samplingFunction=Function[
					(history=Join[If[Length[history]>historyLength-Length[#],
							Take[history,-(historyLength-Length[#])],history],#/dt];
						(c=#/dt;#)&@Mean[#])&
					@If[track\[And]!fixedAxes[[state[[1]]]],
						Module[{counts},
							{state[[2]],counts,{x,y,z},steps[[state[[1]]]],factors[[state[[1]]]]}=
								singleDirectionTrackFunction[state[[2]],{x,y,z},
								UnitVector[3,state[[1]]]steps[[state[[1]]]],factors[[state[[1]]]],
								buffers[[state[[1]]]],countingFunction];
							If[state[[2]]==1,state[[1]]=Mod[state[[1]],3]+1];
							counts],
						MoveStage[{x,y,z}];
						state={Mod[state[[1]],3]+1,1};
						countingFunction[]
				]]},
			While[!quit\[And]SessionTime[]-traceStartTime<maxTraceTime,
				samplingFunction[];
				If[laserPowerMeter=!=Null,
					laserPowerMeterValue=SerialTMCqueryNumber[powerMeter, "READ"]/
						laserPowerMeterFactor];
				If[setLaserPower,
					Switch[laserControlMode,
						"power"|"POWER",SetLaserPower[laserPowerToSet/1000],
						_,SetLaserCurrent[laserPowerToSet/100]];
					setLaserPower=False;];
				laserPower=GetLaserPower[];				
			]],
			Column[{{{x,y,z},c,
					{Mean[#],StandardDeviation[#]}&
					@If[Length[#]>liveHistoryLength,
						Take[#,-liveHistoryLength],#]&@history,
					ToString[IntegerPart[laserPower*1000]]<>"mW",
					If[laserPowerMeter=!=Null,
						ToString[IntegerPart[laserPowerMeterValue*1*^6]]<>"\[Micro]W",
						Sequence[]]},
				ListPlot[Transpose[{dt Take[historyIndices,-Length[#]],#}]&/@
						Function[selectedTrace,Switch[selectedTrace,
							0,Total[#],-1,#[[2]]-#[[1]],
							_,#[[selectedTrace]]]]/@selectedTraces&
						@Transpose[If[Length[#]>liveHistoryLength,
							Take[#,-liveHistoryLength],#]&@history],
					PlotStyle->{Orange,Green,Blue,Red}[[2+selectedTraces]],
					PlotRange->All,ImageSize->120*96/25.4]}]],
		Panel[Column[{
			Grid[{{Row[{"x",Manipulator[Dynamic@x,{0,stageRange[[1]]},
						ImageSize->Large,Appearance->"Open"]}],
					Row[{"fixX",Checkbox[Dynamic[fixedAxes[[1]]]]}]},
				{Row[{"y",Manipulator[Dynamic@y,{0,stageRange[[2]]},
						ImageSize->Large,Appearance->"Open"]}],
					Row[{"fixY",Checkbox[Dynamic[fixedAxes[[2]]]]}]},
				{Row[{"z",Manipulator[Dynamic@z,{0,stageRange[[3]]},
						ImageSize->Large,Appearance->"Open"]}],
					Row[{"fixZ",Checkbox[Dynamic[fixedAxes[[3]]]]}]}}],
			Row[{Row[{"trace",TogglerBar[Dynamic@selectedTraces,
					Join[#->#&/@Range[$ODMRnumCounters],{0->"sum"},
					If[$ODMRnumCounters===2,{-1->"diff"},{}]]]}],,
				Row[{"track",Checkbox[Dynamic[track]]}],,
				Row@If[image=!=Null,{"showImage",Checkbox[Dynamic[showImage]]},{}],,
				Button["clear",history={}],,
				Button["quit",quit=True]}],
			Row[{Row[{Switch[laserControlMode,"power"|"POWER","laserPower(mW)",
						_,"laserCurrent(%)"],
					EventHandler[
						InputField[Dynamic[laserPowerToSet],Number,ImageSize->50],
						{"ReturnKeyDown":>If[0<=laserPowerToSet<=
							Switch[laserControlMode,"power"|"POWER",1000,
								_,100],setLaserPower=True]}]}],,
				Dynamic@Button["Set",setLaserPower=True,
					Enabled->(0<=laserPowerToSet<=
						Switch[laserControlMode,"power"|"POWER",1000,_,100])]}],
			If[Length[images]>0\[And]showImage,Row[
				Function[{image,imageRange,imageAxes,imageZaxis,imageZvalue},
					Row[{#1,,#2}]&@@MapAt[ClickPane[Dynamic@Show[#,
						Graphics[Function[imagePoint,{Green,
							Line[{{#1,#2[[1]]},{#1,#2[[2]]}}]&[
								imagePoint[[1]],imageRange[[2]]],
							Line[{{#2[[1]],#1},{#2[[2]],#1}}]&[
								imagePoint[[2]],imageRange[[1]]]}][
							{x,y,z}[[imageAxes]]]]],
						({x,y,z}=Insert[#,{x,y,z}[[imageZaxis]],imageZaxis])&]&,
					image,1]]@@#&/@images],Sequence[]]
		}]]
		];
		SetCounterCountingTime[dt0];
		{{{x,y,z},c,Mean[history],StandardDeviation[history]},
			If[OptionValue[ReturnPlottedHistory]===True,
				ListPlot[#,PlotStyle->{Orange,Green,Blue,Red}[[2+selectedTraces]],
					PlotRange->All,ImageSize->120*96/25.4],
				#]&[Transpose[{dt Range[-Length[#],-1],#}]&/@
						Function[selectedTrace,Switch[selectedTrace,
							0,Total[#],-1,#[[2]]-#[[1]],
							_,#[[selectedTrace]]]]/@selectedTraces&
					@Transpose[history]]}
	]];

Options[ODMRcw]=Join[{MicrowaveSwitchInstalled->True,LiveScanSync->False,HistoryLength->500,
		TrackerStepSize->0.025,TrackerMinimumStepSize->0.010,
		CountingTime->0.010,CountingSamples->10,OutputData->False,
		TrackerDiscriminationFactors->{1.02,1.02,1.03},FixedAxes->None,
		TrackerStepFactor->0.1,ScannedImageData->Null,MicrowaveSettlingTime->0.001,
		ScansBetweenAutoTracking->0,TimeBetweenAutoTracking->300,Autorun->False,
		MaxScans->\[Infinity],MaxScanTime->\[Infinity],TrackerEnabled->False,
		TrackingsBetweenScanReversal->5},
	Options[ODMRautoTrack]];
ODMRcw[xyz0:{_?NumericQ,_?NumericQ,_?NumericQ}|Null,
		frequencies:(_?NumericQ|{__?NumericQ}),power:(_?NumericQ|{__?NumericQ}),
		options:OptionsPattern[]]:=
	Module[{historyLength=Max[OptionValue[HistoryLength],
				If[ListQ[#],Length[#],1]&/@{frequencies,power}],
			outputData=(#===True)&@OptionValue[OutputData],
			dt=OptionValue[CountingTime],adt=OptionValue[MicrowaveSettlingTime],
			numSamples=OptionValue[CountingSamples],stepSize=OptionValue[TrackerStepSize],
			minimumStepSize=OptionValue[TrackerStepSize],
			iFactors=OptionValue[TrackerDiscriminationFactors],
			scansBetweenAutoTracking=OptionValue[ScansBetweenAutoTracking],
			timeBetweenAutoTracking=OptionValue[TimeBetweenAutoTracking],
			trackingsBetweenScanReversal=OptionValue[TrackingsBetweenScanReversal],
			fixedAxes=Switch[#,
				All,{True,True,True},
				{_?BooleanQ,_?BooleanQ,_?BooleanQ},#,
				_,{False,False,False}]&@OptionValue[FixedAxes],
			sFactor=OptionValue[TrackerStepFactor],imageData=OptionValue[ScannedImageData],
			track=(OptionValue[TrackerEnabled]===True),scan=(OptionValue[Autorun]===True),
			liveScanSync=(OptionValue[LiveScanSync]===True),
			maxScans=If[NumericQ[#]\[Or]#===\[Infinity],#,0]&@OptionValue[MaxScans],
			maxScanTime=If[NumericQ[#]\[Or]#===\[Infinity],#,0]&@OptionValue[MaxScanTime],
			microwaveSwitchInstalled=(OptionValue[MicrowaveSwitchInstalled]===True)},
		Module[{run=True,quit=False,relative=False,
			showHistory=False,showError=False,x,y,z,c=0,cf=0,scans=0,
			lastScanStartTime=-\[Infinity],accumulatedScanTime=0,
			timeOfLastAutoTrack=-\[Infinity],trackings=0,scanReversed=False,
			microwaveActive,microwaveEnabled,stageRange,lastExport,dt0,data,dataSq,
			paddedFrequencies,paddedPower,history={},historyIndices=Range[-historyLength,-1],
			dataReadSucceeded,malformedDataReads=0,
			apdToShow=0,buffers=Array[0&,{3,3}],state={1,1},factors=iFactors,
			steps=Transpose[({{stepSize,0,0},{0,stepSize,0},{0,0,stepSize}})],
			activateMicrowave,deactivateMicrowave,enableMicrowave,disableMicrowave,
			programMicrowaveScanList,reverseMicrowaveScanList,
			countingFunction=Function[Cases[CountCounters[numSamples],{__?NumericQ}]],
			singleDirectionTrackFunction=Function[{state,xyz,step,factor,buffer,counter},
				Module[{c},Switch[state,
					1,MoveStage[xyz];buffer[[2]]=Total@Mean[c=counter[]];{2,c,xyz,step,factor},
					2,MoveStage[xyz+step];buffer[[3]]=Total@Mean[c=counter[]];{3,c,xyz,step,factor},
					3,MoveStage[xyz-step];buffer[[1]]=Total@Mean[c=counter[]];
						{1,c,xyz+If[buffer[[3]]>factor buffer[[2]],step,
							If[buffer[[1]]>factor buffer[[2]],-step,0]],step,factor},
					_,]],{HoldAll}]},
	programMicrowaveScanList=Function[{freq,powers},
		Module[{action="programming microwave"},Monitor[
			GPIBcmd[$ODMRsmiq,":LIST:FREQ "<>StringJoin@Riffle[ToString[#,CForm]&/@freq,","]];
			GPIBcmd[$ODMRsmiq,":LIST:POWER "<>StringJoin@Riffle[ToString[#,CForm]&/@powers,","]];
		,action]];
	];
	reverseMicrowaveScanList=Function[
		Module[{action="reversing microwave scan list"},Monitor[
			scanReversed=!scanReversed;
			If[microwaveActive,
				GPIBcmd[$ODMRsmiq,":FREQ:MODE FIX"];
				GPIBcmd[$ODMRsmiq,":POWER:MODE FIX"]];
			programMicrowaveScanList@@If[scanReversed,Reverse/@#,#]&@
				{paddedFrequencies,paddedPower};
			If[microwaveActive,
				GPIBcmd[$ODMRsmiq,":LIST:LEARN"];
				GPIBcmd[$ODMRsmiq,":FREQ:MODE LIST"];
				GPIBcmd[$ODMRsmiq,"*WAI"];
				While[GPIBqueryNumber[$ODMRsmiq,":FREQ"]==Null\[And]!quit,action=action<>"."];
				Pause[1]];
		,{Button["quit",quit=True],action}]]];
	activateMicrowave=Function[If[!microwaveActive\[Or](Initialize/.{##})===True,
		Module[{action="switching on microwave"},Monitor[
			GPIBcmd[$ODMRsmiq,":OUTP:STATE 1"];
			GPIBcmd[$ODMRsmiq,":LIST:LEARN"];
			GPIBcmd[$ODMRsmiq,":FREQ:MODE LIST"];
			GPIBcmd[$ODMRsmiq,"*WAI"];
			While[GPIBqueryNumber[$ODMRsmiq,":FREQ"]==Null\[And]!quit,action=action<>"."];
			Pause[1];
			,{Button["quit",quit=True],action}]];
		microwaveActive=True;]];
	deactivateMicrowave=Function[If[microwaveActive\[Or](Initialize/.{##})===True,
		Module[{action="switching off microwave"},Monitor[
			GPIBcmd[$ODMRsmiq,":FREQ:MODE FIX"];
			GPIBcmd[$ODMRsmiq,":POWER:MODE FIX"];
			GPIBcmd[$ODMRsmiq,":OUTP:STATE 0"];
			GPIBcmd[$ODMRsmiq,"*WAI"];
			While[GPIBqueryNumber[$ODMRsmiq,":FREQ"]==Null\[And]!quit,action=action<>"."];
			,{Button["quit",quit=True],action}]];
		microwaveActive=False;]];
	enableMicrowave=Function[If[!microwaveEnabled\[Or](Initialize/.{##})===True,
		EnableAOM[MicrowaveSwitchEnabled->True];
		microwaveEnabled=True;]];
	disableMicrowave=Function[If[microwaveEnabled\[Or](Initialize/.{##})===True,
		EnableAOM[MicrowaveSwitchEnabled->False];
		microwaveEnabled=False;]];
	stageRange=GetStageRange[];
	deactivateMicrowave[Initialize->True];
	{paddedFrequencies,paddedPower}=Switch[{#1,#2},
		{_List,_List},{#1,#2},
		{_List,_},{#1,ConstantArray[#2,Length[#1]]},
		{_,_List},{ConstantArray[#1,Length[#2]],#2},
		_,{{#1},{#2}}]&[frequencies,power];
	GPIBcmd[$ODMRsmiq,":FREQ "<>ToString[Mean[paddedFrequencies],CForm]];
	GPIBcmd[$ODMRsmiq,":POWER "<>ToString[Mean[paddedPower],CForm]];
	GPIBcmd[$ODMRsmiq,":LIST:DELETE:ALL"];
	GPIBcmd[$ODMRsmiq,":LIST:SELECT 'ODMR'"];
	GPIBcmd[$ODMRsmiq,":TRIG1:LIST:SOURCE SINGLE"];
	GPIBcmd[$ODMRsmiq,":LIST:MODE AUTO"];
	GPIBcmd[$ODMRsmiq,":LIST:DWELL "<>ToString@CForm[dt+adt]];
	programMicrowaveScanList[paddedFrequencies,paddedPower];
	dt0=GetCounterCountingTime[];
	SetCounterCountingTime[dt];
	SetTriggerMask[{0,0,0,1,0}];
	SetTriggerInvertMask[{0,0,0,1,0}];
	SetNumberOfTriggeredCountingBins[Length[paddedFrequencies]];
	SetTriggeredCountingBinRepetitions[1];
	SetSplitTriggeredCountingBins[False];
	ResetTriggeredCountingData[];
	data=ConstantArray[0,{Length[paddedFrequencies],$ODMRnumCounters}];
	dataSq=ConstantArray[0,{Length[paddedFrequencies],$ODMRnumCounters,$ODMRnumCounters}];
	{x,y,z}=If[xyz0=!=Null,xyz0,ReadStage[]];
	If[microwaveSwitchInstalled,
		disableMicrowave[Initialize->True];
		activateMicrowave[];
	];
	Monitor[Monitor[Module[{
		samplingFunction=Function[countingFunction,
			(history=Join[If[Length[history]>#,Take[history,-#],history]&[
					historyLength-Length[#]],#/dt];
				(c=Total[#/dt];#)&@Mean[#])&@If[track\[And]!fixedAxes[[state[[1]]]]\[And]!scan,
					Module[{counts},
						{state[[2]],counts,{x,y,z},steps[[state[[1]]]],factors[[state[[1]]]]}=
							singleDirectionTrackFunction[state[[2]],{x,y,z},
								UnitVector[3,state[[1]]]steps[[state[[1]]]],
								factors[[state[[1]]]],buffers[[state[[1]]]],
								countingFunction];
						If[state[[2]]==1,state[[1]]=Mod[state[[1]],3]+1];
						counts],
					MoveStage[{x,y,z}];
					state={Mod[state[[1]],3]+1,1};
					countingFunction[]
		]],\[Delta]},
	While[run\[And]scans<maxScans\[And]accumulatedScanTime<maxScanTime,
		If[quit,Break[]];
		If[scan,
			If[track\[And](0<scansBetweenAutoTracking<\[Infinity]
					\[And]Mod[scans,scansBetweenAutoTracking]==0
					\[Or]SessionTime[]-timeOfLastAutoTrack>=timeBetweenAutoTracking),
				If[microwaveSwitchInstalled,disableMicrowave[],deactivateMicrowave[]];
				If[#=!=$Failed,{{x,y,z},c}=#,
					scan=False;Print["tracker failed"];
					If[OptionValue[Autorun]===True,Print["stopping autorun"];run=False];
					Continue[]]&@ODMRautoTrack[{x,y,z},
						Sequence@@FilterRules[{options},Options[ODMRautoTrack]],
						FixedAxes->fixedAxes];
				timeOfLastAutoTrack=SessionTime[];
				trackings++;
				If[scans>0\[And]0<trackingsBetweenScanReversal<\[Infinity]
						\[And]Mod[trackings-1,trackingsBetweenScanReversal]==0,
					reverseMicrowaveScanList[]];
			];
			lastScanStartTime=SessionTime[];
			If[microwaveSwitchInstalled,enableMicrowave[],activateMicrowave[]];
			EnableTriggeredCounting[];
			GPIBcmd[$ODMRsmiq,":TRIG:LIST"];
			Pause[If[liveScanSync,2*dt,Length[paddedFrequencies]*(dt+adt)]];
			While[(cf=GetTriggeredCountingAddress[])!=0\[And]!quit,Pause[dt];];
			dataReadSucceeded=False;
			While[!quit\[And]!dataReadSucceeded,
				If[ListQ[#]\[And]Dimensions[#]=={Length[paddedFrequencies],$ODMRnumCounters},
					(data+=#;dataSq+=(Outer[Times,#,#]&/@#))&@
						If[scanReversed,Reverse[#],#];
					dataReadSucceeded=True,
					Print["retrying malformed data read result: "<>ToString[#]];
					malformedDataReads++
				]&@(\[Delta]=#)&@
				ReadTriggeredCountingData[
					NumberOfTriggeredCountingBins->Length[paddedFrequencies]]];
			ResetTriggeredCountingData[];
			samplingFunction[\[Delta]&];
			scans++;
			accumulatedScanTime+=SessionTime[]-lastScanStartTime;
			,
			If[microwaveSwitchInstalled,disableMicrowave[],deactivateMicrowave[]];
			DisableTriggeredCounting[];
			samplingFunction[countingFunction];
			Pause[0.005];
		]]
	],
	Column[{{x,y,z,c,Mean[history],If[Length[history]>0,StandardDeviation[history],0],scans,
		paddedFrequencies[[cf+1]],malformedDataReads},
		If[showHistory,
			ListPlot[
				Transpose[{dt Take[historyIndices,-Length[#]],#}]&
				@Switch[apdToShow,0,Total[#],-1,#[[2]]-#[[1]],_,#[[apdToShow]]]&
				@Transpose[history],
				PlotStyle->{Orange,Green,Blue,Red}[[2+apdToShow]],
				PlotRange->All,ImageSize->180*96/25.4,Axes->False,Frame->True]
			,Sequence[]],
		If[liveScanSync,Show[#,Graphics[{Red,Line[{{paddedFrequencies[[cf+1]],#[[2,1]]},
				{paddedFrequencies[[cf+1]],#[[2,2]]}}]}]&
			@(PlotRange/.AbsoluteOptions[#, PlotRange])],#]&
		@If[lastExport=!=#,Export[FileNameJoin[{$RootDirectory,"var","www","html",
			"odmrActivity.svg"}],lastExport=#];#,#]&
		@ListLinePlot[Sort[#,#1[[1]]<#2[[1]]&]&@Transpose[{paddedFrequencies,
				Switch[apdToShow,0,Total[#],-1,#[[2]]-#[[1]],_,#[[apdToShow]]]&
				@Transpose[data]}],
			PlotRange->{All,If[relative,{0,All},All]},ImageSize->180*96/25.4,Axes->False,Frame->True],
		If[showError,ListLinePlot[Transpose[{paddedFrequencies,
			Sqrt[scans #2 - #1^2]&@@Switch[apdToShow,
				0,{Total[#1],Total[#2,2]},
				-1,{{-1,1}.#1,{-1, 1}.({-1, 1}.#2)},
				_,{#1[[apdToShow]],#2[[apdToShow,apdToShow]]}]&[
				Transpose[data],Transpose[dataSq,{3,1,2}]]}],
			PlotRange->{All,If[relative,{0,All},All]},ImageSize->180*96/25.4,Axes->False,Frame->True],Sequence[]]}]],
	Panel[Column[{
		Row[{Row[{"x",InputField[Dynamic@x,Number,FieldSize->{6,1}]}],,
			Row[{"fixX",Checkbox[Dynamic[fixedAxes[[1]]]]}],,
			Row[{"y",InputField[Dynamic@y,Number,FieldSize->{6,1}]}],,
			Row[{"fixY",Checkbox[Dynamic[fixedAxes[[2]]]]}],,
			Row[{"z",InputField[Dynamic@z,Number,FieldSize->{6,1}]}],,
			Row[{"fixZ",Checkbox[Dynamic[fixedAxes[[3]]]]}]}],
		Row[{Row[{"run",Checkbox[Dynamic[run]]}],,
			Row[{"scan",Checkbox[Dynamic[scan]]}],,
			Row[{"track",Checkbox[Dynamic[track]]}],,
			Row[{"relative",Checkbox[Dynamic[relative]]}],,
			Row[{"showHistory",Checkbox[Dynamic[showHistory]]}],,
			Row[{"showError",Checkbox[Dynamic[showError]]}],,
			Row[{"apdToShow",SetterBar[Dynamic[apdToShow],
				Join[#->#&/@Range[$ODMRnumCounters],{0->"sum"},
					If[$ODMRnumCounters===2,{-1->"diff"},{}]]]}],,
			Button["clear",data=Map[0&,data,{-1}];dataSq=Map[0&,dataSq,{-1}];scans=0],,
			Button["quit",quit=True]}],
	}]]];
	If[microwaveSwitchInstalled,disableMicrowave[]];
	deactivateMicrowave[];
	DisableTriggeredCounting[];
	SetCounterCountingTime[dt0];
	{If[outputData,Transpose[{paddedFrequencies,data}],
			ListLinePlot[Sort[#,#1[[1]]<#2[[1]]&]&@Transpose[{paddedFrequencies,#}],
				PlotRange->All]&/@Transpose[data]],
		If[outputData,Transpose[{paddedFrequencies,dataSq}],
			Map[ListLinePlot[Sort[#,#1[[1]]<#2[[1]]&]&@Transpose[{paddedFrequencies,
				scans #[[2]]-#[[1]]}],
			PlotRange->All]&,Transpose[
				{Transpose[#,{2,3,1}]&@Outer[Times,#,#,1]&@Transpose@data,
					dataSq},{3,4,1,2}],{2}]],
		{x,y,z},power,scans}
]]/;((#1==#2\[Or]#1==1\[Or]#2==1)&@@(If[ListQ[#],Length[#],1]&/@{frequencies,power}));
Options[ODMRpulsed]=Join[{MicrowaveSwitchInstalled->True,LiveScanSync->False,OutputData->False,
		HistoryLength->500,TrackerStepSize->0.025,TrackerMinimumStepSize->0.010,
		CountingTime->0.010,MicrowaveSettlingTime->0.001,CountingSamples->10,FixedAxes->None,
		TrackerDiscriminationFactors->{1.02,1.02,1.03},TrackerStepFactor->0.1,
		NormalizeCounts->False,NormalizationTriggerOffset->2.5*^-6,
		SwapNormalizationReference->False,Autorun->False,TrackerEnabled->False,
		ScansBetweenAutoTracking->0,TimeBetweenAutoTracking->300,TrackingsBetweenScanReversal->5,
		MaxScans->\[Infinity],MaxScanTime->\[Infinity],OptimizeLaserOnOff->True,
		PulsedCountingTime->300*^-9,CountRepetitions->Automatic,DetectionDelay:>$ODMRdetectionDelay},
	Options[ODMRautoTrack],Options[ConstructMicrowaveSequence]];
ODMRpulsed[xyz0:{_?NumericQ,_?NumericQ,_?NumericQ}|Null,
		frequencies:(_?NumericQ|{__?NumericQ}),power:(_?NumericQ|{__?NumericQ}),
		rabiFrequency_?NumericQ,options:OptionsPattern[]]:=
	Module[{historyLength=Max[OptionValue[HistoryLength],
				If[OptionValue[NormalizeCounts]===True,2,1]*
				(If[ListQ[#],Length[#],1]&/@{frequencies,power})],
			outputData=(#===True)&@OptionValue[OutputData],
			dt=OptionValue[CountingTime],adt=OptionValue[MicrowaveSettlingTime],
			numSamples=OptionValue[CountingSamples],stepSize=OptionValue[TrackerStepSize],
			minimumStepSize=OptionValue[TrackerStepSize],
			iFactors=OptionValue[TrackerDiscriminationFactors],
			scansBetweenAutoTracking=OptionValue[ScansBetweenAutoTracking],
			timeBetweenAutoTracking=OptionValue[TimeBetweenAutoTracking],
			trackingsBetweenScanReversal=OptionValue[TrackingsBetweenScanReversal],
			fixedAxes=Switch[#,
				All,{True,True,True},
				{_?BooleanQ,_?BooleanQ,_?BooleanQ},#,
				_,{False,False,False}]&@OptionValue[FixedAxes],
			sFactor=OptionValue[TrackerStepFactor],
			laserPulseLength=OptionValue[LaserPulseLength],
			splitTriggeredCountingBins=(#===True)&@OptionValue[NormalizeCounts],
			normalizationTriggerOffset=OptionValue[NormalizationTriggerOffset],
			swapNormalizationReference=(#===True)&@OptionValue[SwapNormalizationReference],
			pulsedCountingTime=OptionValue[PulsedCountingTime],
			preMicrowaveDelay=OptionValue[PreMicrowaveDelay],
			postMicrowaveDelay=OptionValue[PostMicrowaveDelay],
			countRepetitions=OptionValue[CountRepetitions],
			detectionDelay=OptionValue[DetectionDelay],
			clockRate=OptionValue[ClockRate],
			liveScanSync=(OptionValue[LiveScanSync]===True),
			track=(OptionValue[TrackerEnabled]===True),scan=(OptionValue[Autorun]===True),
			maxScans=If[NumericQ[#]\[Or]#===\[Infinity],#,0]&@OptionValue[MaxScans],
			maxScanTime=If[NumericQ[#]\[Or]#===\[Infinity],#,0]&@OptionValue[MaxScanTime],
			microwaveSwitchInstalled=(OptionValue[MicrowaveSwitchInstalled]===True),
			optimizeLaserOnOff=(OptionValue[OptimizeLaserOnOff]===True)},
		Module[{run=True,quit=False,relative=False,showHistory=False,showError=False,
			x,y,z,c=0,cf=0,scans=0,stageRange,a,b,n,lastExport,dt0,data,dataSq,
			lastScanStartTime=-\[Infinity],accumulatedScanTime=0,timeOfLastAutoTrack=-\[Infinity],
			apdToShow=0,normalizationViewMode="normalized",paddedFrequencies,paddedPower,
			history={},historyIndices=Range[-historyLength,-1],
			dataReadSucceeded,malformedDataReads=0,trackings=0,scanReversed=False,
			buffers=Array[0&,{3,3}],state={1,1},steps=Transpose[stepSize IdentityMatrix[3]],
			factors=iFactors,awgConfigured=False,microwaveActive,microwaveEnabled,
			activateMicrowave,deactivateMicrowave,enableMicrowave,disableMicrowave,
			programMicrowaveScanList,reverseMicrowaveScanList,
			countingFunction=Function[Cases[CountCounters[numSamples],{__?NumericQ}]],
			singleDirectionTrackFunction=Function[{state,xyz,step,factor,buffer,counter},
				Module[{c},Switch[state,
					1,MoveStage[xyz];buffer[[2]]=Total@Mean[c=counter[]];{2,c,xyz,step,factor},
					2,MoveStage[xyz+step];buffer[[3]]=Total@Mean[c=counter[]];{3,c,xyz,step,factor},
					3,MoveStage[xyz-step];buffer[[1]]=Total@Mean[c=counter[]];
						{1,c,xyz+If[buffer[[3]]>factor buffer[[2]],step,
							If[buffer[[1]]>factor buffer[[2]],-step,0]],step,factor},
					_,]],{HoldAll}]},
	programMicrowaveScanList=Function[{freq,powers},
		Module[{action="programming microwave"},Monitor[
			GPIBcmd[$ODMRsmiq,":LIST:FREQ "<>StringJoin@Riffle[ToString[#,CForm]&/@freq,","]];
			GPIBcmd[$ODMRsmiq,":LIST:POWER "<>StringJoin@Riffle[ToString[#,CForm]&/@powers,","]];
		,action]];
	];
	reverseMicrowaveScanList=Function[
		Module[{action="reversing microwave scan list"},Monitor[
			scanReversed=!scanReversed;
			If[microwaveActive,
				GPIBcmd[$ODMRsmiq,":FREQ:MODE FIX"];
				GPIBcmd[$ODMRsmiq,":POWER:MODE FIX"]];
			programMicrowaveScanList@@If[scanReversed,Reverse/@#,#]&@
				{paddedFrequencies,paddedPower};
			If[microwaveActive,
				GPIBcmd[$ODMRsmiq,":LIST:LEARN"];
				GPIBcmd[$ODMRsmiq,":FREQ:MODE LIST"];
				GPIBcmd[$ODMRsmiq,"*WAI"];
				While[GPIBqueryNumber[$ODMRsmiq,":FREQ"]==Null\[And]!quit,action=action<>"."];
				Pause[1]];
		,{Button["quit",quit=True],action}]]];
	enableMicrowave=Function[If[!microwaveEnabled\[Or](Initialize/.{##})===True,
		Module[{action="configuring awg for pulsing"},Monitor[
			If[!optimizeLaserOnOff\[Or]!awgConfigured,			
				GPIBcmd[$ODMRawg,"AWGCONTROL:STOP"];
				GPIBcmd[$ODMRawg,"AWGCONTROL:RMODE TRIGGERED"];
				GPIBSetTimeout[$ODMRawg,13];
				GPIBcmd[$ODMRawg,"SOURCE2:FUNCTION:USER \"/pulsedODMR.seq\",\"NET1\""];
				While[GPIBqueryNumber[$ODMRawg,":FREQ"]==Null\[And]!quit,action=action<>"."];
				GPIBSetTimeout[$ODMRawg,$ODMRgpibDefaultTimeout];
				GPIBcmd[$ODMRawg,":FREQ "<>ToString[clockRate,CForm]];
				awgConfigured=True;
			];
			GPIBcmd[$ODMRawg,"AWGCONTROL:RUN"];
			,{Button["quit",quit=True],action}]];
		SetCounterCountingTime[pulsedCountingTime];
		microwaveEnabled=True;
	]];
	disableMicrowave=Function[If[microwaveEnabled\[Or](Initialize/.{##})===True,
		Module[{action="configuring awg for constant light"},Monitor[
			If[!optimizeLaserOnOff\[Or]!awgConfigured,
				EnableAOM[],GPIBcmd[$ODMRawg,"AWGCONTROL:STOP"]];
			,{Button["quit",quit=True],action}]];
		SetCounterCountingTime[dt];
		microwaveEnabled=False;
	]];
	activateMicrowave=Function[If[!microwaveActive\[Or](Initialize/.{##})===True,
		Module[{action="switching on microwave"},Monitor[
			GPIBcmd[$ODMRsmiq,":OUTP:STATE 1"];
			GPIBcmd[$ODMRsmiq,":LIST:LEARN"];
			GPIBcmd[$ODMRsmiq,":FREQ:MODE LIST"];
			GPIBcmd[$ODMRsmiq,"*WAI"];
			While[GPIBqueryNumber[$ODMRsmiq,":FREQ"]==Null\[And]!quit,action=action<>"."];
			Pause[1];
			,{Button["quit",quit=True],action}]];
		microwaveActive=True;
		If[(EnableMicrowave/.{##}/.EnableMicrowave->True)===True,
			enableMicrowave[##]];
	]];
	deactivateMicrowave=Function[If[microwaveActive\[Or](Initialize/.{##})===True,
		Module[{action="switching off microwave"},Monitor[
			GPIBcmd[$ODMRsmiq,":FREQ:MODE FIX"];
			GPIBcmd[$ODMRsmiq,":POWER:MODE FIX"];
			GPIBcmd[$ODMRsmiq,":OUTP:STATE 0"];
			GPIBcmd[$ODMRsmiq,"*WAI"];
			While[GPIBqueryNumber[$ODMRsmiq,":FREQ"]==Null\[And]!quit,action=action<>"."];
			,{Button["quit",quit=True],action}]];
		microwaveActive=False;
		If[(EnableMicrowave/.{##}/.EnableMicrowave->False)===False,
			disableMicrowave[##]];
	]];
	stageRange=GetStageRange[];
	deactivateMicrowave[Initialize->True];
	{paddedFrequencies,paddedPower}=Switch[{#1,#2},
		{_List,_List},{#1,#2},
		{_List,_},{#1,ConstantArray[#2,Length[#1]]},
		{_,_List},{ConstantArray[#1,Length[#2]],#2},
		_,{{#1},{#2}}]&[frequencies,power];
	GPIBcmd[$ODMRsmiq,":FREQ "<>ToString[Mean[paddedFrequencies],CForm]];
	GPIBcmd[$ODMRsmiq,":POWER "<>ToString[Mean[paddedPower],CForm]];
	GPIBcmd[$ODMRsmiq,":LIST:DELETE:ALL"];
	GPIBcmd[$ODMRsmiq,":LIST:SELECT 'ODMR'"];
	GPIBcmd[$ODMRsmiq,":TRIG1:LIST:SOURCE SINGLE"];
	GPIBcmd[$ODMRsmiq,":LIST:MODE AUTO"];
	GPIBcmd[$ODMRsmiq,":LIST:DWELL "<>ToString@CForm[dt+adt]];
	programMicrowaveScanList[paddedFrequencies,paddedPower];
	If[!microwaveSwitchInstalled,
		GPIBcmd[$ODMRsmiq,":PULM:POLARITY NORMAL"];
		GPIBcmd[$ODMRsmiq,":PULM:STATE ON"];
		,
		GPIBcmd[$ODMRsmiq,":PULM:STATE OFF"];
	];
	GPIBcmd[$ODMRawg,"AWGCONTROL:STOP"];
	GPIBcmd[$ODMRawg,"TRIGGER:SOURCE EXTERNAL"];
	GPIBcmd[$ODMRawg,"TRIGGER:LEVEL 1V"];
	GPIBcmd[$ODMRawg,"TRIGGER:SLOPE NEGATIVE"];
	If[countRepetitions===Automatic,
		countRepetitions=
			Floor[dt/(laserPulseLength+preMicrowaveDelay
				+1/2/rabiFrequency+postMicrowaveDelay)];
		Print["using "<>ToString[countRepetitions]<>" counts per frequency bin and cycle"]];
	ConstructMicrowaveSequence[{{(1/2)/rabiFrequency,1&}},"pulsedODMR",
		TriggerOffset->If[splitTriggeredCountingBins,{0,normalizationTriggerOffset},0],
		Repetitions->countRepetitions,ClockRate->clockRate,
		UseMicrowaveSwitch->microwaveSwitchInstalled,
		AppendRepetitionsToSequenceFileName->False,
		Sequence@@(FilterRules[{options},Options[ConstructMicrowaveSequence]])];
	dt0=GetCounterCountingTime[];
	SetCounterCountingTime[dt];
	SetCounterPredelay[detectionDelay];
	SetTriggerMask[{0,0,1,0,0}];
	SetNumberOfTriggeredCountingBins[Length[paddedFrequencies]];
	SetTriggeredCountingBinRepetitions[countRepetitions];
	SetSplitTriggeredCountingBins[splitTriggeredCountingBins];
	ResetTriggeredCountingData[];
	data=ConstantArray[0,If[splitTriggeredCountingBins,Append[#,2],#]&@
		{Length[paddedFrequencies],$ODMRnumCounters}];
	dataSq=ConstantArray[0,If[splitTriggeredCountingBins,Join[#,{2,2}],#]&@
		{Length[paddedFrequencies],$ODMRnumCounters,$ODMRnumCounters}];
	a=GetTriggeredCountingAddress[];
	b=GetTriggeredCountingBinRepetitionCounter[];
	SetNumberOfCounts[0];
	n=GetNumberOfCounts[];
	{x,y,z}=If[xyz0=!=Null,xyz0,ReadStage[]];
	If[microwaveSwitchInstalled,
		disableMicrowave[Initialize->True];
		activateMicrowave[EnableMicrowave->False];
	];
	Monitor[Monitor[Module[{
		samplingFunction=Function[countingFunction,
			(history=Join[If[Length[history]>#,Take[history,-#],history]&[
					historyLength-Length[#]],#/dt];
				(c=#/dt;#)&@Mean[#])&@If[
					track\[And]!fixedAxes[[state[[1]]]]\[And]!scan,
					Module[{counts},
						{state[[2]],counts,{x,y,z},steps[[state[[1]]]],factors[[state[[1]]]]}=
							singleDirectionTrackFunction[state[[2]],{x,y,z},
								UnitVector[3,state[[1]]]steps[[state[[1]]]],
								factors[[state[[1]]]],buffers[[state[[1]]]],
								countingFunction];
						If[state[[2]]==1,state[[1]]=Mod[state[[1]],3]+1];
						counts],
					MoveStage[{x,y,z}];
					state={Mod[state[[1]],3]+1,1};
					countingFunction[]
		]],\[Delta]},
	While[run\[And]scans<maxScans\[And]accumulatedScanTime<maxScanTime,
		If[quit,Break[]];
		If[scan,
			If[track\[And](0<scansBetweenAutoTracking<\[Infinity]
					\[And]Mod[scans,scansBetweenAutoTracking]==0
					\[Or]SessionTime[]-timeOfLastAutoTrack>=timeBetweenAutoTracking),
				If[microwaveSwitchInstalled,disableMicrowave[],deactivateMicrowave[]];
				If[#=!=$Failed,{{x,y,z},c}=#,
					scan=False;Print["tracker failed"];
					If[OptionValue[Autorun]===True,Print["stopping autorun"];run=False];
					Continue[]]&@ODMRautoTrack[{x,y,z},
						Sequence@@FilterRules[{options},Options[ODMRautoTrack]],
					FixedAxes->fixedAxes];
				timeOfLastAutoTrack=SessionTime[];
				trackings++;
				If[scans>0\[And]0<trackingsBetweenScanReversal<\[Infinity]
						\[And]Mod[trackings-1,trackingsBetweenScanReversal]==0,
					reverseMicrowaveScanList[]];
			];
			lastScanStartTime=SessionTime[];
			If[microwaveSwitchInstalled,enableMicrowave[],activateMicrowave[]];
			EnableTriggeredCounting[];
			GPIBcmd[$ODMRsmiq,":TRIG:LIST"];
			Pause[If[liveScanSync,2*dt,Length[paddedFrequencies]*(dt+adt)]];
			While[(cf=GetTriggeredCountingAddress[])!=0\[And]!quit,
				a=GetTriggeredCountingAddress[];
				b=GetTriggeredCountingBinRepetitionCounter[];
				n=GetNumberOfCounts[];
				Pause[dt]];
			dataReadSucceeded=False;
			While[!quit\[And]!dataReadSucceeded,
				If[ListQ[#]\[And]Dimensions[#]=={
						Length[paddedFrequencies]*If[splitTriggeredCountingBins,2,1],
						$ODMRnumCounters},
					If[splitTriggeredCountingBins,
						(data+=#;dataSq+=(Transpose/@Outer[Times,#,#,2]&/@#))&@
						If[scanReversed,Reverse[#],#]&@
						If[swapNormalizationReference,Map[Reverse,#,{2}],#]&@
						Transpose[Partition[#,2]&/@Transpose[#]],
						(data+=#;dataSq+=(Outer[Times,#,#]&/@#))&@
						If[scanReversed,Reverse[#],#]];
					dataReadSucceeded=True,
					Print["retrying malformed data read result: "<>ToString[#]];
					malformedDataReads++
				]&@(\[Delta]=#)&@
				ReadTriggeredCountingData[
					NumberOfTriggeredCountingBins->Length[paddedFrequencies],
					SplitTriggeredCountingBins->splitTriggeredCountingBins]];
			a=GetTriggeredCountingAddress[];
			b=GetTriggeredCountingBinRepetitionCounter[];
			n=GetNumberOfCounts[];
			ResetTriggeredCountingData[];
			samplingFunction[\[Delta]&];
			scans++;
			accumulatedScanTime+=SessionTime[]-lastScanStartTime;
			,
			If[microwaveSwitchInstalled,disableMicrowave[],deactivateMicrowave[]];
			DisableTriggeredCounting[];
			samplingFunction[countingFunction];
			Pause[0.005];
		]]
	],
	Column[{{x,y,z,c,Mean[history],If[Length[history]>0,StandardDeviation[history],0],scans,
		paddedFrequencies[[cf+1]],b,a,n,malformedDataReads},
		If[showHistory,ListPlot[
				Transpose[{dt Take[historyIndices,-Length[#]],#}]&
				@Switch[apdToShow,0,Total[#],-1,#[[2]]-#[[1]],_,#[[apdToShow]]]&
				@Transpose[history],
				PlotStyle->{Orange,Green,Blue,Red}[[2+apdToShow]],
				PlotRange->All,ImageSize->180*96/25.4,Axes->False,Frame->True],Sequence[]],
		If[liveScanSync,Show[#,Graphics[{Red,Line[{{paddedFrequencies[[cf+1]],#[[2,1]]},
				{paddedFrequencies[[cf+1]],#[[2,2]]}}]}]&
			@(PlotRange/.AbsoluteOptions[#, PlotRange])],#]&
		@If[lastExport=!=#,Export[FileNameJoin[{$RootDirectory,"var","www","html",
			"odmrActivity.svg"}],lastExport=#];#,#]&
		@ListLinePlot[Sort[#,#1[[1]]<#2[[1]]&]&@Transpose[{paddedFrequencies,
				If[splitTriggeredCountingBins,
					Switch[normalizationViewMode,
						"normalized",If[#[[2]]!=0,#[[1]]/#[[2]],0]&/@#,
						"unnormalized",#[[1]]&/@#,"reference",#[[2]]&/@#],#]&@	
				Switch[apdToShow,0,Total[#],-1,#[[2]]-#[[1]],_,#[[apdToShow]]]&@
				Transpose[data]}],
			PlotRange->{All,If[relative,{0,All},All]},ImageSize->180*96/25.4,Axes->False,Frame->True],
		If[showError,ListLinePlot[Transpose[{paddedFrequencies,
				If[splitTriggeredCountingBins,
					Module[{f=Switch[normalizationViewMode,
						"normalized",Function[{Ea,Eb,Eaa,Eab,Eba,Ebb},
							If[Eb!=0,Sqrt[Eb^2*Eaa+Ea^2*Ebb-2*Ea*Eb*Eab]/Eb^2,0]],
						"unnormalized",Function[{Ea,Eb,Eaa,Eab,Eba,Ebb},
							scans*Sqrt[Eaa-Ea^2]],
						"reference",Function[{Ea,Eb,Eaa,Eab,Eba,Ebb},
							scans*Sqrt[Ebb-Eb^2]]]},
						f@@Flatten[#]&/@Transpose[If[scans!=0,#/scans,0*#]]],
					Sqrt[scans*#2-#1^2]&@@#]&@
				Switch[apdToShow,
					0,{Total[#1],Total[#2,2]},
					-1,{{-1,1}.#1,{-1, 1}.({-1, 1}.#2)},
					_,{#1[[apdToShow]],#2[[apdToShow,apdToShow]]}]&[
				Transpose[data],Transpose[dataSq,{3,1,2}]]}],
			PlotRange->{All,If[relative,{0,All},All]},ImageSize->180*96/25.4,Axes->False,Frame->True],Sequence[]]}]],
	Panel[Column[{
		Row[{Row[{"x",InputField[Dynamic@x,Number,FieldSize->{6,1}]}],,
			Row[{"fixX",Checkbox[Dynamic[fixedAxes[[1]]]]}],,
			Row[{"y",InputField[Dynamic@y,Number,FieldSize->{6,1}]}],,
			Row[{"fixY",Checkbox[Dynamic[fixedAxes[[2]]]]}],,
			Row[{"z",InputField[Dynamic@z,Number,FieldSize->{6,1}]}],,
			Row[{"fixZ",Checkbox[Dynamic[fixedAxes[[3]]]]}],,
			If[splitTriggeredCountingBins,Sequence@@{
					PopupMenu[Dynamic[normalizationViewMode],
							{"normalized","unnormalized","reference"}],,
					Row[{"outputRawData",Checkbox[Dynamic[outputData]]}]},
				Sequence[]]}],
		Row[{Row[{"run",Checkbox[Dynamic[run]]}],,
			Row[{"scan",Checkbox[Dynamic[scan]]}],,
			Row[{"track",Checkbox[Dynamic[track]]}],,
			Row[{"relative",Checkbox[Dynamic[relative]]}],,
			Row[{"showHistory",Checkbox[Dynamic[showHistory]]}],,
			Row[{"showError",Checkbox[Dynamic[showError]]}],,
			Row[{"apdToShow",SetterBar[Dynamic[apdToShow],
				Join[#->#&/@Range[$ODMRnumCounters],{0->"sum"},
					If[$ODMRnumCounters===2,{-1->"diff"},{}]]]}],,
			Button["clear",data=Map[0&,data,{-1}];dataSq=Map[0&,dataSq,{-1}];scans=0],,
			Button["quit",quit=True]}]
	}]]];
	deactivateMicrowave[];
	If[optimizeLaserOnOff,EnableAOM[]];
	If[!microwaveSwitchInstalled,
		GPIBcmd[$ODMRsmiq,":PULM:STATE OFF"];];
	DisableTriggeredCounting[];
	SetTriggeredCountingBinRepetitions[1];
	SetCounterCountingTime[dt0];
	{If[outputData,Transpose[{paddedFrequencies,data}],
			ListLinePlot[Sort[#,#1[[1]]<#2[[1]]&]&@Transpose[{paddedFrequencies,
					If[splitTriggeredCountingBins,If[#[[2]]!=0,#[[1]]/#[[2]],0]&/@#,#]}],
				PlotRange->All]&/@Transpose[data]],
		If[outputData,Transpose[{paddedFrequencies,dataSq}],
			Map[ListLinePlot[Sort[#,#1[[1]]<#2[[1]]&]&@Transpose[{paddedFrequencies,
				If[splitTriggeredCountingBins,
					Function[{Ea1,Eb1,Ea2,Eb2,Ea1a2,Ea1b2,Ea2b1,Eb1b2},If[Eb1*Eb2!=0,
						(Eb1*Eb2*Ea1a2+Ea1*Ea2*Eb1b2-Ea1*Eb2*Ea2b1-Ea2*Eb1*Ea1b2)/
						(Eb1^2*Eb2^2),0]]@@Flatten[If[scans!=0,#/scans,0*#]]&/@#,
					scans*#[[2]]-#[[1]]]}],
			PlotRange->All]&,If[splitTriggeredCountingBins,
				Transpose[{Outer[List,#,#,1]&@Transpose[data,{3,1,2}], 
					Transpose[dataSq,{5,1,2,3,4}]},{4,1,2,5,6,3}],
				Transpose[{Transpose[#,{2,3,1}]&@Outer[Times,#,#,1]&@Transpose@data,
					dataSq},{3,4,1,2}]],{2}]],
		{x,y,z},power,scans}
]]/;((#1==#2\[Or]#1==1\[Or]#2==1)&@@(If[ListQ[#],Length[#],1]&/@{frequencies,power}));
Options[ODMRrabi]=Join[{MicrowaveSwitchInstalled->True,HistoryLength->500,TrackerStepSize->0.025,
		FixedAxes->None,TrackerMinimumStepSize->0.010,CountingTime->0.010,CountingSamples->10,
		TrackerDiscriminationFactors->{1.02,1.02,1.03},TrackerStepFactor->0.1,
		ScansBetweenAutoTracking->0,TimeBetweenAutoTracking->300,
		Autorun->False,MaxScans->\[Infinity],MaxScanTime->\[Infinity],TrackerEnabled->False,
		PulsedCountingTime->300*^-9,NormalizeCounts->False,SwapNormalizationReference->False,
		OutputData->False,CountRepetitions->1,DetectionDelay:>$ODMRdetectionDelay,
		ClockRate->Automatic,WaitTime->Automatic,OptimizeLaserOnOff->True,
		MicrowaveEnabled->True,IQModulationEnabled->False,PulseModulationEnabled->False,
		AWGprogrammingTimeout->14},
	Options[ODMRautoTrack]];
ODMRrabi[xyz0:{_?NumericQ,_?NumericQ,_?NumericQ}|Null,
		frequency_?NumericQ,power_?NumericQ,
		rabiSeqFile_String?(StringMatchQ[#,"*.seq"|"*.wfm",IgnoreCase->True]&),
		rabiLength_Integer?Positive,maxMicrowavePulseLength:_?NumericQ|{_?NumericQ..},
		options:OptionsPattern[]]:=
	Module[{historyLength=Max[OptionValue[HistoryLength],
				If[OptionValue[NormalizeCounts]===True,2,1]*rabiLength],
			outputData=(OptionValue[OutputData]===True),
			dt=OptionValue[CountingTime],
			numSamples=OptionValue[CountingSamples],
			stepSize=OptionValue[TrackerStepSize],
			minimumStepSize=OptionValue[TrackerStepSize],
			iFactors=OptionValue[TrackerDiscriminationFactors],
			scansBetweenAutoTracking=OptionValue[ScansBetweenAutoTracking],
			timeBetweenAutoTracking=OptionValue[TimeBetweenAutoTracking],
			fixedAxes=Switch[#,
				All,{True,True,True},
				{_?BooleanQ,_?BooleanQ,_?BooleanQ},#,
				_,{False,False,False}]&@OptionValue[FixedAxes],
			sFactor=OptionValue[TrackerStepFactor],
			waitTime=OptionValue[WaitTime],
			splitTriggeredCountingBins=(#===True)&@OptionValue[NormalizeCounts],
			swapNormalizationReference=(#===True)&@OptionValue[SwapNormalizationReference],
			pulsedCountingTime=OptionValue[PulsedCountingTime],
			countRepetitions=OptionValue[CountRepetitions],
			microwaveSwitchInstalled=(OptionValue[MicrowaveSwitchInstalled]===True),
			optimizeLaserOnOff=(OptionValue[OptimizeLaserOnOff]===True),
			detectionDelay=OptionValue[DetectionDelay],clockRate=OptionValue[ClockRate],
			track=(OptionValue[TrackerEnabled]===True),scan=(OptionValue[Autorun]===True),
			maxScans=If[NumericQ[#]\[Or]#===\[Infinity],#,0]&@OptionValue[MaxScans],
			maxScanTime=If[NumericQ[#]\[Or]#===\[Infinity],#,0]&@OptionValue[MaxScanTime],
			iqmod=(OptionValue[IQModulationEnabled]===True),
			pulsemod=(OptionValue[PulseModulationEnabled]===True),
			utilizeMicrowave=(OptionValue[MicrowaveEnabled]=!=False),
			awgProgrammingTimeout=OptionValue[AWGprogrammingTimeout]},
		Module[{run=True,quit=False,relative=False,showHistory=False,showError=False,
				scans=0,lastScanStartTime=-\[Infinity],accumulatedScanTime=0,
				timeOfLastAutoTrack=-\[Infinity],apdToShow=0,dt0,pd0,
				data,dataSq,stageRange,pulseLengths,n,a,lastExport,
				awgConfigured=False,history={},historyIndices=Range[-historyLength,-1],
				x,y,z,c=0,lastAutoTrackTime=-\[Infinity],lastAutoTrackScanCount=0,
				normalizationViewMode="normalized",buffers=Array[0&,{3,3}],state={1,1},
				steps=Transpose[stepSize IdentityMatrix[3]],factors=iFactors,
				dataReadSucceeded,malformedDataReads=0,microwaveActive,microwaveEnabled,
				activateMicrowave,deactivateMicrowave,enableMicrowave,disableMicrowave,
				countingFunction=Function[Cases[CountCounters[numSamples],{__?NumericQ}]],
				singleDirectionTrackFunction=Function[{state,xyz,step,factor,buffer,counter},
					Module[{c},Switch[state,
						1,MoveStage[xyz];buffer[[2]]=Total@Mean[c=counter[]];{2,c,xyz,step,factor},
						2,MoveStage[xyz+step];buffer[[3]]=Total@Mean[c=counter[]];
							{3,c,xyz,step,factor},
						3,MoveStage[xyz-step];buffer[[1]]=Total@Mean[c=counter[]];
							{1,c,xyz+If[buffer[[3]]>factor buffer[[2]],step,
								If[buffer[[1]]>factor buffer[[2]],-step,0]],step,factor},
						_,]],{HoldAll}]},
	If[waitTime==Automatic\[Or]clockRate===Automatic,
		Function[{wt,cr},
			If[waitTime==Automatic,
				waitTime=Ceiling[wt[[1]],0.001]];
			If[clockRate===Automatic,clockRate=cr];
		]@@GetAWGwfmDurationAndClockRate[rabiSeqFile]];
	enableMicrowave=Function[If[!microwaveEnabled\[Or](Initialize/.{##})===True,
		Module[{action="configuring awg for pulsing"},Monitor[
			If[!optimizeLaserOnOff\[Or]!awgConfigured,			
				GPIBcmd[$ODMRawg,"AWGCONTROL:STOP"];
				GPIBcmd[$ODMRawg,"AWGCONTROL:RMODE TRIGGERED"];
				GPIBSetTimeout[$ODMRawg,awgProgrammingTimeout];			
				GPIBcmd[$ODMRawg,"SOURCE2:FUNCTION:USER \"/"<>rabiSeqFile<>"\",\"NET1\""];
				While[GPIBqueryNumber[$ODMRawg,":FREQ"]==Null\[And]!quit,action=action<>"."];
				GPIBSetTimeout[$ODMRawg,$ODMRgpibDefaultTimeout];
				GPIBcmd[$ODMRawg,":FREQ "<>ToString[clockRate,CForm]];
				If[iqmod,
					GPIBcmd[$ODMRawg,"OUTPUT1 ON"];
					GPIBcmd[$ODMRawg,"OUTPUT2 ON"]];
				awgConfigured=True];
			GPIBcmd[$ODMRawg,"AWGCONTROL:RUN"];
			,{Button["quit",quit=True],action}]];
		SetCounterCountingTime[pulsedCountingTime];
		microwaveEnabled=True;
	]];
	disableMicrowave=Function[If[microwaveEnabled\[Or](Initialize/.{##})===True,
		Module[{action="configuring awg for constant light"},Monitor[
			If[!optimizeLaserOnOff\[Or]!awgConfigured,
				If[iqmod,
					GPIBcmd[$ODMRawg,"OUTPUT1 OFF"];
					GPIBcmd[$ODMRawg,"OUTPUT2 OFF"]];
				EnableAOM[],
				GPIBcmd[$ODMRawg,"AWGCONTROL:STOP"]];
			,{Button["quit",quit=True],action}]];
		SetCounterCountingTime[dt];
		microwaveEnabled=False;
	]];
	activateMicrowave=Function[If[(!microwaveActive\[Or](Initialize/.{##})===True)\[And]utilizeMicrowave,
		Module[{action="switching on microwave"},Monitor[
			GPIBcmd[$ODMRsmiq,":OUTP:STATE 1"];
			GPIBcmd[$ODMRsmiq,"*WAI"];
			While[GPIBqueryNumber[$ODMRsmiq,":FREQ"]==Null\[And]!quit,action=action<>"."];
			Pause[1];
			,{Button["quit",quit=True],action}]];
		microwaveActive=True;
		If[(EnableMicrowave/.{##}/.EnableMicrowave->True)===True,
			enableMicrowave[##]];
	]];
	deactivateMicrowave=Function[If[microwaveActive\[Or](Initialize/.{##})===True,
		Module[{action="switching off microwave"},Monitor[
			GPIBcmd[$ODMRsmiq,":OUTP:STATE 0"];
			GPIBcmd[$ODMRsmiq,"*WAI"];
			While[GPIBqueryNumber[$ODMRsmiq,":FREQ"]==Null\[And]!quit,action=action<>"."];
			,{Button["quit",quit=True],action}]];
		microwaveActive=False;
		If[(EnableMicrowave/.{##}/.EnableMicrowave->False)===False,
			disableMicrowave[##]];
	]];
	stageRange=GetStageRange[];
	dt0=GetCounterCountingTime[];
	SetCounterCountingTime[dt];
	pd0=GetCounterPredelay[];
	SetCounterPredelay[detectionDelay];
	SetTriggerMask[{0,0,1,0,0}];
	SetTriggerInvertMask[{0,0,0,0,0}];
	SetNumberOfTriggeredCountingBins[rabiLength];
	SetTriggeredCountingBinRepetitions[countRepetitions];
	SetSplitTriggeredCountingBins[splitTriggeredCountingBins];
	ResetTriggeredCountingData[];
	GPIBcmd[$ODMRsmiq,":FREQ:MODE CW"];
	GPIBcmd[$ODMRsmiq,":POWER:MODE FIX"];
	GPIBcmd[$ODMRsmiq,":OUTP:STATE 0"];
	GPIBcmd[$ODMRsmiq,":FREQ "<>ToString[frequency,CForm]];
	GPIBcmd[$ODMRsmiq,":POWER "<>ToString[power,CForm]];
	If[pulsemod,
		GPIBcmd[$ODMRsmiq,":PULM:POLARITY NORMAL"];
		GPIBcmd[$ODMRsmiq,":PULM:STATE ON"];
		,
		GPIBcmd[$ODMRsmiq,":PULM:STATE OFF"]];
	GPIBcmd[$ODMRawg,"AWGCONTROL:STOP"];
	GPIBcmd[$ODMRawg,"TRIGGER:SOURCE EXTERNAL"];
	If[iqmod,
		GPIBcmd[$ODMRsmiq,":DM:IQ:STATE ON"];
		GPIBcmd[$ODMRawg,"SOURCE1:VOLTAGE 1V"];
		GPIBcmd[$ODMRawg,"SOURCE1:VOLTAGE:OFFSET 0V"];
		GPIBcmd[$ODMRawg,"SOURCE2:VOLTAGE 1V"];
		GPIBcmd[$ODMRawg,"SOURCE2:VOLTAGE:OFFSET 0V"];
		,
		GPIBcmd[$ODMRsmiq,":DM:IQ:STATE OFF"]];
	microwaveActive=True;
	deactivateMicrowave[];
	pulseLengths=If[ListQ[maxMicrowavePulseLength],maxMicrowavePulseLength,
		Range[0,maxMicrowavePulseLength,maxMicrowavePulseLength/(rabiLength-1)]];
	data=ConstantArray[0,If[splitTriggeredCountingBins,Append[#,2],#]&@{rabiLength,$ODMRnumCounters}];
	dataSq=ConstantArray[0,If[splitTriggeredCountingBins,Join[#,{2,2}],#]&@{rabiLength,
		$ODMRnumCounters,$ODMRnumCounters}];
	a=GetTriggeredCountingAddress[];
	SetNumberOfCounts[0];
	n=GetNumberOfCounts[];
	{x,y,z}=If[xyz0=!=Null,xyz0,ReadStage[]];
	If[microwaveSwitchInstalled,
		disableMicrowave[Initialize->True];
		activateMicrowave[EnableMicrowave->False];
	];
	Monitor[Monitor[Module[{
		samplingFunction=Function[countingFunction,
			(history=Join[If[Length[history]>#,Take[history,-#],history]&[
					historyLength-Length[#]],#/dt];
				(c=#/dt;#)&@Mean[#])&
			@If[track\[And]!fixedAxes[[state[[1]]]]\[And]!scan,
				Module[{counts},
					{state[[2]],counts,{x,y,z},steps[[state[[1]]]],factors[[state[[1]]]]}=
						singleDirectionTrackFunction[state[[2]],{x,y,z},
							UnitVector[3,state[[1]]]steps[[state[[1]]]],factors[[state[[1]]]],
							buffers[[state[[1]]]],countingFunction];
					If[state[[2]]==1,state[[1]]=Mod[state[[1]],3]+1];
					counts],
				MoveStage[{x,y,z}];
				state={Mod[state[[1]],3]+1,1};
				countingFunction[]
		]],\[Delta]},
	While[!quit\[And]run\[And]scans<maxScans\[And]accumulatedScanTime<maxScanTime,
		If[scan,
			If[track\[And](0<scansBetweenAutoTracking<\[Infinity]
					\[And]Mod[scans,scansBetweenAutoTracking]==0
					\[Or]SessionTime[]-timeOfLastAutoTrack>=timeBetweenAutoTracking),
				If[microwaveSwitchInstalled,disableMicrowave[],deactivateMicrowave[]];
				If[#=!=$Failed,{{x,y,z},c}=#,
					scan=False;Print["tracker failed"];
					If[OptionValue[Autorun]===True,Print["stopping autorun"];run=False];
					Continue[]]&@ODMRautoTrack[{x,y,z},
						Sequence@@FilterRules[{options},Options[ODMRautoTrack]],
						FixedAxes->fixedAxes];
				timeOfLastAutoTrack=SessionTime[];
			];
			lastScanStartTime=SessionTime[];
			If[microwaveSwitchInstalled,enableMicrowave[],activateMicrowave[]];
			EnableTriggeredCounting[];
			GPIBcmd[$ODMRawg,"TRIG"];
			Pause[waitTime];
			While[(a=GetTriggeredCountingAddress[])!=0\[And]!quit,Pause[0.01]];
			dataReadSucceeded=False;
			While[!quit\[And]!dataReadSucceeded,
				If[ListQ[#]\[And]Dimensions[#]=={rabiLength*If[splitTriggeredCountingBins,2,1],
						$ODMRnumCounters},
					If[splitTriggeredCountingBins,
						(data+=#;dataSq+=(Transpose/@Outer[Times,#,#,2]&/@#))&@
						If[swapNormalizationReference,Map[Reverse,#,{2}],#]&@
						Transpose[Partition[#,2]&/@Transpose[#]],
						data+=#;dataSq+=(Outer[Times,#,#]&/@#)];
					dataReadSucceeded=True,
					Print["retrying malformed data read result: "<>ToString[#]];
					malformedDataReads++
				]&@(\[Delta]=#)&@
				ReadTriggeredCountingData[NumberOfTriggeredCountingBins->rabiLength,
					SplitTriggeredCountingBins->splitTriggeredCountingBins]];
			n=GetNumberOfCounts[];
			ResetTriggeredCountingData[];
			samplingFunction[\[Delta]&];
			scans++;
			accumulatedScanTime+=SessionTime[]-lastScanStartTime;
			,
			If[microwaveSwitchInstalled,disableMicrowave[],deactivateMicrowave[]];
			samplingFunction[countingFunction];
			n=GetNumberOfCounts[];
			Pause[0.005];
		]
	]],
	Column[{{x,y,z,c,Mean[history],If[Length[history]>0,StandardDeviation[history],0],
			scans,a,n,malformedDataReads},
		If[showHistory,ListPlot[
				Transpose[{dt Take[historyIndices,-Length[#]],#}]&
				@Switch[apdToShow,0,Total[#],-1,#[[2]]-#[[1]],_,#[[apdToShow]]]&
				@Transpose[history],
				PlotStyle->{Orange,Green,Blue,Red}[[2+apdToShow]],
				PlotRange->All,ImageSize->180*96/25.4,Axes->False,Frame->True],Sequence[]],
		If[lastExport=!=#,Export[FileNameJoin[{$RootDirectory,"var","www","html",
			"odmrActivity.svg"}],lastExport=#];#,#]&@ListLinePlot[Transpose[{pulseLengths,
				If[splitTriggeredCountingBins,Switch[normalizationViewMode,
						"normalized",If[#[[2]]!=0,#[[1]]/#[[2]],0]&/@#,
						"unnormalized",#[[1]]&/@#,"reference",#[[2]]&/@#],#]&@
				Switch[apdToShow,0,Total[#],-1,#[[2]]-#[[1]],_,#[[apdToShow]]]&
				@Transpose[data]}],
			PlotRange->{All,If[relative,{0,All},All]},ImageSize->180*96/25.4,Axes->False,Frame->True],
		If[showError,ListLinePlot[Transpose[{pulseLengths,
				If[splitTriggeredCountingBins,
					Module[{f=Switch[normalizationViewMode,
						"normalized",Function[{Ea,Eb,Eaa,Eab,Eba,Ebb},
							If[Eb!=0,Sqrt[Eb^2*Eaa+Ea^2*Ebb-2*Ea*Eb*Eab]/Eb^2,0]],
						"unnormalized",Function[{Ea,Eb,Eaa,Eab,Eba,Ebb},
							scans*Sqrt[Eaa-Ea^2]],
						"reference",Function[{Ea,Eb,Eaa,Eab,Eba,Ebb},
							scans*Sqrt[Ebb-Eb^2]]]},
						f@@Flatten[#]&/@Transpose[If[scans!=0,#/scans,0*#]]],
					Sqrt[scans*#2-#1^2]&@@#]&@
				Switch[apdToShow,
					0,{Total[#1],Total[#2,2]},
					-1,{{-1,1}.#1,{-1, 1}.({-1, 1}.#2)},
					_,{#1[[apdToShow]],#2[[apdToShow,apdToShow]]}]&[
				Transpose[data],Transpose[dataSq,{3,1,2}]]}],
			PlotRange->{All,If[relative,{0,All},All]},ImageSize->180*96/25.4,
			Axes->False,Frame->True],Sequence[]]}]],
	Panel[Column[{
		Row[{Row[{"x",InputField[Dynamic@x,Number,FieldSize->{6,1}]}],,
			Row[{"fixX",Checkbox[Dynamic[fixedAxes[[1]]]]}],,
			Row[{"y",InputField[Dynamic@y,Number,FieldSize->{6,1}]}],,
			Row[{"fixY",Checkbox[Dynamic[fixedAxes[[2]]]]}],,
			Row[{"z",InputField[Dynamic@z,Number,FieldSize->{6,1}]}],,
			Row[{"fixZ",Checkbox[Dynamic[fixedAxes[[3]]]]}],,
			If[splitTriggeredCountingBins,Sequence@@{
					PopupMenu[Dynamic[normalizationViewMode],
							{"normalized","unnormalized","reference"}],,
					Row[{"outputRawData",Checkbox[Dynamic[outputData]]}]},
				Sequence[]]}],
		Row[{Row[{"run",Checkbox[Dynamic[run]]}],,
			Row[{"scan",Checkbox[Dynamic[scan]]}],,
			Row[{"track",Checkbox[Dynamic[track]]}],,
			Row[{"relative",Checkbox[Dynamic[relative]]}],,
			Row[{"showHistory",Checkbox[Dynamic[showHistory]]}],,
			Row[{"showError",Checkbox[Dynamic[showError]]}],,
			Row[{"apdToShow",SetterBar[Dynamic[apdToShow],
				Join[#->#&/@Range[$ODMRnumCounters],{0->"sum"},
					If[$ODMRnumCounters===2,{-1->"diff"},{}]]]}],,
			Button["clear",data=Map[0&,data,{-1}];dataSq=Map[0&,dataSq,{-1}];scans=0],,
			Button["quit",quit=True]}]
		}]]
	];
	deactivateMicrowave[];
	If[optimizeLaserOnOff,EnableAOM[]];
	If[iqmod,
		GPIBcmd[$ODMRsmiq,":DM:IQ:STATE OFF"];
		GPIBcmd[$ODMRawg,"OUTPUT1 OFF"];
		GPIBcmd[$ODMRawg,"OUTPUT2 OFF"];
	];
	If[pulsemod,GPIBcmd[$ODMRsmiq,":PULM:STATE OFF"]];
	DisableTriggeredCounting[];
	SetTriggeredCountingBinRepetitions[1];
	SetCounterCountingTime[dt0];
	SetCounterPredelay[pd0];
	{If[outputData,Transpose[{pulseLengths,data}],
		ListLinePlot[Sort[#,#1[[1]]<#2[[1]]&]&@Transpose[{pulseLengths,
				If[splitTriggeredCountingBins,If[#[[2]]!=0,#[[1]]/#[[2]],0]&/@#,#]}],
			PlotRange->All]&/@Transpose[data]],
		If[outputData,Transpose[{pulseLengths,dataSq}],
			Map[ListLinePlot[Sort[#,#1[[1]]<#2[[1]]&]&@Transpose[{pulseLengths,
				If[splitTriggeredCountingBins,
					Function[{Ea1,Eb1,Ea2,Eb2,Ea1a2,Ea1b2,Ea2b1,Eb1b2},If[Eb1*Eb2!=0,
						(Eb1*Eb2*Ea1a2+Ea1*Ea2*Eb1b2-Ea1*Eb2*Ea2b1-Ea2*Eb1*Ea1b2)/
						(Eb1^2*Eb2^2),0]]@@Flatten[If[scans!=0,#/scans,0*#]]&/@#,
					scans*#[[2]]-#[[1]]]}],
			PlotRange->All]&,If[splitTriggeredCountingBins,
				Transpose[{Outer[List,#,#,1]&@Transpose[data,{3,1,2}], 
					Transpose[dataSq,{5,1,2,3,4}]},{4,1,2,5,6,3}],
				Transpose[{Transpose[#,{2,3,1}]&@Outer[Times,#,#,1]&@Transpose@data,
					dataSq},{3,4,1,2}]],{2}]],
		{x,y,z},power,scans}
]];

ClearAll[NVmap,NVmapQ,StartNVmap,AdjustCurrentNVPosition,AutoAdjustCurrentNVPosition,
	GetCurrentMapOffset,ChangeCurrentNV,ChangeCurrentNVbyTag,ExtractCurrentMap,GetCurrentMap,
	GetCurrentNV,GetCurrentNVindex,GetCurrentPositionOfNV,GetCurrentPositionOfNVbyTag,
	AdjustPositionOfNV,AdjustPositionOfNVbyTag,AddNVtoMap,AddNVtoMapAndTrack,RemoveNVfromMap,
	RemoveNVfromMapbyTag,ChangeTagOfNV,ReTagNV,PlotAndAnnotateConfocalImage,ManageNVmap];
StartNVmap[tag_->position:{_?NumericQ,_?NumericQ,_?NumericQ}]:=
	NVmap[{tag->position},1,tag->position];
NVmapQ[m_]:=
	MatchQ[m,NVmap[l:{__Rule},currentIndex_Integer,currentNV_Rule]/;1<=currentIndex<=Length[l]];
AdjustCurrentNVPosition[NVmap[l:{__Rule},currentIndex_Integer?Positive,currentNV_Rule],
		newPosition:{_?NumericQ,_?NumericQ,_?NumericQ}]:=
	NVmap[l,currentIndex,ReplacePart[currentNV,2->newPosition]];
AutoAdjustCurrentNVPosition[m:NVmap[l:{__Rule},currentIndex_Integer?Positive,currentNV_Rule],
		options:OptionsPattern[]]:=
	If[#=!=$Failed,AdjustCurrentNVPosition[m,#[[1]]],Print["auto-adjusting failed!"];m]&@
		ODMRautoTrack[currentNV[[2]],options]/;1<=currentIndex<=Length[l];
GetCurrentMapOffset[NVmap[l:{__Rule},currentIndex_Integer,currentNV_Rule]]:=
	currentNV[[2]]-l[[currentIndex,2]]/;1<=currentIndex<=Length[l];
ChangeCurrentNV[m:NVmap[l:{__Rule},currentIndex_Integer,currentNV_Rule],
		newIndex_Integer?Positive]:=
	NVmap[l,newIndex,MapAt[#+GetCurrentMapOffset[m]&,l[[newIndex]],2]]/;
		And@@(1<=#<=Length[l]&/@{currentIndex,newIndex});
ChangeCurrentNV[m:NVmap[l:{__Rule},currentIndex_Integer,currentNV_Rule],
		newIndex_Integer?Negative]:=
	NVmap[l,Length[l]+1+newIndex,MapAt[#+GetCurrentMapOffset[m]&,l[[newIndex]],2]]/;
		And@@(1<=#<=Length[l]&/@{currentIndex,-newIndex});
GetCurrentNVindex[m:NVmap[l:{__Rule},currentIndex_Integer,currentNV_Rule]]:=
	currentIndex/;1<=currentIndex<=Length[l];
GetCurrentNV[m:NVmap[l:{__Rule},currentIndex_Integer,currentNV_Rule]]:=
	currentNV/;1<=currentIndex<=Length[l];
GetCurrentNVtag[m:NVmap[l:{__Rule},currentIndex_Integer,currentNV:(_->_)]]:=
	currentNV[[1]]/;1<=currentIndex<=Length[l];
GetCurrentNVposition[m:NVmap[l:{__Rule},currentIndex_Integer,currentNV:(_->_)]]:=
	currentNV[[2]]/;1<=currentIndex<=Length[l];
ChangeCurrentNVbyTag[m:NVmap[{__Rule},_Integer,_Rule],newTag_]:=
	ChangeCurrentNV[m,Position[m[[1]],newTag->_][[1,1]]]/;MemberQ[m[[1]],newTag->_];
ExtractCurrentMap[m:NVmap[l:{__Rule},currentIndex_Integer,currentNV_Rule]]:=
	MapAt[#+GetCurrentMapOffset[m]&,l,{All,2}]/;1<=currentIndex<=Length[l];
GetCurrentMap[m:NVmap[l:{__Rule},currentIndex_Integer,currentNV_Rule]]:=
	Module[{off=GetCurrentMapOffset[m]},
		NVmap[MapAt[#+off&,l,{All,2}],currentIndex,currentNV]]/;1<=currentIndex<=Length[l];
GetCurrentPositionOfNV[m:NVmap[l:{__Rule},currentIndex_Integer,currentNV_Rule],
		nvIndex_Integer]:=
	l[[nvIndex,2]]+GetCurrentMapOffset[m]/;And@@(1<=#<=Length[l]&/@{currentIndex,nvIndex});
GetCurrentPositionOfNVbyTag[m:NVmap[{__Rule},_Integer,_Rule],tag_]:=
	GetCurrentPositionOfNV[m,Position[m[[1]],tag->_][[1,1]]]/;MemberQ[m[[1]],tag->_];
AdjustPositionOfNV[m_?NVmapQ,nvIndex_Integer,newPosition:{_,_,_}]:=
	If[nvIndex==m[[2]],ReplacePart[#,{3,2}->newPosition],#]&@
	ReplacePart[m,{1,nvIndex,2}->newPosition-GetCurrentMapOffset[m]]/;1<=nvIndex<=Length[m[[1]]];
AdjustPositionOfNVbyTag[m:NVmap[{__Rule},_Integer,_Rule],tag_,newPosition:{_,_,_}]:=
	AdjustPositionOfNV[m,Position[m[[1]],tag->_][[1,1]],newPosition]/;MemberQ[m[[1]],tag->_];
AddNVtoMap[m:NVmap[l:{__Rule},currentIndex_Integer,currentNV_Rule],
		newNV:(_->{_?NumericQ,_?NumericQ,_?NumericQ})]:=
	NVmap[Append[l,MapAt[#-GetCurrentMapOffset[m]&,newNV,2]],currentIndex,currentNV]/;
		1<=currentIndex<=Length[l];
AddNVtoMapAndTrack[m:NVmap[l:{__Rule},currentIndex_Integer,currentNV_Rule],
		newNV:(_->{_?NumericQ,_?NumericQ,_?NumericQ})]:=
	ChangeCurrentNV[AddNVtoMap[m,newNV],-1]/;1<=currentIndex<=Length[l];
RemoveNVfromMap[m:NVmap[l:{__Rule},currentIndex_Integer,currentNV_Rule],indexToRemove_Integer]:=
	If[currentIndex<indexToRemove,NVmap[Delete[l,indexToRemove],currentIndex,currentNV],
		NVmap[Delete[l,indexToRemove],currentIndex-1,currentNV]]/;
			And@@(1<=#<=Length[l]&/@{currentIndex,indexToRemove})\[And]currentIndex!=indexToRemove;
RemoveNVfromMapbyTag[m:NVmap[{__Rule},_Integer,_Rule],tag_]:=
	RemoveNVfromMap[m,Position[m[[1]],tag->_][[1,1]]]/;MemberQ[m[[1]],tag->_]\[And]m[[3,1]]=!=tag;
ChangeTagOfNV[m:NVmap[l:{__Rule},currentIndex_Integer,_Rule],indexToChange_Integer->newTag_]:=
	If[indexToChange==currentIndex,ReplacePart[#,{3,1}->newTag],#]&@
		ReplacePart[m,{1,indexToChange,1}->newTag]/;1<=currentIndex<=Length[l];
ReTagNV[m_?NVmapQ,oldTag_->newTag_]:=
	ChangeTagOfNV[m,Position[m[[1]],oldTag->_][[1,1]]->newTag]/;MemberQ[m[[1]],oldTag->_];
PlotAndAnnotateConfocalImage[data_ConfocalImage,map_?NVmapQ,options:OptionsPattern[]]:=
	AnnotateConfocalImage[PlotConfocalImage[data,options],map,options,
		Sequence@@(Rule@@#&/@Transpose[{{ZAxis,ZValue},If[Length[#]>0,{
				Switch[#[[1,1]],"X",1,"Y",2,"Z",3],#[[1,2]]},{3,0}]&
			@Cases[data[[2]],HoldPattern[x:(("X"|"Y"|"Z")->_)]:>x]}])];
AnnotateConfocalImage[image0:(_Graphics|{_Graphics,Graphics[_Raster,___]}),map_?NVmapQ,
		options:OptionsPattern[{NVradius->0.5,ZAxis->Automatic,ZValue->0}]]:=
	Module[{radii=Switch[#,{_?NumericQ,_?NumericQ,_?NumericQ},#,_,{#,#,2.7#}]&@
				OptionValue[NVradius],zAxis,zValue=OptionValue[ZValue],imageAxes,imageRange,
			image=If[MatchQ[#,_Graphics],{#},#]&@image0},
		imageRange=PlotRange/.AbsoluteOptions[image[[1]],PlotRange];
		zAxis=If[#===Automatic,First@Complement[Range[3],(Print[#];#)&@
				Switch[#,"x(\[Mu]m)",1,"y(\[Mu]m)",2,"z(\[Mu]m)",3]&/@
				(FrameLabel/.Options[image[[1]],FrameLabel])],#]&@
			Switch[#,1|2|3|Automatic,#,
				_,Print["illegal zAxis, assuming Automatic: "<>ToString[#]];Automatic]&@
			OptionValue[ZAxis];
		imageAxes=Complement[Range[3],{zAxis}];
		If[ListQ[image0],#,#[[1]]]&@MapAt[Show[#,Graphics[
			Function[{tag,pos},If[And@@(#[[2,1]]-#[[3]]<=#[[1]]<=#[[2,2]]+#[[3]]&/@
					Transpose[{pos[[imageAxes]],imageRange,radii[[imageAxes]]}])
					\[And]Abs[pos[[zAxis]]-zValue]<=radii[[zAxis]],
				{Opacity[0],EdgeForm[{Thick,If[(tag->pos)===map[[3]],Green,Red]}],
					Tooltip[Disk[pos[[imageAxes]],radii[[imageAxes]]],tag]},{}]]@@#&/@
			ExtractCurrentMap[map]]]&,image,1]];
AnnotateConfocalImage[images:{(_Graphics|{_Graphics,Graphics[_Raster,___]})..},
		map_?NVmapQ,options:OptionsPattern[]]:=
	AnnotateConfocalImage[#,map,options]&/@images;
PlotAndAnnotateConfocalImage[data:{__ConfocalImage},map_?NVmapQ,options:OptionsPattern[]]:=
	PlotAndAnnotateConfocalImage[#,map,options]&/@data;
Options[ManageNVmap]={NVradius->0.5,ZAxis->Automatic,ZAdjustmentRange->{-20,20},
			ZAxis->Automatic,ZValue->0};
ManageNVmap[map_,data:(_ConfocalImage|{__ConfocalImage}),
		options:OptionsPattern[{ManageNVmap,PlotConfocalImage}]]:=
	ManageNVmap[map,PlotConfocalImage[#,Sequence@@(FilterRules[{options},
		Options[PlotConfocalImage]])]&/@#,Sequence@@FilterRules[{options},Options[ManageNVmap]],
		Sequence@@(Rule@@#&/@Transpose[{{ZAxis,ZValue},Transpose[If[Length[#]>0,{
				Switch[#[[1,1]],"X",1,"Y",2,"Z",3],#[[1,2]]},{3,0}]&
			@Cases[#[[2]],HoldPattern[x:(("X"|"Y"|"Z")->_)]:>x]&/@#]}])]&@
	If[ListQ[data],data,{data}]/;NVmapQ[map]\[Or]Head[map]===Symbol;
ManageNVmap[map_,images0:(_Graphics|{_Graphics,Graphics[_Raster,___]}
		|{(_Graphics|{_Graphics,Graphics[_Raster,___]})..}),
		options:OptionsPattern[]]:=
	Module[{radii=Switch[#,{_?NumericQ,_?NumericQ,_?NumericQ},#,_,{#,#,2.7 #}]&@
				OptionValue[NVradius],zAxes,zValues,zValueAdjust=0,zValue,imageAxes,
			zValueAdjustRange=Switch[#,{_,_},#,_,{-#,#}]&@OptionValue[ZAdjustmentRange],
			sleep=0.05,run=True,i=1,images,namingFunction,GetMousePosition,GetUsedNVnames,
			SearchClosestNV,imageRanges,cmd="idle",nextNVname,nextNVposition,draggedNV=Null,
			currentMap=If[Head[#]===Symbol\[Or]#==={},Null,#]&@map,initialDragPositions,
			singleNVdragging=False,
			indexSeparationFunction=Function[
				If[StringMatchQ[#[[2]],RegularExpression["[0-9]+"]],{#[[1]],ToExpression[#[[2]]]},
					{StringJoin[#],}]&@{StringJoin@Most[#],Last[#]}&@
				StringSplit[StringReplace[#,
					x:RegularExpression["([^0-9][0-9])|([0-9][^0-9])"]:>StringJoin@Insert[
						Characters[x],"\[InvisibleSpace]",2]],"\[InvisibleSpace]"]]},
		images=Switch[#,_Graphics,{{#}},{_Graphics,Graphics[_Raster,___]},{#},
			_List,Switch[#,_Graphics,{#},{_Graphics,Graphics[_Raster,___]},#]&/@#]&@images0;
		imageRanges=(PlotRange/.AbsoluteOptions[#[[1]],PlotRange])&/@images;
		zAxes=MapIndexed[If[#1===Automatic,First@Complement[Range[3],
				Switch[#,"x(\[Mu]m)",1,"y(\[Mu]m)",2,"z(\[Mu]m)",3]&/@
				(FrameLabel/.Options[images[[#2,1]],FrameLabel])],
			#1]&@@{Switch[#,1|2|3|Automatic,#,
				_,Print["illegal zAxis, assuming Automatic: "<>ToString[#]];Automatic],#2[[1]]}&,
			Switch[#,{__}/;Length[#]>=Length[images],Take[#,Length[images]],
				{__}/;Length[If #]<Length[images],PadRight[#,Length[images],Automatic],
				_,ConstantArray[#,Length[images]]]]&@OptionValue[ZAxis];
		zValues=Switch[#,{__}/;Length[#]>=Length[images],Take[#,Length[images]],
				{__}/;Length[If #]<Length[images],PadRight[#,Length[images],#[[-1]]],
				_,ConstantArray[#,Length[images]]]&@OptionValue[ZValue];
		zValue=Function[zValues[[i]]+zValueAdjust];
		imageAxes=Complement[Range[3],{#}]&/@zAxes;
		namingFunction=Function[{name,nameList},If[MemberQ[nameList,name],
			Function[{prefix,index},prefix<>ToString[Max[indexSeparationFunction[#][[2]]&/@
				Select[nameList,StringMatchQ[#,prefix~~RegularExpression["[0-9]*"]]&]/.Null->-1]+1]
			]@@indexSeparationFunction[name],name]];
		GetMousePosition=Function[Insert[MousePosition["Graphics"],zValue[],zAxes[[i]]]];
		GetUsedNVnames=Function[If[NVmapQ[currentMap],First/@currentMap[[1]],{}]];
		nextNVname=namingFunction["NV1",GetUsedNVnames[]];
		SearchClosestNV=Function[{pos,nvList},If[Length[#]>0,#[[1]],Null]&@
			SortBy[#,Norm[#[[2]]-pos]&]&@Select[nvList,
				Norm[#[[imageAxes[[i]]]]/radii[[imageAxes[[i]]]]]<=1\[And]
				Abs[#[[zAxes[[i]]]]]<=radii[[zAxes[[i]]]]&[#[[2]]-pos]&]];
		Monitor[Monitor[
			While[run===True,
				Switch[cmd,
					"idle",Pause[sleep],
					"adjustMap",If[NVmapQ[currentMap],
							currentMap=AdjustCurrentNVPosition[currentMap,
								MapAt[#-zValueAdjust&,
									GetCurrentNVposition[currentMap],
									zAxes[[i]]]];
							zValueAdjust=0;
							currentMap=AutoAdjustCurrentNVPosition[currentMap,
								StepMonitorFunction->((currentMap[[3,2]]=#1)&)]
						];
						cmd="idle";,
					"rescanImage",zValueAdjust=0;
						zValues[[i]]=GetCurrentNVposition[currentMap][[zAxes[[i]]]];
						images[[i]]=PlotConfocalImage[#,Sequence@@(FilterRules[
								{options},Options[PlotConfocalImage]])]&[
							ScanConfocalImage@@
							Append[#,zValues[[i]]]&@Flatten@
							If[#[[1,1]]===1,Reverse[#],#]&@
							Transpose[{imageAxes[[i]],imageRanges[[i]],
								Cases[images[[i,1]],
									x_Raster:>Dimensions[x[[1]]][[1;;2]],
									\[Infinity]][[1]]}]];
						cmd="idle";,
					"handleClick",
						If[#=!=Null,
							currentMap=ChangeCurrentNVbyTag[currentMap,#[[1]]];
							MoveStage[GetCurrentNVposition[currentMap]];,
							If[!MemberQ[GetUsedNVnames[],nextNVname],
								If[#=!=$Failed,
									currentMap=If[NVmapQ[currentMap],
											AddNVtoMap[
												currentMap,#],
											StartNVmap[#]]&[
										nextNVname->#[[1]]];
									nextNVname=namingFunction[nextNVname,
										GetUsedNVnames[]]]&@
								ODMRautoTrack[nextNVposition,
									StepMonitorFunction->
										((nextNVposition=#1)&)];
								If[NVmapQ[currentMap],MoveStage[
									GetCurrentNVposition[currentMap]
								]];
						]]&@SearchClosestNV[nextNVposition,If[NVmapQ[currentMap],
							ExtractCurrentMap[currentMap],{}]];
						cmd="idle";,
					"handleRightClick",If[#=!=Null,Function[iCmd,
						Switch[iCmd,
							"Remove"[_],If[iCmd[[1]]=!=GetCurrentNVtag[currentMap],
								currentMap=RemoveNVfromMapbyTag[currentMap,
									iCmd[[1]]]];,
							"Rename"[_,_],currentMap=ReTagNV[currentMap,
									Rule@@iCmd];
								nextNVname=namingFunction[nextNVname,
									GetUsedNVnames[]];,
							"Reposition"[_],Module[{oldNVposition=
									GetCurrentPositionOfNVbyTag[currentMap,
										iCmd[[1]]]},
								If[#=!=$Failed,
									currentMap=AdjustPositionOfNVbyTag[
										currentMap,
										iCmd[[1]],#[[1]]],
									currentMap=AdjustPositionOfNVbyTag[
										currentMap,
										iCmd[[1]],oldNVposition];
									DialogInput[DialogNotebook[{
										TextCell["Reposition of NV "<>
											ToString[#[[1]]]<>
											"failed!"],
										DefaultButton[DialogReturn[]]}]
									]
								]&@ODMRautoTrack[oldNVposition,
									StepMonitorFunction->
									((currentMap=AdjustPositionOfNVbyTag[
										currentMap,iCmd[[1]],#1])&)]
								If[NVmapQ[currentMap],MoveStage[
									GetCurrentNVposition[currentMap]
								]];
							];,
							$Canceled,]]@
						DialogInput[DialogNotebook[{
							TextCell[ToString[#[[1]]]<>"@"<>ToString[#[[2]]]],
							DefaultButton["Reposition",DialogReturn[
								"Reposition"[#[[1]]]]],
							Button["Rename",DialogReturn[
								"Rename"[#[[1]],nextNVname]]],
							Button["Remove",DialogReturn[
								"Remove"[#[[1]]]],
								Enabled->(#[[1]]=!=GetCurrentNVtag[currentMap])
							],
							CancelButton[]}]]]&@
						SearchClosestNV[nextNVposition,If[NVmapQ[currentMap],
							ExtractCurrentMap[currentMap],{}]];
					cmd="idle";]],
		Append[#,{"X","Y","Z"}[[zAxes[[i]]]]->If[zValueAdjust!=0,
			HoldForm[#3[#1,#2]]&[zValues[[i]],Abs[zValueAdjust],If[zValueAdjust>0,Plus,Subtract]],
			zValues[[i]]]]&@MapAt[EventHandler[Show[#,Graphics[Function[{tag,pos},
				If[And@@(#[[2,1]]-#[[3]]<=#[[1]]<=#[[2,2]]+#[[3]]&/@
					Transpose[{pos[[imageAxes[[i]]]],imageRanges[[i]],
						radii[[imageAxes[[i]]]]}])\[And]
					Abs[pos[[zAxes[[i]]]]-zValue[]]<=radii[[zAxes[[i]]]],
					{Opacity[0],EdgeForm[{Thick,Switch[tag->pos,
						If[NVmapQ[currentMap],GetCurrentNV[currentMap],Null],Green,
							nextNVname->nextNVposition/;cmd==="handleClick",
							Gray,_,Red]}],
						Tooltip[Disk[pos[[imageAxes[[i]]]],
							radii[[imageAxes[[i]]]]],tag]},{}]]@@#&/@
				Join[If[NVmapQ[currentMap],ExtractCurrentMap[currentMap],{}],
					If[cmd==="handleClick",{nextNVname->nextNVposition},{}]]]],
			{"MouseDown":>If[cmd==="idle"\[And]NVmapQ[currentMap],
				nextNVposition=GetMousePosition[];
				draggedNV=If[singleNVdragging\[And]#=!=Null,#[[1]],Null]&@
					SearchClosestNV[nextNVposition,ExtractCurrentMap[currentMap]];
				initialDragPositions={nextNVposition,If[draggedNV=!=Null,
					GetCurrentPositionOfNVbyTag[currentMap,draggedNV],
					GetCurrentNVposition[currentMap]]};],
			"MouseMoved":>If[ListQ[initialDragPositions],
						nextNVposition=GetMousePosition[];
						currentMap=If[draggedNV=!=Null,AdjustPositionOfNVbyTag[currentMap,draggedNV,#],
								AdjustCurrentNVPosition[currentMap,#]]&[
							initialDragPositions[[2]]+nextNVposition-initialDragPositions[[1]]];],
			"MouseUp":>If[ListQ[initialDragPositions],
					nextNVposition=GetMousePosition[];
					If[nextNVposition=!=initialDragPositions[[1]],
						currentMap=If[draggedNV=!=Null,AdjustPositionOfNVbyTag[currentMap,draggedNV,#],
								AdjustCurrentNVPosition[currentMap,#]]&[
							initialDragPositions[[2]]+nextNVposition-initialDragPositions[[1]]]];
					draggedNV=Null;
					initialDragPositions=.;],
			"MouseClicked":>If[cmd==="idle",
				nextNVposition=GetMousePosition[];cmd="handleClick"],
			{"MouseClicked",2}:>If[cmd==="idle",
				nextNVposition=GetMousePosition[];cmd="handleRightClick"]}]&,images[[i]],1]],
		Panel[Row[{Button["done",run=False],,Button["abort",run=$Aborted],,
			Button["readjust",If[cmd==="idle",cmd="adjustMap"]],,
			Button["rescan",If[cmd==="idle",cmd="rescanImage"]],,
			Row[{"singleNVdragging",Checkbox[Dynamic[singleNVdragging]]}],,
			If[Length[images]>1,Sequence[PopupMenu[Dynamic@i,Range@Length[images]],],Sequence[]],
			Row[{"zAdj",Manipulator[Dynamic@zValueAdjust,zValueAdjustRange]}],,
			InputField[Dynamic@nextNVname,String],
			Dynamic@If[MemberQ[GetUsedNVnames[],nextNVname],"name already used!",""]}]]];
	If[run===$Aborted,$Aborted,
		If[MatchQ[Hold[map],Hold[_Symbol]],map=currentMap];
		If[MatchQ[images0,_Graphics|{_Graphics,Graphics[_Raster,___]}],#[[1]],#]&[
			AnnotateConfocalImage[#[[1]],map,ZAxis->#[[2]],ZValue->#[[3]],
				Sequence@@(DeleteCases[{options},(Rule|RuleDelayed)[ZAxis|ZValue,_]])]&/@
			Transpose[{If[MatchQ[#,_Graphics|{_Graphics,Graphics[_Raster,___]}],{#},#]&@images,
				zAxes,zValues}]]]
]/;NVmapQ[map]\[Or]Head[map]===Symbol;
SetAttributes[ManageNVmap,HoldFirst];
Function[f,
	SetAttributes[f,HoldFirst];
	f[map_Symbol,o___]:=
		(map=AutoAdjustCurrentNVPosition@AdjustCurrentNVPosition[map,
			If[f===ODMRTrace,#[[1,1]],#[[3]]]];#)&@
		f[#,o]&@GetCurrentNVposition[map]/;NVmapQ[map];]/@
	{ODMRTrace,ODMRcw,ODMRpulsed,ODMRrabi};

ODMRmultiLineFit[data_Graphics, o___]:=
	Module[{fex=(PlotRange/.AbsoluteOptions[data,PlotRange])[[1]],f},
		Append[#,Show[data,Plot[#[[1]][f],{f,fex[[1]],fex[[2]]},PlotStyle->Black,PlotRange->All]]]]&@
		ODMRmultiLineFit[Cases[data,y:{_RGBColor|_Hue|_GrayLevel,___,(Line|Point)[_List]}
				|{___,Directive[_RGBColor|_Hue|_GrayLevel],(Line|Point)[_List]}:>y[[-1, 1]],
			\[Infinity]][[1]],o];
ODMRmultiLineFit[data:{{_?NumericQ,_?NumericQ}..},fEstimates:{_?NumericQ..},
		wEstimate:(_?Positive|{_?Positive..}):1*^6,cEstimate:(_?NumericQ|{_?NumericQ..}):0.03]:= 
	Module[{base=ToExpression["base"],cEstimates, wEstimates},
		{cEstimates, wEstimates} = If[ListQ[#],#,ConstantArray[#,Length[fEstimates]]]&
			/@{cEstimate,wEstimate}; 
		Block[{base},NonlinearModelFit[data, 
			base*(1-Total[ToExpression["c"<>#]/(1+
				((f-ToExpression["f"<>#])/(ToExpression["w"<>#]/2))^2)&/@
			ToString/@Range[Length[fEstimates]]]),
			Join[{{base,Mean[#[[2]]&/@data]}},Sequence@@MapIndexed[
				Function[{f0,w0,c0,i},{{ToExpression["f"<>i],f0},
					{ToExpression["w"<>i],w0},{ToExpression["c"<>i], c0}}]
				@@Append[#1,ToString@#2[[1]]]&,
				Transpose[{fEstimates,wEstimates,cEstimates}]]],f]]
		//{#,#["ParameterTable"],#["RSquared"],RootMeanSquare@#["FitResiduals"],
			RootMeanSquare@#["FitResiduals"]/#["ParameterTableEntries"][[1,1]]}&
	]/;(Positive[wEstimate]\[Or]ListQ[wEstimate]\[And]Length[wEstimate]==Length[fEstimates])\[And]
		(NumericQ[cEstimate]\[Or]ListQ[cEstimate]\[And]Length[cEstimate]==Length[fEstimates]);

