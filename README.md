# Hole Detection Dataset

This repository contains scripts to extract single CAD parts and corresponding labels for the extracted parts.
The classes are 0 (no hole) and 1 (hole). This dataset is derived from the assembly dataset from 
Lupinetti et al. under http://3dassemblyrepository.ge.imati.cnr.it/.

The extraction of single parts follows the methodology described in our paper *Evaluating Rule- and Learning-Based Strategies
for Fastener Hole Detection* (links in references below).

The steps to obtain the single CAD parts from the assemblies and the structure of the labels are described in the
chapters below.


## Obtaining single parts

First download all areas from http://3dassemblyrepository.ge.imati.cnr.it/ and place them in a single folder
(click the images of the areas to download the .rar files).
Then decompress all `.rar` files (e.g. using 7-zip or unrar).

Your folder structure should look as follows:

```
main_folder/
├── CouplingFlange/
│   └── Coupling flange/
├── Differential/
│   └── Differential/
├── DoubleRotorTurbine/
│   └── Double rotor turbin/
├── HydraulicReduction/
│   └── Hydraulic reduction/
├── HydraulicRotor/
│   └── Hydraulic rotor/
├── LandingGear/
│   └── Landing gear/
├── LinearActuator/
│   └── Linear actuor/
├── MillMax/
│   └── Mill max/
├── Other/
│   └── Other/
├── PropellerMixer/
│   └── Propeller mixer/
├── RotorWindTurbine/
│   └── Rotor wind turbin/
```

Then run the script to extract the single CAD-parts from the assemblies.

```
python -m part_extraction "path/to/downloaded/dataset" "path/to/extract/files/to"
```

## Labels

In the labels folder csv-files for the respective parts can be found.
The labels "1" correspond to the hole faces. Shown below is an example of how the labels can be used.

```python
import cadquery as cq

# load the step file
workplane = cq.importers.importStep("path/to/step_file.stp")

# extract the single solid it contains
part = workplane.solids.vals()[0]  # assumes exactly one solid

# load the corresponding label-csv
with open("label_file.csv") as f:
    labels = list(map(int, f.read().strip().split(",")))

# Example of using the labels to obtain hole faces
hole_faces = [face for label, face in zip(labels, part.Faces()) if label == 1]
```


## References

- Lupinetti, K., Giannini, F., Monti, M., Pernot, J.-P. (2019).  
  *Content-based multi-criteria similarity assessment of CAD assembly models*.  
  Computers in Industry, 112, 103111.  
  https://doi.org/10.1016/j.compind.2019.07.001

- Kai Schütte, Edgar Heinert, Matthias Rottmann.  
  *Evaluating Rule- and Learning-Based Strategies
for Fastener Hole Detection*.  
  Preprint, 2026.  
  Available at: https://arxiv.org/abs/XXXX.XXXXX
