"""Read a single existing HFSS two-port session. Never solve or save a project."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pid', type=int, required=True)
    parser.add_argument('--port', type=int, required=True, help='Existing AEDT gRPC listener')
    parser.add_argument('--version', required=True)
    parser.add_argument('--project', required=True)
    parser.add_argument('--design', required=True)
    parser.add_argument('--solution', required=True)
    parser.add_argument('--input', required=True, help='Exact input excitation/terminal name')
    parser.add_argument('--output', required=True, help='Exact output excitation/terminal name')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    desktop = None
    try:
        if args.pid <= 0 or not 1 <= args.port <= 65535:
            raise ValueError('Invalid PID or listener port.')
        if args.input == args.output:
            raise ValueError('Input and output must be different excitations.')
        if ' : ' not in args.solution or args.solution.endswith(' : Table'):
            raise ValueError('Choose an existing native Setup : Sweep, not an imported Table.')
        if args.out.exists() and (not args.out.is_dir() or any(args.out.iterdir())):
            raise ValueError('Output folder must be absent or empty.')
        import psutil
        process = psutil.Process(args.pid)
        if process.name().lower() != 'ansysedt.exe':
            raise ValueError('PID does not identify AEDT.')
        listeners = [c.laddr.port for c in process.net_connections(kind='tcp') if c.status == psutil.CONN_LISTEN]
        if args.port not in listeners:
            raise ValueError('The requested listener is not owned by this AEDT PID.')
        from ansys.aedt.core import Desktop, Hfss
        desktop = Desktop(version=args.version, port=args.port, aedt_process_id=args.pid,
                          new_desktop=False, close_on_exit=False)
        if desktop.aedt_process_id != args.pid:
            raise RuntimeError('Attachment selected a different AEDT process.')
        project = desktop.odesktop.GetActiveProject()
        if not project or project.GetName() != args.project:
            raise ValueError('Select the requested project in HFSS first; exporter will not switch or open it.')
        design = project.GetActiveDesign()
        if not design or design.GetName() != args.design:
            raise ValueError('Select the requested design in HFSS first.')
        if desktop.odesktop.AreThereSimulationsRunning():
            raise RuntimeError('A simulation is running; leave the session untouched.')
        h = Hfss(project=args.project, design=args.design, version=args.version,
                 aedt_process_id=args.pid, new_desktop=False, close_on_exit=False)
        if h.solution_type not in ('Modal', 'Terminal'):
            raise ValueError('Only HFSS Modal and Terminal network solutions are supported.')
        excitations = list(h.excitation_names)
        if len(excitations) != 2 or set(excitations) != {args.input, args.output}:
            raise ValueError('Export requires exactly the two specified excitations; no implicit mode reduction.')
        if args.solution not in h.existing_analysis_sweeps:
            raise ValueError('The selected native solution is not available.')
        symbol = 'St' if h.solution_type == 'Terminal' else 'S'
        expressions = {
            'S11': f'{symbol}({args.input},{args.input})',
            'S21': f'{symbol}({args.output},{args.input})',
            'S12': f'{symbol}({args.input},{args.output})',
            'S22': f'{symbol}({args.output},{args.output})',
        }
        variations = dict(h.available_variations.nominal_values)
        variations['Freq'] = ['All']
        category = 'Terminal Solution Data' if h.solution_type == 'Terminal' else 'Modal Solution Data'
        data = h.post.get_solution_data(expressions=list(expressions.values()),
                                       setup_sweep_name=args.solution, variations=variations,
                                       primary_sweep_variable='Freq', report_category=category)
        if not data or len(data.variations) != 1:
            raise RuntimeError('No unique actual saved data for the current nominal variation.')
        unit = data.units_sweeps.get('Freq')
        factors = {'Hz': 1e-6, 'kHz': .001, 'MHz': 1, 'GHz': 1000, 'THz': 1e6}
        if unit not in factors:
            raise ValueError(f'Unsupported frequency unit {unit!r}.')
        frequencies = [float(f)*factors[unit] for f in data.primary_sweep_values]
        if not frequencies or not all(math.isfinite(f) and f > 0 for f in frequencies):
            raise ValueError('Invalid saved frequency axis.')
        if any(b <= a for a,b in zip(frequencies,frequencies[1:])):
            raise ValueError('Saved frequency axis must be strictly increasing.')
        matrix = {}
        for name, expression in expressions.items():
            real = list(data.get_expression_data(expression,'real')[1])
            imag = list(data.get_expression_data(expression,'imag')[1])
            if len(real) != len(frequencies) or len(imag) != len(frequencies):
                raise ValueError('Saved matrix arrays are incomplete.')
            if not all(math.isfinite(float(v)) for v in real+imag):
                raise ValueError('Nonfinite saved S parameters.')
            matrix[name] = {'real':real,'imag':imag}
        project_file = Path(h.project_file)
        metadata = {
            'project':args.project, 'design':args.design, 'project_file':str(project_file),
            'project_sha256':hashlib.sha256(project_file.read_bytes()).hexdigest(),
            'pid':args.pid, 'port':args.port, 'version':args.version, 'solution':args.solution,
            'solution_type':h.solution_type, 'input':args.input, 'output':args.output,
            'expressions':expressions, 'nominal_variables':dict(h.available_variations.nominal_values),
            'saved_variations':data.variations, 'samples':len(frequencies), 'frequency_unit':'MHz',
            'port_and_boundary_properties':[{'name':b.name,'type':b.type,'props':dict(b.props)} for b in h.boundaries],
            'power_wave_normalization_verified':False,
            'setup_and_sweep_evidence':[], 'solver_was_started':False,
        }
        for setup in h.setups:
            metadata['setup_and_sweep_evidence'].append({'name':setup.name,'saved_setup_props':dict(setup.props),
                'wrapper_sweep_props':[{'name':s.name,'props':dict(s.props)} for s in setup.sweeps]})
        args.out.mkdir(parents=True,exist_ok=True)
        columns=['frequency_MHz']+[f'{s}_{p}' for s in expressions for p in ('real','imag')]
        with (args.out/'s_parameters.csv').open('w',encoding='utf-8',newline='') as file:
            writer=csv.DictWriter(file,fieldnames=columns)
            writer.writeheader()
            for index, frequency in enumerate(frequencies):
                row={'frequency_MHz':frequency}
                row.update({f'{s}_{p}':matrix[s][p][index] for s in expressions for p in ('real','imag')})
                writer.writerow(row)
        setup_name = args.solution.split(' : ',1)[0]
        try:
            convergence = h.export_convergence(setup_name, output_file=str((args.out/'convergence.txt').resolve()))
            metadata['native_convergence_exported'] = bool(convergence) and (args.out/'convergence.txt').exists()
        except Exception as exc:
            metadata['native_convergence_exported'] = False
            metadata['convergence_export_error'] = str(exc)
        (args.out/'provenance.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
        print(json.dumps({'success':True,'samples':len(frequencies),'solution':args.solution,'out':str(args.out)},ensure_ascii=True))
    except Exception as exc:
        parser.exit(2,f'Error: {exc}\n')
    finally:
        if desktop is not None:
            desktop.release_desktop(close_projects=False,close_on_exit=False)


if __name__ == '__main__':
    main()
