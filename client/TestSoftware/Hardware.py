#Hardware.py
import sys
from DChains import DChains
#MUX dict
  #Given JX, set MUXes

cardAddresses = [0x19, 0x1A, 0x1B, 0x1C]
def getCardAddress(slot):
    if slot in [2,7,18,23] : return cardAddresses[0]
    if slot in [3,8,19,24] : return cardAddresses[1]
    if slot in [4,9,20,25] : return cardAddresses[2]
    if slot in [5,10,21,26]: return cardAddresses[3]

def getReadoutSlot(slot):
    if slot in [2,3,4,5] : return     4
    if slot in [7,8,9,10] : return    3
    if slot in [18,19,20,21] : return 2
    if slot in [23,24,25,26] : return 1
def ngccmGroup(rm):
    i2cGroups = [0x01, 0x10, 0x20, 0x02]
    return i2cGroups[rm-1]

def openChannel(slot, bus):
    rmLoc = getReadoutSlot(slot)
    if rmLoc in [3,4]:
      # Open channel to ngCCM for RM 3,4: J1 - J10
        bus.write(0x72,[0x02])
    elif rmLoc in [1,2]:
      # Open channel to ngCCM for RM 1,2: J17 - J26
        bus.write(0x72,[0x01])
    else:
        print 'Invalid RM = ', rmLoc
        print 'Please choose RM = {1,2,3,4}'
        return 'closed channel'
  # Open channel to i2c group
    bus.write(0x74, [ngccmGroup(rmLoc)])
    bus.read(0x74, 2)

  # Reset the backplane
    bus.write(0x00,[0x06])
    return bus.sendBatch()

#Get DChains
def getDChains(slot, bus):
    openChannel(slot, bus)
    return DChains(getCardAddress(slot), bus)

#SetQInjMode(t)
def SetQInjMode(onOffBit, slot, bus):
    openChannel(slot, bus)
    #expects onOffBit of 0 or 1
    if onOffBit == 0 or onOffBit == 1:
        bus.write(getCardAddress(slot),[0x11,0x03,0,0,0])
        bus.write(0x09,[0x11,onOffBit,0,0,0])
        bus.sendBatch()
    else:
        print "INVALID INPUT IN SetQInjMode... doing nothing"

# Cryptic 0x70 Reset
def reset(ngccm): #RM4,3->ngccm2 -- RM2,1->ngccm1
    b.write(0x72,[ngccm])
    b.write(0x74,[0x08])
    b.write(0x70,[0x3,0])
    b.write(0x70,[0x1,0])
    b.sendBatch()


# Converts ADC to fC (Nate Chaverin's class)
class ADCConverter:
    # Bitmasks for 8-bit ADC input

    expMask = 192
    manMask = 63
    baseSensitivity = 3.1
    # Base charges for each subrange
    # Use array for which 0 ADC = 0 fC input charge
    inputCharge = [
        -1.6, 48.4, 172.4, 433.4, 606.4,
        517, 915, 1910, 3990, 5380,
        4780, 7960, 15900, 32600, 43700,
        38900, 64300, 128000, 261000, 350000
    ]

    #Defines the size of the ADC mantissa subranges
    adcBase = [0, 16, 36, 57, 64]

    # A class to convert ADC to fC
    fc = {}

    def __init__(self):
        # Loop over exponents, 0 - 3
        for exp in xrange(0, 4):
            # Loop over mantissas, 0 - 63
            for man in xrange(0, 64):
                subrange = -1
                # Find which subrange the mantissa is in
                for i in xrange(0, 4):
                    if man >= self.adcBase[i] and man < self.adcBase[i + 1]:
                        subrange = i

                if subrange == -1:
                    print "Something has gone horribly wrong!"

                # Sensitivity = 3.1 * 8^exp * 2^subrange
                sensitivity = self.baseSensitivity * 8.0**float(exp) * 2.0**subrange
                # Add sensitivity * (location in subrange) to base charge
                #fc[exp * 64 + man] = (inputCharge[exp * 5 + subrange] + ((man - adcBase[subrange])) * sensitivity) / gain;
                self.fc[exp * 64 + man] = self.inputCharge[exp * 5 + subrange] + ((man - self.adcBase[subrange]) + .5) * sensitivity

    def linearize(self, adc):
        return self.fc[adc]
