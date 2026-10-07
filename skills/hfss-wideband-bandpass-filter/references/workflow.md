# Reproduction and optimization

Capture center convention, bandwidth definition, port impedance/reference planes, insertion/return-loss limits, ripple/group-delay limits, stopband ranges and required rejection. A bandwidth specification alone does not specify return loss or manufacturing tolerance. An audit can proceed while unprovided acceptance limits remain unknown.

Inspect dielectric slabs and internal electrodes, vias, ground planes, terminal pads, PCB substrate and launches. Establish electrical connectivity from geometry/history rather than names such as C or L. In LTCC, distinguish ceramic spacing, metal thickness, fired shrinkage, via diameter and alignment limits. Check unintended shorts/opens before optimization.

Record permittivity, loss tangent, conductivity, frequency dependence, conductor treatment and Solve Inside. Assess conductor thickness against skin depth rather than meshing all metal internally by default. Fired paste is not necessarily bulk silver. A lossy PCB launch belongs to the simulated assembly unless physically removed or consistently de-embedded in a comparison.

Inspect each terminal's signal connection and reference conductor. Preserve reference planes between candidates; fixture changes or renormalization can change reported loss without improving the intrinsic filter.

## Parameter search

Separate parameters by observed effect: resonant dimensions/capacitive spacing, coupling gaps/overlap, external coupling/launch dimensions, and fabrication limits. Estimate sensitivities from small allowed perturbations with full-wave results. Names alone do not establish a parameter's electrical effect.

Use equivalent circuits or size scaling for initial bounds. Approximately lumped resonance scales as 1/sqrt(LC), but coupling, shielding and distributed parasitics can invalidate naive scaling. A wideband filter cannot be certified by narrowband prototype coefficients or an axisymmetric waveguide surrogate.

MATLAB or Python can schedule bounded samples, fit response surfaces, and optimize a mask-based objective. Penalize bandwidth/center error, passband violation, stopband violation, parasitic passbands and manufacturing violations separately. Every proposed winner needs a native HFSS solution with consistent port normalization and adequate coverage. A fitted minimum is a candidate, not a verified optimum.

Preserve topology, layer count and connections when only dimension changes are allowed. Work on a copy and log parameters, solution identity, convergence, sweep kind, metrics and resource usage. Reject negative spacings, conductor collisions and invalid layer order before solving. Refine candidates only while the user's target remains unmet; do not invent a zero-loss objective or tolerance.

## Numerical cost

Do not copy enormous air regions or field-saving settings blindly. Validate open boundaries across the relevant range. Refine high-field gaps, vias and conductor edges selectively, then assess the change in S parameters.

For an authorized solve, monitor available physical RAM, commit headroom and solver working set. Field saving at every display point may be unnecessary for curve-only screening. Single-frequency convergence establishes the criterion at that adaptive frequency; broadband/multifrequency or selected edge/stopband checks provide evidence elsewhere. Stop before resource exhaustion.

Use one identified AEDT instance for a project. Back up results before closing or repairing file contention. Validate an actual S-parameter read rather than only a solution name. Preserve user source projects/results during skill creation.

## Primary references

- [HFSS adaptive meshing](https://ansyshelp.ansys.com/public/views/secured/electronics/v251/en/subsystems/hfss/Content/HFSS/AdaptiveMeshingMethodsInHFSS.htm)
- [Terminal renormalization](https://ansyshelp.ansys.com/public/views/secured/electronics/v261/en/subsystems/hfss/Content/HFSS/SetRenormalizingImpedanceforTerminals.htm)
- [Frequency sweeps](https://ansyshelp.ansys.com/public/Views/Secured/Electronics/v251/en/Subsystems/HFSS/Content/HFSS/AddingaFrequencySweepHFSS.htm)

Use documentation matching the installed release before changing settings. These references do not replace the user specification or material data.
