import numpy as np
import sys
import math
import copy
import heapq
import operator #for sorting lists of classes by attribute
import bitstring
from timeit import default_timer as timer
from datetime import timedelta

class HuffmanNode:
    """Huffman encoding tree node"""
    
    character = -1      #the character represented
    index = -1          #index of character (integer)
    count = -1          #character frequency (count) in the file
    left = []           #left child node
    right = []          #right child node
    code = bitstring.BitString()    #bitstring code for the character
    
    #constructor
    def __init__(self,character):
        self.character = character;
        self.index = int.from_bytes(self.character, sys.byteorder)
        self.count = 0
    
    #for printing
    def __repr__(self):
        return str("Huffman Node") + str(self.__dict__)
        
    #for printing
    def __str__(self):
        return str("Huffman Node") + str(self.__dict__)
        
    #comparison operator required for heapq comparison
    def __lt__(self, other):
        return self.count < other.count

    #print function (non-recursive)
    def print(self):
        print("Huffman Node: ")
        print("\tCharacter = ", self.character)
        print("\tIndex = ", self.index)
        print("\tCount = ", self.count)
        has_left = (self.left != [])
        has_right = (self.right != [])
        print("\tHas left child = ", has_left)
        print("\tHas right child = ", has_right)
        print("\tCode = ", self.code)

def getfilecharactercounts(filename):
    """ Read a file and count characters """

    f = open(filename,"rb")
    nodes = [];
    
    #for every character of interest (and then some) create a huffman node
    for i in range(0,256):
        nodes.append(HuffmanNode(bytes([i]))) #works in python 3
    
    #loop over file reading a character at a time and increment the count
    #of that character in the list of huffman nodes
    while True:
        c = f.read(1)
        if c:
            index = int.from_bytes(c, sys.byteorder)
            nodes[index].count += 1
        else:
            print("End of file")
            break

    f.close()

    #Create one for pseudoeof
    #Pseudoeof read in actual content section indicate end of file
    PSEUDOEOF = bitstring.BitString()
    PSEUDOEOF.append(bin(256))
    nodes.append(HuffmanNode(PSEUDOEOF))
    nodes[-1].count += 1

    nodes.sort()
    curr = 0
    #Delete empty count nodes (Trimming)
    while(nodes[curr].count == 0):
        nodes.pop(curr)
    return nodes


def createhuffmantree(huffmannodes):
    """ Create the huffman tree
        Using heapq functionality to build the tree from a priority queue"""

    node_heap = copy.deepcopy(huffmannodes)  #first create a copy
    heapq.heapify(node_heap)                 #create heap
    print(node_heap)
    # #Code Missing: Create the Huffman Node Tree using the Min Priority Queue (heap)
    for i in range(len(huffmannodes) - 1):
        leftNode = heapq.heappop(node_heap)
        rightNode = heapq.heappop(node_heap)
        parentNode = HuffmanNode(bytes([0])) #Random char chosen since the char value does not matter
        parentNode.count = leftNode.count + rightNode.count
        parentNode.left = leftNode
        parentNode.right = rightNode
        heapq.heappush(node_heap, parentNode)
    return heapq.heappop(node_heap) #final node is the tree we want


def codehuffmantree(huffmantreenode, nodecode, PSEUDOEOFHuffmanCode):
    """ Traverse Huffman Tree to produce Prefix Codes"""
    #huffmantreenode.print()
    #print("Nodecode = ", nodecode)

    if (huffmantreenode.left == [] and huffmantreenode.right == []):
        huffmantreenode.code = nodecode     #no children - assign code
        if(huffmantreenode.character == bitstring.BitString('0b100000000')):
            PSEUDOEOFHuffmanCode.append(nodecode)
    else:
        leftcode = copy.copy(nodecode)      #append 0 to left
        leftcode.append(bitstring.Bits('0b0'))
        codehuffmantree(huffmantreenode.left,leftcode, PSEUDOEOFHuffmanCode)
        rightcode = copy.copy(nodecode)     #append 1 to right
        rightcode.append(bitstring.Bits('0b1'))
        codehuffmantree(huffmantreenode.right,rightcode, PSEUDOEOFHuffmanCode)


def listhuffmancodes(huffmantreenode, codelist):
    """ Create a list of Prefix Codes from the Huffman Tree"""
    if (huffmantreenode.left == [] and huffmantreenode.right == []):
        codelist[huffmantreenode.index] = huffmantreenode.code
    else:
        listhuffmancodes(huffmantreenode.left,codelist)
        listhuffmancodes(huffmantreenode.right,codelist)


