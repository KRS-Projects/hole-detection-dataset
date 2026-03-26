import os
import time
import logging
from typing import Iterable, cast as tcast, List
from OCP.TopTools import TopTools_IndexedMapOfShape  # used to check if has faces
from OCP.TopAbs import TopAbs_FACE  # used to check if has faces
from OCP.TopExp import TopExp
from OCP.TopoDS import TopoDS_Shape
from OCP.TDataStd import TDataStd_Name
from OCP.Standard import Standard_GUID
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.IFSelect import IFSelect_RetDone
from OCP.TDF import TDF_LabelSequence, TDF_Label, TDF_AttributeIterator
from OCP.TopLoc import TopLoc_Location
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.XCAFDoc import XCAFDoc_DocumentTool

logger = logging.getLogger(__name__)

def check_filename(filename: str) -> None:
    """
    This function simply checks if the filename is correct and raises an error, if it is not the case.

    :param filename: The path to the file.
    """
    if not os.path.isfile(filename):
        raise FileNotFoundError("%s not found." % filename)

    if not isinstance(filename, str):
        raise TypeError(f"Filename not type string: {type(filename)}")

    if not filename.split(".")[-1].lower() in ["stp", "step"]:
        raise TypeError(f"Wrong file extension: {filename.split('.')[-1]}")

        
        
def load_step(filename: str) -> List[dict]:
    """
    This function recursively iterates through the elements in the Step-file while adding them
    to a list of Dictionaries. The elements location in the Step-file is denoted in the "Tree"
    item of the dictionary (e.g. 0.0.17.0.1). Elements that have no faces are filtered out.
    Assemblies and Subassemblies are included.

    :param filename: The filename of the step-file to be loaded.
    ...
    :returns: A list of all the shapes and assemblies with their corresponding names.
    """
    check_filename(filename)

    # the output list
    output_shapes = []

    # Location list, to set subassembly location
    locs = []

    # create handle to a document
    doc = TDocStd_Document(TCollection_ExtendedString("test-doc"))

    # Get root assembly
    shape_tool = XCAFDoc_DocumentTool().ShapeTool_s(doc.Main())

    # set Reader parameters
    step_reader = STEPCAFControl_Reader()
    # reduced tolerance etc. possible?
    step_reader.SetLayerMode(True)
    step_reader.SetNameMode(True)
    step_reader.SetMatMode(True)
    step_reader.SetGDTMode(True)

    # Read file. This is the part that takes time.
    start = time.time()
    status = step_reader.ReadFile(filename)
    if status == IFSelect_RetDone:
        logger.info("Starting to load file")
        step_reader.Transfer(doc)
    logger.info(f"Read File. Duration: {time.time() - start} seconds.")
    
    def _get_sub_shapes(lab, loc, tree):
        l_subss = TDF_LabelSequence()
        shape_tool.GetSubShapes_s(lab, l_subss)

        if shape_tool.IsAssembly_s(lab):
            l_c = TDF_LabelSequence()
            shape_tool.GetComponents_s(lab, l_c)
            for i in range(l_c.Length()):
                label = l_c.Value(i + 1)
                if shape_tool.IsReference_s(label):
                    label_reference = TDF_Label()
                    shape_tool.GetReferredShape_s(label, label_reference)
                    loc = shape_tool.GetLocation_s(label)

                    locs.append(loc)

                    _get_sub_shapes(label_reference, loc, tree + '.' + str(i))
                    locs.pop()

                    # if none were added, add this
                    loc = TopLoc_Location()
                    for l in locs:
                        loc = loc.Multiplied(l)
                    shape = shape_tool.GetShape_s(lab)
                    shape_disp = BRepBuilderAPI_Transform(shape, loc.Transformation()).Shape()
                    tree_temp = tree
                    if has_faces(shape_disp):
                        if not any([i["Tree"] == tree_temp for i in output_shapes]):
                            output_shapes.append({
                                'Shape': shape_disp,
                                'Tree': tree_temp,
                                'Name': GetLabelName(lab),
                            })

        elif shape_tool.IsSimpleShape_s(lab):
            shape = shape_tool.GetShape_s(lab)

            # add the locations of the assemblies this part belongs to
            loc = TopLoc_Location()
            for l in locs:
                loc = loc.Multiplied(l)

            shape_disp = BRepBuilderAPI_Transform(shape, loc.Transformation()).Shape()
            tree_temp = tree + '.(' + str(0) + ')'

            if has_faces(shape_disp):
                if not any([i["Tree"] == tree_temp for i in output_shapes]):
                    output_shapes.append({
                        'Shape': shape_disp,
                        'Tree': tree_temp,
                        'Name': GetLabelName(lab),
                    })

            for i in range(l_subss.Length()):
                tree_temp = tree + '(' + str(i + 1) + ')'

                lab_subs = l_subss.Value(i + 1)
                shape_sub = shape_tool.GetShape_s(lab_subs)
                shape_to_disp = BRepBuilderAPI_Transform(shape_sub, loc.Transformation()).Shape()

                if has_faces(shape_to_disp):
                    if not any([i["Tree"] == tree_temp for i in output_shapes]):
                        output_shapes.append({
                            'Shape': shape_to_disp,
                            'Tree': tree_temp,
                            'Name': GetLabelName(lab_subs),
                        })

    logger.info("Getting Subshapes.")
    start = time.time()

    labels = TDF_LabelSequence()
    shape_tool.GetFreeShapes(labels)

    for j in range(labels.Length()):
        root_item = labels.Value(j + 1)
        _get_sub_shapes(root_item, None, '.' + str(j))

    logger.info(f"Duration getting subshapes {time.time() - start}")

    return output_shapes


def GetLabelName(label) -> str | None:
    """ This function obtains the name of the shape from its label, if a name is present.

    :param label: The label of a shape.
    ...
    :returns: The name of the shape (if available).
    """
    label_it = TDF_AttributeIterator(label)
    while label_it.More():
        attr = label_it.Value()
        if Standard_GUID.IsEqual_s(attr.ID(), TDataStd_Name.GetID_s()):
            return attr.Get().ToExtString()
        label_it.Next()
    return None


def has_faces(shape: TopoDS_Shape) -> bool:
    """
    Checks if the shape has faces

    :param shape: A Shape object.
    ...
    :returns: Boolean, whether the shape has faces.    
    """
    shape_set = TopTools_IndexedMapOfShape()
    TopExp.MapShapes_s(shape, TopAbs_FACE, shape_set)
    return len([i for i in tcast(Iterable[TopoDS_Shape], shape_set)]) > 0
