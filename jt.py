import io
import struct
import sys
import zlib
from uuid import UUID

elements = dict()

class TocEntry:
    def __init__(self, segmentOffset, segmentLength, segmentAttributes):
        self.segmentOffset = segmentOffset
        self.segmentLength = segmentLength
        self.segmentAttributes = segmentAttributes
class DataSegment:
    def __new__(cls, data, tocEntry):
        segmentTypes = {
            1: LsgSegment,
            4: MetaDataSegment,
            6: ShapeLodSegment
            }
        data.seek(tocEntry.segmentOffset)
        segmentId = UUID(bytes_le=data.read(16))
        segmentType, segmentLength = struct.unpack("=II", data.read(8))
        if segmentType <= 4:
            compressionFlag, compressedDataLength, compressionAlgorithm = struct.unpack("=IIB", data.read(9))
            objectData = io.BytesIO(zlib.decompress(data.read(compressedDataLength)))
        else:
            objectData = data
        return segmentTypes[segmentType](objectData)
class LsgSegment:
    def __init__(self, data):
        for i in range(2):
            while LogicalElement(data):
                pass
        versionNumber, elementPropertyTableCount = struct.unpack("=HI", data.read(6))
        for i in range(elementPropertyTableCount):
            elementObjectId, keyPropertyAtomObjectId = struct.unpack("=II", data.read(8))
            while keyPropertyAtomObjectId != 0:
                valuePropertyAtomObjectId, = struct.unpack("=I", data.read(4))
                elements[elementObjectId].property[elements[keyPropertyAtomObjectId]] = elements[valuePropertyAtomObjectId]
                keyPropertyAtomObjectId, = struct.unpack("=I", data.read(4))
        for element in elements.values():
            if isinstance(element, BaseNode):
                element.attribute = list()
                for attributeObjectId in element.attributeObjectId:
                    element.attribute.append(elements[attributeObjectId])
                del element.attributeObjectId
            if isinstance(element, GroupNode):
                element.childNode = list()
                for childNodeObjectId in element.childNodeObjectId:
                    element.childNode.append(elements[childNodeObjectId])
                del element.childNodeObjectId
class MetaDataSegment:
    def __init__(self, data):
        while LogicalElement(data):
            pass
class ShapeLodSegment:
    def __init__(self,data):
        LogicalElement(data)
class LogicalElement:
    def __new__(cls, data):
        objectTypeIdentifiers = {
            (0xffffffff, 0xffff, 0xffff, 0xff, 0xff, 0xffffffffffff): None,
            (0x10dd1035, 0x2ac8, 0x11d1, 0x9b, 0x6b, 0x0080c7bb5997): BaseNode,
            (0x10dd101b, 0x2ac8, 0x11d1, 0x9b, 0x6b, 0x0080c7bb5997): GroupNode,
            (0x10dd102a, 0x2ac8, 0x11d1, 0x9b, 0x6b, 0x0080c7bb5997): InstanceNode,
            (0x10dd102c, 0x2ac8, 0x11d1, 0x9b, 0x6b, 0x0080c7bb5997): LodNode,
            (0xce357245, 0x38fb, 0x11d1, 0xa5, 0x06, 0x006097bdc6e1): MetaDataNode,
            (0xce357244, 0x38fb, 0x11d1, 0xa5, 0x06, 0x006097bdc6e1): PartNode,
            (0x10dd103e, 0x2ac8, 0x11d1, 0x9b, 0x6b, 0x0080c7bb5997): PartitionNode,
            (0x10dd104c, 0x2ac8, 0x11d1, 0x9b, 0x6b, 0x0080c7bb5997): RangeLodNode,
            (0x10dd1059, 0x2ac8, 0x11d1, 0x9b, 0x6b, 0x0080c7bb5997): BaseShapeNode,
            (0x10dd107f, 0x2ac8, 0x11d1, 0x9b, 0x6b, 0x0080c7bb5997): VertexShapeNode,
            (0x10dd1077, 0x2ac8, 0x11d1, 0x9b, 0x6b, 0x0080c7bb5997): TriStripSetShapeNode,
            (0x10dd1030, 0x2ac8, 0x11d1, 0x9b, 0x6b, 0x0080c7bb5997): MaterialAttribute,
            (0x10dd1046, 0x2ac8, 0x11d1, 0x9b, 0x6b, 0x0080c7bb5997): PolylineSetShapeNode,
            (0x10dd1083, 0x2ac8, 0x11d1, 0x9b, 0x6b, 0x0080c7bb5997): GeometricTransformAttribute,
            (0x10dd104b, 0x2ac8, 0x11d1, 0x9b, 0x6b, 0x0080c7bb5997): BasePropertyAtom,
            (0x10dd106e, 0x2ac8, 0x11d1, 0x9b, 0x6b, 0x0080c7bb5997): StringPropertyAtom,
            (0xe0b05be5, 0xfbbd, 0x11d1, 0xa3, 0xa7, 0x00aa00d10954): LateLoadedPropertyAtom,
            (0x10dd1019, 0x2ac8, 0x11d1, 0x9b, 0x6b, 0x0080c7bb5997): FloatingPointPropertyAtom,
            (0xce357247, 0x38fb, 0x11d1, 0xa5, 0x06, 0x006097bdc6e1): PropertyProxyMetaData,
            (0x10dd10a4, 0x2ac8, 0x11d1, 0x9b, 0x6b, 0x0080c7bb5997): BaseShapeLod,
            (0x10dd10b0, 0x2ac8, 0x11d1, 0x9b, 0x6b, 0x0080c7bb5997): VertexShapeLod,
            (0x10dd10ab, 0x2ac8, 0x11d1, 0x9b, 0x6b, 0x0080c7bb5997): TriStripSetShapeLod,
            }
        objectTypeIdentifiers = dict((UUID(fields=k), v) for (k,v) in objectTypeIdentifiers.items())

        elementLength, = struct.unpack("=I", data.read(4))
        element = io.BytesIO(data.read(elementLength))
        objectTypeId = UUID(bytes_le=element.read(16))
        objectType = objectTypeIdentifiers[objectTypeId]
        if not objectType:
            return
        objectBaseType, objectId = struct.unpack("=BI", element.read(5))
        logicalElement = objectType(element)
        elements[objectId] = logicalElement
        return logicalElement