def huffmanencodefile(filename):
    """ Read and Encode a File using Huffman Codes"""

    counts = getfilecharactercounts(filename) #get the counts from the file

    huffmantree = createhuffmantree(counts) #create and encode the characters
    PSEUDOEOFHuffmanCode = bitstring.BitString()
    codehuffmantree(huffmantree,bitstring.BitString(),PSEUDOEOFHuffmanCode)

    codelist = [None]*256
    listhuffmancodes(huffmantree, codelist) #get the codes for each character


    for i in range(0,256):
        if codelist[i] != None:
            print("character ", chr(i), " maps to code ", codelist[i].bin)

    #encode the file
    with open(filename, 'rb') as f:
        filecode = bitstring.BitString()
        while True:
            c = f.read(1)
            index = int.from_bytes(c, sys.byteorder)
            if c:
                filecode.append(codelist[index])
            else:
                break #eof


    #write the file
    with open(filename + ".huf", 'wb') as coded_file:
        finalEncodedFile = bitstring.BitString()
        """
        Start of file - Header - using Pre-order Traversal
        0 means not a leaf node. 1 means is a left node
        If 1, then write out the character binary value in ASCII (8-bits) format
        """
        #The Header
        header = bitstring.BitString()
        huffmanencodefileHeader(huffmantree, header)
        finalEncodedFile.append(header)
        #Mark the end of header and start of the actual content
        #Actual content and EOF--------------------------------------
        filecode.append(PSEUDOEOFHuffmanCode)
        #Write actual content and EOF onto file ----------------------------
        finalEncodedFile.append(filecode)
        print(len(finalEncodedFile))
        #Paddding to make byte size  ------------------------------------------
        if(len(finalEncodedFile) % 8 != 0):
            timesToPad = 8 - (len(finalEncodedFile) % 8)
            for i in range(timesToPad):
                finalEncodedFile.append(bitstring.Bits('0b0')) #Pad with 0 to make it multiple of 8 bits
        print(len(finalEncodedFile))
        #Write it all onto the file
        coded_file.write(finalEncodedFile.bytes)

