# -*- coding: UTF-8 -*-
# Restartprogramm und konvektive Wärmeübergangsrandbedingung für das Wasserstrahlmodell

from abaqus import *
from abaqusConstants import *
from caeModules import *
from odbAccess import *
import os
import sys
import numpy as np
from math import sqrt

# 最大运行次数,maximale Anzahl an Läufen
MaxNum = 3
# 读取flodel, step, job名称方法
lastModelName = 'Model-Restart-Initial'
lastStepName = 'Step-1'
lastJobName = 'Restart-Initial'
# 先计算双打时间计算步长
stepinterval = 0.1

instancename = 'WORKPIECE'
nodesetname = 'SET-4'
surfacename = 'Surf-Workpiece'
instancename3 = 'Workpiece'
elementrange = 1.5

# 对流特性参数/对流传热设置
# v1=1330.4333216mm/s,0.5MPa,9.9838e-09t/mm2,
v=0.8*sqrt(2*0.1/0.000000009705)
rj=6.1358
rjx=6.1358
x1=1.5
xx=1.5
#Re(x)=19039.4740437
rex=(0.000000009705*v*xx)/0.0000008902
# lambda为热导率(W/mmK)
lambda0=0.000387979838948
#NU(x)根据公式计算得出387.979838948
NU=(x)**(0.33)*Re(x)**(0.9)
# 根据努塞尔数计算热传导h
h=(lambda0*NU)/(mm2K)
# 热流边界温度为298K
sinktemp=298



# 原始模型名称 ursprungliche ModelIname.Model-Restart-Initial,import Model

# 创建并提交作业Restart-Initial,Job erstellen und absenden.Restart-Initial
mdb.job(name='Restart-Initial', model='Model-Restart-Initial', description='',
    type=ANALYSIS, atTime=None, waitMinutes=0, waitHours=0, queue=None,
    memory=90, memoryUnits=PERCENTAGE, explicitPrecision=DOUBLE,
    nodalOutputPrecision=SINGLE, echoPrint=OFF, modelPrint=OFF,
    contactPrint=OFF, historyPrint=OFF, userSubroutine='', scratch='',
    resultsFormat=ODB, parallelizationMethodExplicit=DOMAIN, numDomains=8,
    activateLoadBalancing=False, multiprocessingMode=DEFAULT, numCpus=8)
mdb.jobs['Restart-Initial'].submit(consistencyChecking=OFF)
print('Wait for Restart-Initial')
mdb.jobs['Restart-Initial'].waitForCompletion() # 等待完成,auf Fertigstellung warten



for i in range(MaxNum):
    mdb.Model(name='Model-Restart-ts{}'.format(i+1), objectToCopy=mdb.models[lastNodeName])
    a = mdb.models['Model-Restart-ts{}'.format(i+1)].rootAssembly
    mdb.models['Model-Restart-ts{}'.format(i+1)].setValues(restartJob=LastJobName, restartStep=lastStepName)
    mdb.models['Model-Restart-ts{}'.format(i+1)].ImplicitDynamicsStep(name='Step-{}'.format(i+2), previous=lastStepName,
        timePeriod=startTime, improvedDtm=ON)
    mdb.Job(name='Restart-ts{}'.format(i+1), model='Model-Restart-ts{}'.format(i+1), description='',
        type=ANALYSIS, atTime=None, waitMinutes=0, waitHours=0, queue=None,
        memory=90, memoryUnits=PERCENTAGE, explicitPrecision=DOUBLE,
        nodalOutputPrecision=SINGLE, echoPrint=OFF, modelPrint=OFF,
        contactPrint=OFF, historyPrint=OFF, userSubroutine='', scratch='',
        resultsFormat=ODB, parallelizationMethodExplicit=DOMAIN, numDomains=4,
        activateLoadBalancing=False, multiprocessingMode=DEFAULT, numCpus=4)
    
    mdb.jobs['Restart-ts{}'.format(i+1)].submit(consistencyChecking=OFF)
    print('Wait for Restart-ts{}'.format(i+1))
    mdb.jobs['Restart-ts{}'.format(i+1)].waitForCompletion() # 等待完成,auf Fertigstellung warten
    
    job_name = 'Restart-ts{}'.format(i+1)
    odb = openOdb(path=job_name+'.odb', readOnly=False)

try:
    
    lastFrame = odb.steps['Step-{}'.format(i+2)].frames[-1]# 获取指定分析步的最后一帧数据
    # 使用字符串格式化动态生成步骤名称，frames[-1]表示该步骤的最后一帧
    cpress_output_Data = lastFrame.fieldOutputs['CPRESS']# 从最后一帧中提取接触压力(CPRESS)场输出数据
    # CPRESS是Abaqus中的接触压力变量，表示接触面上的压力分布
    topCenter_2 = odb.rootAssembly.nodesets[nodesetname]# 获取预定义的节点集，用于指定要提取数据的区域
    # nodesetname是之前定义的节点集名称，包含我们感兴趣的区域节点
    
    # 可选：从特定实例的节点集获取数据（当前被注释）
    # topCenter_21 = odb.rootAssembly.instances[instancename1].nodesets[nodesetname1]
    
    # 从接触压力数据中提取指定节点集区域的子集
    # 只获取topCenter_2节点集中节点的接触压力值
    centerDisplacement = cpress_output_Data.getSubset(region=topCenter_2)
    
    # 可选：从其他节点集提取数据（当前被注释）
    # centerDisplacement = cpress_output_Data.getSubset(region=topCenter_21)
    
    # 计算选定区域中的节点数量
    # len()函数返回centerDisplacement.values列表的长度，即节点个数
    num = len(centerDisplacement.values)
    
    # 初始化两个列表来存储筛选后的数据：
    # multilist1: 存储节点标签(编号)
    # multilist2: 存储对应的接触压力值
    # 创建长度为num的列表，初始值都为0
    multilist1 = [0] * num
    multilist2 = [0] * num
    
    # 可选：为其他节点集初始化列表（当前被注释）
    # multilist11 = [0] * num1
    # multilist21 = [0] * num1
    
    # 初始化计数器j，用于记录满足条件的节点数量
    j = 0
    
    # 遍历所有节点，筛选接触压力值在指定范围内的节点
    for k in range(0, num):
        # 获取当前节点的接触压力值
        a = centerDisplacement.values[k].data
        
        # 检查接触压力是否在0到70的范围内（不包括0）
        if (a > 0) and (a <= 70):
            # 如果满足条件，存储节点标签和对应的接触压力值
            multilist1[j] = centerDisplacement.values[k].nodeLabel
            multilist2[j] = centerDisplacement.values[k].data
            # 计数器加1，移动到下一个存储位置
            j = j + 1
        else:
            # 如果不满足条件，保持计数器不变
            # 这个else分支可以省略，这里为了逻辑清晰而保留
            j = j


