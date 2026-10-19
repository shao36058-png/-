---
name: hfss-wideband-bandpass-filter
description: "面向射频与微波工程的 HFSS 宽带带通滤波器、LTCC 滤波器复现、优化与结果检查。 Reproduce, inspect, optimize, and validate HFSS RF bandpass filters, especially multilayer LTCC filters with embedded conductors and PCB launches. Use for bandwidth extraction, insertion and return loss, stopband masks, terminal ports, layer-stack checks, and dimension optimization."
license: MIT
metadata:
  author: "shao36058-png"
  version: "0.1.0"
  domain: "Electronics Engineering / 电子工程"
  specialty: "RF and Microwave Engineering / 射频与微波工程"
  component: "RF Bandpass Filters / 射频带通滤波器"
  author-suggested-soc: "17-2072"
---

# HFSS Wideband Bandpass Filter

Identify the filter topology, stack, port reference planes, saved variation and acceptance mask before interpreting a curve. Preserve structure and connectivity when only dimension changes are permitted; names alone do not establish a circuit topology.

## Choose the operation

- For reproduction and dimension optimization, read [references/workflow.md](references/workflow.md). Map the reference to actual dielectric gaps, electrodes, vias, terminals and fixture. Separate original, scaled and modified aspects.
- For result review, read [references/validation.md](references/validation.md). Read actual complex S parameters and native convergence rather than trusting a solved window or a solution list.
- Process curves with [scripts/filter_metrics.py](scripts/filter_metrics.py). It accepts complete complex two-port CSV and explicitly selects absolute or peak-relative bandwidth.
- Export with [scripts/export_saved_filter.py](scripts/export_saved_filter.py) from one explicitly identified existing session, project, design, solution and port order.

## Engineering decisions

Record whether bandwidth means absolute S21 >= -3 dB, a 3 dB drop from the main-passband peak, or a combined loss/matching mask. Report both edges and the definition. Select the connected interval containing the intended center, not a spurious remote lobe. An unbracketed edge is unknown, not the sweep endpoint.

Keep arithmetic center (fL+fH)/2, geometric center sqrt(fL*fH), and response peak distinct. A 1200 MHz nominal center with 600 MHz total width suggests 900–1500 MHz under an arithmetic-center convention; do not assume symmetry or an unspecified tolerance. A 50% fractional bandwidth needs full-wave validation of preliminary narrowband models.

Driven Terminal uses St(out,in) and actual terminal names; Driven Modal needs its actual modal expressions. Terminal names, physical port numbers and mode indices are not interchangeable. Record reference impedance, ground connection, renormalization and de-embedding.

Separate insertion loss, input/output return loss, ripple, group delay and stopband rejection. With verified equal real power-wave impedances, |S21|^2 is forward power. Unaccounted power includes dielectric/conductor loss, radiation and unrepresented channels; it does not isolate one loss mechanism. Full-matrix passivity can detect gain missed by individual columns.

Read material properties and units rather than trusting variable names: an er-prefixed parameter may be a length. Ceramic loss, fired metal conductivity, conductor thickness and the PCB launch all matter. Air/PEC waveguide settings do not constitute a filter model.

For wide bands, assess mesh and samples at edges and relevant stopband features. Display points are not independent solves. Wrapper defaults may disagree with saved/native sweep definitions; retain authoritative evidence or mark the type unknown. CSV processing alone cannot certify convergence or normalization.

Skill creation and saved-result inspection do not start a solve. For authorized computation, use one identified AEDT instance, check running jobs and physical/commit memory headroom, preserve results, and evaluate dimension candidates against actual HFSS feedback. Do not open a second process on the same project or bypass a live semaphore.

## Deliverables

State model scope, frequency coverage, bandwidth definition, curve estimates, convergence and remaining acceptance gaps. Keep source projects, PDFs and local case data out of public skill releases unless publication of those artifacts is explicitly requested.
