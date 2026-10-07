# Saved-data audit

Read actual complex data for the current project/design/parameter variation. A solved window, setup name or report is insufficient. Keep native solutions, imported tables and regenerated reports distinct. Record native convergence, ports/normalization, sweep type, sampling and materials.

Single-frequency adaptive convergence does not prove broadband mesh convergence. Displayed sweep points are not independent solves unless the sweep is discrete. Wrapper defaults can disagree with saved/native sweep definitions; record authoritative evidence or mark the type unknown. Threshold interpolation is an estimate, not a solved frequency. Check passband edges, ripple, narrow notches and specified stopbands with adequate samples.

## CSV format

```text
frequency_MHz,S11_real,S11_imag,S21_real,S21_imag,S12_real,S12_imag,S22_real,S22_imag
```

All nine columns are required; extra columns are ignored. Values must be finite and frequencies positive, strictly increasing and distinct. At least three rows are needed. Missing matrix entries must not be assumed zero. Assign port directions physically before mapping S11/S21/S12/S22.

```bash
python scripts/filter_metrics.py data.csv --center-mhz 1200 --reference absolute --drop-db 3 --target-bandwidth-mhz 600 --output metrics.json
python scripts/filter_metrics.py data.csv --center-mhz 1200 --reference peak --drop-db 3
```

Absolute reference uses a fixed -drop_db S21 threshold. Peak reference finds the response lobe around the requested center, bounded by local response minima, and subtracts drop_db from that lobe's peak. It avoids a remote spurious peak. Inspect the chosen peak if a multi-peak intentional passband makes that lobe selection unsuitable.

The connected threshold interval must contain the requested center. Never substitute an unrelated broad passband. An edge beyond the sampled grid is null and the width is unknown. Crossings use linear interpolation in S21 dB. Report arithmetic/geometric centers and their fractional-bandwidth conventions separately. A target bandwidth also produces sampled metrics on center +/- bandwidth/2.

Insertion loss is -20log10(|S21|); return loss uses S11 or S22 similarly. Ripple is the S21 dB spread. Displayed dB is capped at -300 for zero magnitude; raw input remains unchanged. Group delay uses unwrapped S21 phase with one-sided endpoints and centered differences inside the selected interval. It is a sampled estimate: sparse points, zeros and phase aliasing can invalidate it. A large principal phase increment is flagged, but small increments do not prove no missing phase turns.

With verified equal real power-wave reference impedances, the helper reports unaccounted incident-column power, reciprocity error and the largest singular value of the full matrix. Sigma >1 indicates apparent gain for some coherent excitation; investigate numerical error and normalization. Unaccounted power includes radiation and all losses, not exclusively conductor dissipation.

Exit 0 means processing completed, not that a device passed. CSV cannot establish convergence or port normalization. Bandwidth deviation is not pass/fail without a user-defined tolerance. No loss, matching or rejection limits are invented.

## Existing-session export

```bash
python scripts/export_saved_filter.py --pid AEDT_PID --port GRPC_PORT --version AEDT_VERSION --project PROJECT_NAME --design DESIGN_NAME --solution 'Setup1 : Sweep' --input INPUT_TERMINAL --output OUTPUT_TERMINAL --out NEW_EMPTY_FOLDER
```

Requires PyAEDT and psutil. Validate PID/listener and the already active project/design; refuse a running solve. Export current nominal variation, all four complex two-port parameters, parameter/port provenance, and native convergence when available. It does not start a session, open/close projects, solve, save, edit sources or change geometry. Release only the scripting connection.

Supports single-ended HFSS Modal and Terminal two-port designs. Additional excitations, differential/mixed-mode matrices and complex-reference interpretations need an appropriate extension. The metadata contains local paths and dimensions and is private by default. Preserve actual saved/native sweep definitions alongside wrapper properties so discrepancies remain visible.
