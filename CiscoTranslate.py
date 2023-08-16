import re
from pathlib import Path
localPath = Path(__file__)

# Options are 'config' or 'template'
# Config creates an Extreme Config file
# Template creates a list of port and the vlans associated with them, collapsed to make duplicates one entry
# Template_Long creates a list of ports and vlans separated out

outputMode = "template_long"
showDisabled = False

fileName = "EDGE-4B-1"
outputFileName = fileName + "-" + outputMode + ".txt"

class PortInfoClass:
    def __init__(self, stackID=-1, portNumber=-1, tagged=None, untagged=None, portDescription='', portEnabled=False):
        self.stackID = stackID
        self.portNumber = portNumber
        self.tagged = tagged if tagged is not None else []
        self.untagged = untagged if untagged is not None else []
        self.portDescription = portDescription
        self.portEnabled = portEnabled
        self.isTrunk = False
        self.subslot = None

class VlanInfoClass:
    def __init__(self, vlanName='', tagged=None, untagged=None):
        self.vlanName = vlanName
        self.tagged = tagged if tagged is not None else []
        self.untagged = untagged if untagged is not None else []

vlanDict = {}
portDict = {}

f = open(localPath.with_name(fileName + '.txt'))
lines = f.readlines()
x = 0
fullChunk = ""

def splitVlans(vlans):
    # Breaks out all the vlans into their own array to run through with ports in a second
    vlanArray = []
    vlanArray = vlans.split(',')
    i = 0
    for item in vlanArray:
        if item.__contains__('-'):
            item.split('-')
            print(item)
        else:
            vlanArray[i] = int(item)
        i += 1
    return vlanArray

def associateVlans(portInfo, portSetting):
    vlanArray = splitVlans(portInfo[portSetting])
    portID = portInfo.stackID + ":" + portInfo.portNumber
    if portID == '3:23':
        print()
    # Creates the association between the vlan array and the ports
    for vlan in vlanArray:
        vlan = int(vlan)
        portList = []
        vlanInfo = VlanInfoClass()
        if (vlan in vlanDict.keys()):
            portList = vlanDict[vlan][portSetting]
        vlanInfo[portSetting].append(portID)
        vlanInfo[portSetting] = list(set(vlanInfo[portSetting]))
        vlanDict.update({vlan : vlanInfo})

def listString(inputList):
    outputString = ""
    for item in inputList:
        outputString += str(item)
        outputString += ', '
    
    return outputString[:-2]

while x < len(lines):
    while (lines[x] != '!\n') and (x < len(lines)-1):
        fullChunk += lines[x]
        x+=1
    x+=1

    # Searches for the vlan names in the file
    vlanSearch = re.search(r"interface vlan (\d+)\n ?name (.+)\n", fullChunk)
    if (vlanSearch != None):
        vlanID = int(vlanSearch.group(1))
        vlanName = vlanSearch.group(2)
        if (vlanName == ''):
            vlanName = "vlan_" + str(vlanID)
        if (vlanID in vlanDict):
            vlanDict[vlanID].vlanName = vlanName
        else:
            vlanInfo = VlanInfoClass()
            vlanInfo.vlanName = vlanName
            vlanDict.update({vlanID:vlanInfo})

    interface = re.search(r"interface [a-zA-Z]+(\d+)\/(\d+)\/(\d+)\n", fullChunk)    
    if (interface != None):
        portInfo = PortInfoClass()
        portInfo.tagged = []
        portInfo.untagged = []
        
        # Fetches a list of vlans that the port has been assigned
        #vlans = re.findall(r"(?:vlan (?:add )?([^\na-z]*)[^!]*?)", fullChunk)

        # Get the type of vlan assigned to the port
        portTypes = re.findall(r"switchport ([a-zA-Z]+)(?: allowed)? vlan (.+)\n", fullChunk)
        if (portTypes != None):
            for portType in portTypes:
                portList = splitVlans(portType[1])
                match (portType[0]):
                    case 'trunk':
                        portInfo.tagged += portList
                        portInfo.tagged = list(set(portInfo.tagged))
                    case 'access':
                        portInfo.untagged+=portList
                        portInfo.untagged = list(set(portInfo.untagged))
                    case 'voice':
                        portInfo.tagged+=portList
                        portInfo.tagged = list(set(portInfo.tagged))
                    case _:
                        print("ERROR: UNRECOGNISED TYPE")

        # Check if the port is a trunk port
        trunkCheck = re.search(r"switchport mode trunk\n", fullChunk)
        if (trunkCheck != None):
            portInfo.isTrunk = True

        # Add the description of the port to the config
        portDesc = re.search(r"description (.+)\n", fullChunk)
        if (portDesc != None):
            portInfo.portDescription = portDesc.group(1)

        # Disable the port if the RegEx finds "shutdown" as its own line
        portDisabled = re.search(r" shutdown\n", fullChunk)
        if (portDisabled == None):
            portInfo.portEnabled = True

        portID = interface.group(1) + ":" + interface.group(3)
        portInfo.subslot = interface.group(2)
        portInfo.stackID = interface.group(1)
        portInfo.portNumber = interface.group(2)
        if (portInfo.subslot == '0'):
            portDict.update({portID:portInfo})
    fullChunk = ""
f.close()

