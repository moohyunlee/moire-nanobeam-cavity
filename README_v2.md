# Offset-Enabled Localization in a Finite Moiré Nanobeam Cavity
*Independent investigation of phase-sensitive mode formation, numerical convergence, local leakage control, and quamtum-emitter placement in a three-row GaAs moiré nanobeam*

> **Main result**: Introducing a relative lattice shift in the moiré cell produced reproducible mirror-related localized modes with $Q\approx7.5\times10^3$, while local interface refinement further increased the 2D simulated $Q$ to approximately $9.6\times10^3$.

## Overview
A commesurate 13:14 three-row GaAs moiré nanobeam was studied using MPB eigenmode analysis and Meep finite-difference time-domain simulation tools.

MPB was first used to identify candidate TE-like folded bands and field symmetries in the periodic ABA supercell. The selected candidates were then transferred to finite structures and tested through FDTD optimization and numerical convergence.

<p align="center">
  <img src="figures/meep/eta_map_offset.png" width="1500">
</p>

<p align="center">
  <em>Geometry, convergence result, offset-enabled localization, and final non-contact M19 design.</em>
</p>

At resolution 52, the unshifted M19 configuration produced a spatial extended response with $Q\approx404, C_{\mathrm{moire}}\approx0.008$ showing that the cavity-like resonance observed during lower-resolution screening was not numerically robust.

In contrast, relative shifts of the center row to (+0.3a) and (-0.3a) at moiré cell produced localized modes with nearly identical properties in opposite positions:

|Configuration|Offset|Gap|$Q$|$C_\mathrm{moire}$|
|:---|---:|---:|---:|---:|
|Unshifte|0|-|404|0.008|
|Offset|+0.3a|Original|7541|0.872|
|Offset, mirrored|-0.3a|Original|7547|0.872|
|Final non-contact|+0.3a|+0.01a|9583|0.882|

Reversing the shifted reversed the field-maximum position from approximately (+3.82a) to (-3.82a), while preserving the resonance frequency, quality factor, and localization metric.

A subsequent fixed-offset interface control showed that physical contact was not for the high-$Q$ localized response. A geometry with a (0.01a) gap reacehd $Q\approx9.6\times10^3, C_\mathrm{moire}\approx0.882$

These results support a hierarchical design interpretation:
> Relative phase enables the localized mode configuration, while local interface geometry primarily tunes its leakage.

## Key Findings
- Convergence rejected the initial unshifted-cavity interpretation.
- Relative lattice shift enabled a reproducible localized optical response.
- Opposite shifts generated symmetry-related modes with nearly identical $Q$ and localization.
- Local interface refinement changed leakage.
- The final cavity was evaluated using $Q$, localization, effective area, and emitter-placement tolerance.


## Workflow
### 1. MPB Mode Screening
Candidate folded bands and field symmetries were found in the periodic 13:14 ABA moiré supercell.

<p align="center">
  <img src="figures/mpb/target_bandgap.png" width="500">
</p>

<p align="center">
  <em>TE-like bands 93-95 near the target normalized-frequency range</em>
</p>

### 2. Finite-cavity validation

 Candidate MPB modes were transfarred to finite Meep structures and tested through $Q$, field localization ($C_\mathrm{moire}$), runtime, resolution convergence.
 
### 3. Offset and Interface Controls

Zero and opposite offsets were compared under identical conditions. A fixed-offset local-radius control was then used to test whether the localized response required physical contact at the interface.

<p align="center">
  <img src="figures/meep/final_geometry.png" width="500">
</p>

<p align="center">
  <em>M19 - Offset and mirror engineered geometry</em>
</p>
 
### 4. Emitter-oriented evaluation

Evaluate effective area and coupling sensitivity for a resonant (y)-oriented emitter.

## Result Summary
  <p align="center">
  <img src="figures/meep/final_geometry.png" width="1000">
</p>

<p align="center">
  <em>M19 - Offset and mirror engineered geometry</em>
</p>

## Limitations
- The primary optimization was performed using a 2D z-invariant model and therefore does not capture out-of-plane radiation; systematic 3D convergence remains future work.
- The placement analysis assumes a resonant, $y$-oriented dipole.
- The field maximum close to an etched air-hole boundary.
- Fabrication-disorder analysis and a matched conventional-cavity benchmark remain future work.

## Repository Structure
- code/       MPB and Meep simulation workflows
- figures/    geometry, fields, optimization, and robustness results
- data/       processed numerical results

## Reproduce
```bash
conda env create -f environment.yml
conda activate moire-cavity
```