def huffmandecodefile(filename):
    """ Decode a Huffman-Coded File"""

    """ For the Actual content """
    decodedFile = "" #Hold the text in string instead bitstring
    currentBitString = bitstring.BitString() #Will check which huffman code correspond to the currentBitString value
    huffmancodeList = [] #Store the keys to huffmancodeDict

    """ For the Header """
    huffmancodeDict = {} #Stores the huffman code and their characters
    key = bitstring.BitString() #Hold the huffman code
    value = bitstring.BitString() #Hold the character in binary value
    readValue = False #Indicate whether the value currently being read is a value. True when it is value.
    bitCounter = 0 #Indicate the number of bits that has already been appended to value
    currentLevel = 0 #Indicate the current depth in tree, with 0 being the root node level
    leftTraversed = [False] #Whether the left node has been traversed
    rightTraversed = [False] #Whether the right node has been traversed

    """ Actual Decoding """
    compressedFile = bitstring.ConstBitStream(filename = filename)
    #Get the dictionary of huffman codes
    # huffmandecodefileHeader(compressedFile,currentLevel,leftTraversed,rightTraversed,readValue,bitCounter,key,value,huffmancodeDict)
    c = compressedFile.read(1) #skip the first one
    startTimeDecodeHeader = timer()
    while True:
        c = compressedFile.read(1) #b holds the current byte value being read
        #Start of Header section
        #Fill up the huffmancodeList with keys and values
        #When currentLevel >= 0, it means that it's still in the header section
        if(currentLevel >= 0):
            #If you get 0 when left and right has not been traversed, and it's not in value reading mode
            if(c == bitstring.Bits('0b0') and leftTraversed[currentLevel] == False and rightTraversed[currentLevel] == False and readValue == False):
                key.append(bitstring.Bits('0b0')) #Add 0 to key
                leftTraversed[currentLevel] = True #It traversed the left
                currentLevel += 1
                leftTraversed.append(False) #The new current level has leftTraversed = False
                rightTraversed.append(False) #The new current level has rightTraversed = False
                #Left and right has not been traversed
            #If you get 0 while left has been traversed and right has not, and it's not in value reading mode
            elif(c == bitstring.Bits('0b0') and leftTraversed[currentLevel] == True and rightTraversed[currentLevel] == False and readValue == False):
                key.append(bitstring.Bits('0b1')) #Add 1 to key
                rightTraversed[currentLevel] = True #It traversed the right on that level
                currentLevel += 1
                leftTraversed.append(False) #The new current level has leftTraversed = False
                rightTraversed.append(False) #The new current level has rightTraversed = False
            #If you get 1 while left and right has not been traversed, and it's not in value reading mode
            elif(c == bitstring.Bits('0b1') and leftTraversed[currentLevel] == False and rightTraversed[currentLevel] == False and readValue == False):
                key.append(bitstring.Bits('0b0'))
                readValue = True #Start Reading Value up to 9 bits
                leftTraversed[currentLevel] = True #It traversed the left on that level
                currentLevel += 1
                leftTraversed.append(False) #The new current level has leftTraversed = False
                rightTraversed.append(False) #The new current level has rightTraversed = False
            #If you get 1 while left has been traversed and right has not, and it's not in value reading mode
            elif(c == bitstring.Bits('0b1') and leftTraversed[currentLevel] == True and rightTraversed[currentLevel] == False and readValue == False):
                key.append(bitstring.Bits('0b1')) #Add 1 to key
                readValue = True #Start Reading Value up to 9 bits
                rightTraversed[currentLevel] = True #It traversed the right on that level
                currentLevel += 1
                leftTraversed.append(False) #The new current level has leftTraversed = False
                rightTraversed.append(False) #The new current level has rightTraversed = False
            #When in reading mode
            elif(readValue == True):
                #0-7th bit
                if(bitCounter < 8):
                    value.append(c)
                    bitCounter += 1
                #When it reaches the 9th bit
                else:
                    value.append(c)
                    keyString = str(key)
                    huffmancodeDict[keyString] = value.copy()
                    huffmancodeList.append(keyString)
                    bitCounter = 0 #Restart bitcounter
                    readValue = False #No longer reading the value
                    currentLevel -= 1 #Go back down a level
                    leftTraversed.pop() #Remove the last index
                    rightTraversed.pop() #Remove the last index
                    del key[-1] #Cut off the last bit
                    value.clear() #Restart the value
            #Once left and right has been traversed
            while(leftTraversed[currentLevel] == True and rightTraversed[currentLevel] == True ):
                currentLevel -= 1 #Go back down a level
                if(currentLevel < 0):
                    break
                del key[-1] #Cut off the last bit
                #Left remains traversed
                leftTraversed.pop()
                rightTraversed.pop()
        # End of Header section
        # At this point, you already got the dictionary (huffmancodeDict) of huffman codes
        # Start of Actual Content Section
        else:
            endTimeDecodeHeader = timer()
            print(endTimeDecodeHeader-startTimeDecodeHeader)
            #Decode the content and append it to decodedFile
            huffmancodeList = huffmancodeDict.keys()
            currentBitString.append(c) #Add the current bit to the bitstring
            #Compare the currentBitString with the list of huffmancodes in huffmancodeList
            translatedFromBitString = 0
            for key in huffmancodeList:
                if(str(currentBitString) == key):
                    translatedFromBitString = huffmancodeDict.get(key).uint #Get the character binary string from the dict
                    if(int(translatedFromBitString) == 256): #256 indicating EOF
                        break
                    else:
                        decodedFile += chr(translatedFromBitString) #Add the character to the decodedFileString
                        currentBitString.clear() #Reset the currentBitString
            if(translatedFromBitString == 256): #256 indicating EOF
                break

    """ Write the decoded file into a .rtf file """
    #.txt to test out my file
    with open("fileWritten.rtf", 'w') as f:
        f.write(decodedFile)


""" 0 denotes parent node, 1 denotes leaf nodes"""
def huffmanencodefileHeader(huffmantreenode, header):
    #While the left node is not empty continue traversing until lowest left is reached
    if(huffmantreenode.left != []):
        header.append(bitstring.Bits('0b0')) #To show that it is not at a leaf node yet
        huffmanencodefileHeader(huffmantreenode.left, header)
        huffmanencodefileHeader(huffmantreenode.right, header)
    #When it is the lowest left leaf node
    elif(huffmantreenode.left == [] and huffmantreenode.right == []):
        header.append(bitstring.Bits('0b1')) #To show that it arrived at a leaf node
        if(len(huffmantreenode.character) % 9 != 0): #If they are 8-bits value, turn them into 9-bits
            nineBitValue = bitstring.BitString()
            nineBitValue.append(bitstring.Bits('0b0'))
            nineBitValue.append(huffmantreenode.character)
            header.append(nineBitValue)
        else:
            header.append(huffmantreenode.character) #The character value in bytes
    return

# #main
filename="./LoremIpsumLong.rtf"
startTimeEncode = timer()
huffmanencodefile(filename)
endTimeEncode = timer()
elapsedTimeEncode = endTimeEncode - startTimeEncode
print("It took the program ",elapsedTimeEncode, "s to encode the file")

startTimeDecode = timer()
huffmandecodefile(filename + ".huf") #uncomment once this file is written
endTimeDecode = timer()
elapsedTimeDecode = endTimeDecode - startTimeDecode
print("It took the program ",elapsedTimeDecode, "s to encode the file")




