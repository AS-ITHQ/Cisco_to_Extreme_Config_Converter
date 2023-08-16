import csv
import re
from pathlib import Path
localPath = Path(__file__)

fileName = "HIP-LOLASMIDDLE-2023-05-03T08_00_18.000Z-template_long"
csvFileName = "lolasmid-interfaces"

portRemoveList = []

#outputFileName = fileName + "-" + outputMode + ".txt"
csvRead = open(localPath.with_name(csvFileName + '.csv'), 'r', newline='')


fRead = csv.reader(csvRead, delimiter=',', quotechar='|')
for row in fRead:
    if (row[3] != '"up"'):
        portInfo = re.search(r"Gi(\d)\/(\d)\/(\d{1,2})", row[1])
        if ((portInfo != None) and (portInfo.group(2) == '0')):
            portRemoveList.append(portInfo.group(1) + ":" + portInfo.group(3))


txtFileRead = open(localPath.with_name(fileName + '.txt'))
lines = txtFileRead.readlines()
x = 0
txtFileRead.close()
loopLength = len(lines)
while x < loopLength:
    port = re.search(r"\d:\d\d?",lines[x])
    if (port != None) and (port.group() in portRemoveList):
        line = lines[x]
        tempLine = line.replace(port.group(), "")
        if (tempLine != line):
            curLine = lines[x]
            lines.pop(x)
            while ((not re.match(r"\d:\d\d?",lines[x]) and (x < loopLength-1))):
                lines.pop(x)
            loopLength = len(lines)
    else:
        x = x+1

txtFileRead = open(localPath.with_name(fileName + '.txt'), 'w')
for line in lines:
    txtFileRead.write(line)
txtFileRead.close()