class BaseNode:
    def __init__(self, data):
        versionNumber, self.nodeFlags, attributeCount = struct.unpack("=HII", data.read(10))
        self.attributeObjectId = struct.unpack("={}I".format(attributeCount), data.read(4*attributeCount))
        self.property = dict()
class GroupNode(BaseNode):
    def __init__(self, data):
        BaseNode.__init__(self, data)
        versionNumber, childCount = struct.unpack("=HI", data.read(6))
        self.childNodeObjectId = struct.unpack("={}I".format(childCount), data.read(4*childCount))
class PartitionNode(GroupNode):
    def __init__(self, data):
        GroupNode.__init__(self, data)
        self.partitionFlags, count = struct.unpack("=II", data.read(8))
        self.fileName = data.read(count*2).decode("utf-16")
        reservedField = struct.unpack("=6f", data.read(24))
        if self.partitionFlags & 1 == 0:
            self.transformedBbox = reservedField
        self.area, = struct.unpack("=f", data.read(4))
        self.vertexCountRange = struct.unpack("=2I", data.read(8))
        self.nodeCountRange = struct.unpack("=2I", data.read(8))
        self.polygonCountRange = struct.unpack("=2I", data.read(8))
        if self.partitionFlags & 1 != 0:
            self.untransformedBbox = struct.unpack("=6f", data.read(24))
class MetaDataNode(GroupNode):
    def __init__(self, data):
        GroupNode.__init__(self, data)
        version, = struct.unpack("=H", data.read(2))
class PartNode(MetaDataNode):
    def __init__(self, data):
        MetaDataNode.__init__(self, data)
        version, reservedField = struct.unpack("=HI", data.read(6))
class LodNode(GroupNode):
    def __init__(self, data):
        GroupNode.__init__(self, data)
        version, count = struct.unpack("=HI", data.read(6))
        reservedField = struct.unpack("={}fI".format(count), data.read(4*count + 4))
class RangeLodNode(GroupNode):
    def __init__(self, data):
        LodNode.__init__(self, data)
        version, count = struct.unpack("=HI", data.read(6))
        self.rangeLimits = struct.unpack("={}f".format(count), data.read(4*count))
        self.center = struct.unpack("=3f", data.read(12))
class BaseShapeNode(BaseNode):
    def __init__(self, data):
        BaseNode.__init__(self, data)
        versionNumber, = struct.unpack("=H", data.read(2))
        reservedField = struct.unpack("=6f", data.read(24))
        self.untransformedBbox = struct.unpack("=6f", data.read(24))
        self.area, = struct.unpack("=f", data.read(4))
        self.vertexCountRange = struct.unpack("=2I", data.read(8))
        self.nodeCountRange = struct.unpack("=2I", data.read(8))
        self.polygonCountRange = struct.unpack("=2I", data.read(8))
        self.size, self.compressionLevel = struct.unpack("=If", data.read(8))
class VertexShapeNode(BaseShapeNode):
    def __init__(self, data):
        BaseShapeNode.__init__(self, data)
        versionNumber, self.vertexBinding = struct.unpack("=HQ", data.read(10))
        self.quantizationParameters = struct.unpack("=4B", data.read(4))
        if versionNumber != 1:
            self.vertexBinding, = struct.unpack("=Q", data.read(8))