for port in portDict.items():
    portInfo = port[1]
    #vlanInfoType.tagged = []
    taggedVlans = []
    #vlanInfoType.untagged = []
    untaggedVlans = []

    taggedVlans = portInfo.tagged
    for vlan in taggedVlans:
        vlanInfo = VlanInfoClass()
        if (vlan in vlanDict.keys()):
            vlanInfo = vlanDict[vlan]
        vlanInfo.tagged.append(port[0])
        vlanInfo.tagged = list(set(vlanInfo.tagged))
        vlanDict[vlan] = vlanInfo
        
    untaggedVlans = portInfo.untagged
    for vlan in untaggedVlans:
        vlanInfo = VlanInfoClass()
        if (vlan in vlanDict.keys()):
            vlanInfo = vlanDict[vlan]
        vlanInfo.untagged.append(port[0])
        vlanInfo.untagged = list(set(vlanInfo.untagged))
        vlanDict[vlan] = vlanInfo

vlanPortDict = {}

for vlan in vlanDict.items():
    #print(" VLAN:", key)
    #print("PORTS:", value)
    taggedPortString = ""
    untaggedPortString = ""
    #print(taggedPortString, untaggedPortString)
    for port in vlan[1].tagged:
        portInfo = portDict[port]
        taggedPortString += (port + ",")
    for port in vlan[1].untagged:
        portInfo = portDict[port]
        untaggedPortString += (port + ",")
                
    taggedPortString = taggedPortString[:-1]
    untaggedPortString = untaggedPortString[:-1]
    #print(taggedPortString)
    #print(untaggedPortString)
    #print()
    vlanPortDict.update({vlan[0] : [taggedPortString, untaggedPortString]})
    if (vlan[1].vlanName == ''):
        vlan[1].vlanName = "vlan_" + str(vlan[0])
        vlanDict.update({vlan[0] : vlan[1]})
    #print()

f = open(localPath.with_name(outputFileName), "w")

#Output Mode: Config
match (outputMode.lower()):
    case 'config': 
        #Output port description config
        for key in portDict:
            if (portDict[key].portDescription != ""):
                f.write("configure ports " + key + " description-string \"" + portDict[key].portDescription + "\"\n")
        f.write("\n\n")

        #Output port shutdown config
        for key in portDict:
            if (portDict[key].portEnabled == False):
                f.write("disable port " + key + "\n")
        f.write("\n\n")

        #Output vlan creation config
        for vlan in vlanDict:
            f.write("create vlan \"" + vlanDict[vlan].vlanName + "\" tag " + str(vlan) + "\n")
        f.write("\n\n")

        #Output vlan port config
        for key, value in vlanPortDict.items():
            if (len(value[0]) > 0):
                f.write("configure vlan " + vlanDict[key].vlanName + " add ports " + value[0] + " tagged\n")
            if (len(value[1]) > 0):
                f.write("configure vlan " + vlanDict[key].vlanName + " add ports " + value[1] + " untagged\n")
            if (len(value[0]) + len(value[1]) > 0):
                f.write("\n")
    case 'template':
        concatDict = {}
        for key in portDict:
            port = portDict[key]
            if (port.portEnabled or showDisabled):
                portDesc = port.portDescription
                tagged = listString(port.tagged)
                untagged = listString(port.untagged)
                isTrunk = port.isTrunk
                
                # Create a list of all the ports with the same config
                concatStr = 't' + tagged + 'u' + untagged + str(isTrunk)
                tempList = []
                if (concatStr in concatDict):
                    tempList = concatDict[concatStr]
                tempList.append(key)
                concatDict.update({concatStr:tempList}) 

        for item in concatDict:
            key = concatDict[item][0]
            port = portDict[key]
            portDesc = port.portDescription
            tagged = listString(port.tagged)
            untagged = listString(port.untagged)
            ports = listString(concatDict[item])

            f.write(ports + ": \n")
            if (port.portDescription != ""):
                f.write("Description: " + portDesc + "\n")
            if (len(port.tagged) > 0):
                f.write("Tagged vlans: " + tagged + "\n")
            if (len(port.untagged) > 0):
                f.write("Untagged vlans: " + untagged + "\n")
            if (len(port.tagged) + len(port.untagged) == 0):
                if (port.isTrunk == True):
                    f.write("Trunk port\n")
                else:
                    f.write("No vlans assigned\n")
            f.write("\n")
    case 'template_long':
        for key in portDict:
            port = portDict[key]
            if (port.portEnabled or showDisabled):
                portDesc = port.portDescription
                tagged = listString(port.tagged)
                untagged = listString(port.untagged)
                f.write(key + ": \n")
                if (port.portDescription != ""):
                    f.write("Description: " + portDesc + "\n")
                if (port.subslot != None):
                    f.write("Subslot: " + port.subslot + "\n")
                if (len(port.tagged) > 0):
                        f.write("Tagged vlans: " + tagged + "\n")
                if (len(port.untagged) > 0):
                        f.write("Untagged vlans: " + untagged + "\n")
                if (len(port.tagged) + len(port.untagged) == 0):
                    if (port.isTrunk == True):
                        f.write("Trunk port\n")
                    else:
                        f.write("No vlans assigned\n")
                f.write("\n")
    case _:
        print("Invalid Output Mode")

f.close()