nozeronum = len(np.nonzero(multilist1)[0])# 计算数组中数值在0到70范围内的节点数量
# 使用np.nonzero找到multilist1中非零元素的索引，并计算数量

# 可选：计算其他数组的非零元素数量（当前被注释）
# nozeronum1 = len(np.nonzero(multilist11)[0])

# 创建文件用于保存0到70范围内的节点编号
# 打开文件'workpiece_nodes_list.txt'，以写入模式('w')
cpFile = open('workpiece_nodes_list.txt', 'w')

# 遍历所有满足条件的节点，将节点编号写入文件
for k in range(0, nozeronum):
    # 将节点编号写入文件，格式化为整数
    cpFile.write("%d\n" % (multilist1[k]))
else:
# 关闭文件，确保数据保存
    cpFile.close()
odb.close()

#============节点坐标解析场办法=================

# 导入节点txt文件，首先对被切体进行操作
# Knoten-TXT-Datei importieren

     result = []  # 初始化空列表用于存储读取的数据

# 打开节点文件并读取内容
     with open('workpiece_nodes_list.txt', 'r') as f:
      for line in f:
        # 将每行文本转换为浮点数列表并添加到result中
        result.append(list(map(float, line.split('.'))))

# 计算读取到的节点数量
     numnodecollst = len(result)

# 创建节点编号数组，初始化为0
     numnodeL1 = [0] * numnodecollst

# numnodeL1为节点编号数组
# 遍历所有读取的数据，提取整数节点编号
    for k in range(0, numnodecollst):
        a-=result[k][0]
        a=int(a)
        numnodeL1[k] = a
    num0=len(numnodeL1)
    os.remove('workpiece_nodes_list.txt')# 删除临时文件

    # 定义存储节点坐标的数组，访问numnodeL1设置节点的数量
# Definieren ein Array von Speicherknotenkoordinaten

# 创建4列n行的二维数组来存储节点坐标（x,y,z,标记值）
multilist = [[0 for col in range(4)] for row in range(numnodecollst)]

# 获取所有对应节点编号的节点对象
# Finden alle Knoten, die allen Knotennummern entsprechen
a = mdb.models['Model-Restart-ts{}'.format(i+1)].rootAssembly
n1 = a.instances[instancesname].nodes
node1 = n1.getSequenceFromMask(mask=numnodeL1)

# 将节点的x,y,z坐标赋值给multilist数组，最后一列设置为1作为标记
# Weisen der Array-Multiliste die X-, Y- und Z-Koordinaten der obigen Knoten zu
for x in range(0, numnodecollst):
    multilist[x][0] = node1[x].coordinates[0]  # X坐标
    multilist[x][1] = node1[x].coordinates[1]  # Y坐标  
    multilist[x][2] = node1[x].coordinates[2]  # Z坐标
    multilist[x][3] = 1  # 标记值

# 创建映射场AnalyticalField-1，使用multilist数组数据
# Erstellen AnalyticalField-1 mit multilist Array-Daten
mdb.models['Model-Restart-ts{}'.format(i+1)].AnalyticalField(name='AnalyticalField-1',
    description='', localCsys=None, fieldType=SCALAR, pointData=multilist)

# 应用分析场数据和对流换热系数到节点的对流边界条件
# Wenden die analytischen Felddaten und konvektiven Wärmeübergangskoeffizienten an den Knoten auf die konvektiven Randbedingungen an.
a = mdb.models['Model-Restart-ts{}'.format(i+1)].rootAssembly
region = a.surfaces[surfacename]
mdb.models['Model-Restart-ts{}'.format(i+1)].FilmCondition(name='Int-workpiece',
    createStepName='Step-{}'.format(i+2), surface=region, definition=FIELD,
    field='AnalyticalField-1', filmCoeff=filmCoeffValue, filmCoeffAmplitude='',
    sinkTemperature=sinkTempValue, sinkAmplitude='', sinkDistributionType=UNIFORM,
    sinkFieldName='')








    except:
       pass

# 更新重启分析所需的模型、步骤和作业名称变量
lastModelName = 'Model-Restart-{}'.format(i+1)  # 上一次的模型名称
lastStepName = 'Step-{}'.format(i+2)            # 上一次的分析步名称  
lastJobName = 'Restart-{}'.format(i+1)          # 上一次的作业名称