class TriStripSetShapeNode(VertexShapeNode):
    pass
class BaseAttribute:
    def __init__(self, data):
        versionNumber, self.stateFlags, self.fieldInhibitFlags = struct.unpack("=HBI", data.read(7))
        self.property = dict()
class MaterialAttribute(BaseAttribute):
    def __init__(self, data):
        BaseAttribute.__init__(self, data)
        versionNumber, self.dataFlags = struct.unpack("=HH", data.read(4))
        self.ambientColor = struct.unpack("=4f", data.read(16))
        self.diffuseColorAndAlpha = struct.unpack("=4f", data.read(16))
        self.specularColor = struct.unpack("=4f", data.read(16))
        self.emissionColor = struct.unpack("=4f", data.read(16))
        self.shininess, = struct.unpack("=f", data.read(4))
        if versionNumber == 2:
            self.reflectivity, = struct.unpack("=f", data.read(4))
class PolylineSetShapeNode(VertexShapeNode):
    def __init__(self, data):
        VertexShapeNode.__init__(self, data)
        versionNumber, self.areaFactor = struct.unpack("=Hf", data.read(6))
        if versionNumber != 1:
            self.vertexBindings, = struct.unpack("=Q", data.read(8))
class InstanceNode(BaseNode):
    def __init__(self, data):
        BaseNode.__init__(self, data)
        versionNumber, self.childNodeObjectId = struct.unpack("=HI", data.read(10))
class GeometricTransformAttribute(BaseAttribute):
    def __init__(self, data):
        BaseAttribute.__init__(self, data)
        versionNumber, storedValuesMask = struct.unpack("=HH", data.read(4))
        self.elementValue = [1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]
        for i in range(16):
            if storedValuesMask & 0x8000:
                self.elementValue[i] = struct.unpack("=ff", data.read(8))
            storedValuesMask = storedValuesMask << 1
class BasePropertyAtom:
    def __init__(self, data):
        versionNumber, self.stateFlags = struct.unpack("=HI", data.read(6))
class StringPropertyAtom(BasePropertyAtom):
    def __new__(cls, data):
        basePropertyAtom = BasePropertyAtom(data)
        versionNumber, count = struct.unpack("=HI", data.read(6))
        value = data.read(count*2).decode("utf-16")
        return value
class LateLoadedPropertyAtom(BasePropertyAtom):
    def __init__(self, data):
        BasePropertyAtom.__init__(self, data)
        versionNumber, segmentId, self.segmentType, self.payloadObjectId, reserved = struct.unpack("=H16s3I", data.read(30))
        self.segmentId = UUID(bytes_le=segmentId)
class FloatingPointPropertyAtom(BasePropertyAtom):
    def __init__(self, data):
        BasePropertyAtom.__init__(self, data)
        versionNumber, self.value = struct.unpack("=Hf", data.read(6))
class PropertyProxyMetaData:
    def __init__(self, data):
        versionNumber, count = struct.unpack("=HI", data.read(6))
        self.property = dict()
        while count > 0:
            propertyKey = data.read(count*2).decode("utf-16")
            propertyValueType, = struct.unpack("=B", data.read(1))
            if propertyValueType == 1:
                count, = struct.unpack("=I", data.read(4))
                propertyValue = data.read(count*2).decode("utf-16")
            elif propertyValueType == 2:
                propertyValue, = struct.unpack("=I", data.read(4))
            elif propertyValueType == 3:
                propertyValue, = struct.unpack("=f", data.read(4))
            elif propertyValueType == 4:
                propertyValue = struct.unpack("=6H", data.read(12))
            self.property[propertyKey] = propertyValue
            count, = struct.unpack("=I", data.read(4))
class BaseShapeLod:
    def __init__(self, data):
        versionNumber, = struct.unpack("=H", data.read(2))
class VertexShapeLod:
    def __init__(self, data):
        BaseShapeLod.__init__(self, data)
        versionNumber, self.vertexBindings = struct.unpack("=HQ", data.read(10))
class TriStripSetShapeLod(VertexShapeLod):
    pass

f = open(sys.argv[1], "rb")
version, byteOrder, reservedField, tocOffset, lsgSegmentId = struct.unpack("=80s?II16s", f.read(105))
lsgSegmentId = UUID(bytes_le=lsgSegmentId)

tocSegment = dict()
f.seek(tocOffset)
entryCount = struct.unpack("=I", f.read(4))[0]
for entry in range(entryCount):
    segmentId = UUID(bytes_le=f.read(16))
    tocSegment[segmentId] = TocEntry(*struct.unpack("=III", f.read(12)))

DataSegment(f, tocSegment[lsgSegmentId])
