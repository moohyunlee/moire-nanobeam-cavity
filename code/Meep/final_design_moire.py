#!/usr/bin/env python3

import csv
import math
import time
from pathlib import Path

import h5py
import meep as mp
import numpy as np


# Fixed final design
RESOLUTION = 52
RUNTIME_AFTER_SOURCES = 6000.0
CENTRAL_B_OFFSET = 0.300
RIGHT_CENTER_TRANSITION_RADIUS = 0.298571

LABEL = "M19_final_offset_p0p300000_r_p0p298571_res52"
OUTPUT_DIR = Path("final_M19_res52")

EPS_GAAS = 13.0
GAAS_THRESHOLD = 0.5 * EPS_GAAS
BEAM_WIDTH = 3.4
ROW_SPACING = 1.0
HOLE_RADIUS = 0.31

A_A = 1.0
A_B = 13.0 / 14.0
L_MOIRE = 13.0
MIRROR_PERIODS = 19

DPML = 2.5
X_PAD = 2.0
Y_PAD = 3.0
MIRROR_RADIUS = HOLE_RADIUS * 1.04
TRANSITION_RADIUS = HOLE_RADIUS * 1.095
INTERFACE_SHIFT = 0.5

FCEN = 0.2857
DF = 0.0100
FREQUENCY_MIN = 0.2800
FREQUENCY_MAX = 0.2910
TARGET_FREQUENCY = 0.2857
MAX_HARMINV_ERROR = 1.0e-3

SOURCE_POINT = mp.Vector3(0.0, 0.3)
FIELD_AVERAGE_SPAN = 20.0
FIELD_SAMPLE_INTERVAL = 1.0

RESULT_COLUMNS = [
    "label",
    "status",
    "message",
    "control_type",
    "sweep_name",
    "sweep_value",
    "resolution",
    "runtime_after_sources",
    "central_B_offset",
    "right_center_transition_radius",
    "left_center_transition_radius",
    "nearest_interface_gap",
    "frequency",
    "Q",
    "decay",
    "amplitude",
    "harminv_error",
    "harminv_monitor",
    "Ey_frequency",
    "Ey_Q",
    "Hz_frequency",
    "Hz_Q",
    "A_eff_y_2D_over_aA2",
    "Q_over_A_eff_y",
    "C_moire",
    "peak_x_a",
    "peak_y_a",
    "effective_x_length_a",
    "x_width_90_a",
    "field_samples",
    "runtime_minutes",
    "field_h5",
]


def nearest_interface_gap():
    right_gap = (
        A_B
        - CENTRAL_B_OFFSET
        - HOLE_RADIUS
        - RIGHT_CENTER_TRANSITION_RADIUS
    )
    left_gap = A_B + CENTRAL_B_OFFSET - HOLE_RADIUS - TRANSITION_RADIUS
    return min(left_gap, right_gap)


def build_geometry():
    gaas = mp.Medium(epsilon=EPS_GAAS)
    geometry = [
        mp.Block(
            size=mp.Vector3(mp.inf, BEAM_WIDTH, mp.inf),
            center=mp.Vector3(),
            material=gaas,
        )
    ]

    # Central A rows
    for n in range(13):
        x = (n - 6) * A_A
        for y in (+ROW_SPACING, -ROW_SPACING):
            geometry.append(
                mp.Cylinder(
                    radius=HOLE_RADIUS,
                    center=mp.Vector3(x, y),
                    material=mp.air,
                )
            )

    # Central B row
    for m in range(14):
        x = (m - 6.5) * A_B + CENTRAL_B_OFFSET
        geometry.append(
            mp.Cylinder(
                radius=HOLE_RADIUS,
                center=mp.Vector3(x, 0.0),
                material=mp.air,
            )
        )

    # BBB mirrors
    for j in range(MIRROR_PERIODS):
        radius = TRANSITION_RADIUS if j == 0 else MIRROR_RADIUS
        left_x = -L_MOIRE / 2 - (j + INTERFACE_SHIFT) * A_B
        right_x = +L_MOIRE / 2 + (j + INTERFACE_SHIFT) * A_B

        for y in (+ROW_SPACING, 0.0, -ROW_SPACING):
            right_radius = (
                RIGHT_CENTER_TRANSITION_RADIUS
                if j == 0 and abs(y) < 1.0e-12
                else radius
            )
            geometry.append(
                mp.Cylinder(
                    radius=radius,
                    center=mp.Vector3(left_x, y),
                    material=mp.air,
                )
            )
            geometry.append(
                mp.Cylinder(
                    radius=right_radius,
                    center=mp.Vector3(right_x, y),
                    material=mp.air,
                )
            )

    return geometry


def create_simulation():
    mirror_length = MIRROR_PERIODS * A_B
    structure_length = L_MOIRE + 2 * mirror_length
    cell_size = mp.Vector3(
        structure_length + 2 * X_PAD + 2 * DPML,
        BEAM_WIDTH + 2 * Y_PAD + 2 * DPML,
        0,
    )
    sources = [
        mp.Source(
            src=mp.GaussianSource(frequency=FCEN, fwidth=DF),
            component=mp.Ey,
            center=SOURCE_POINT,
        )
    ]
    simulation = mp.Simulation(
        cell_size=cell_size,
        geometry=build_geometry(),
        boundary_layers=[mp.PML(DPML)],
        sources=sources,
        resolution=RESOLUTION,
        dimensions=2,
        filename_prefix=LABEL,
    )
    return simulation, cell_size, structure_length


class FieldAccumulator:
    def __init__(self, cell_size):
        self.cell_size = cell_size
        self.source_end_time = None
        self.sum_ex2 = None
        self.sum_ey2 = None
        self.sum_hz2 = None
        self.count = 0

    def mark_source_end(self, simulation):
        if self.source_end_time is None:
            self.source_end_time = float(simulation.meep_time())
            start = self.source_end_time + RUNTIME_AFTER_SOURCES - FIELD_AVERAGE_SPAN
            print(f"source_end={self.source_end_time:.6f}; field_average_start={start:.6f}")

    def sample(self, simulation):
        if self.source_end_time is None:
            return

        start = self.source_end_time + RUNTIME_AFTER_SOURCES - FIELD_AVERAGE_SPAN
        if simulation.meep_time() + 1.0e-9 < start:
            return

        fields = {
            name: np.asarray(
                simulation.get_array(
                    center=mp.Vector3(),
                    size=self.cell_size,
                    component=component,
                    cmplx=False,
                ),
                dtype=float,
            )
            for name, component in (("ex", mp.Ex), ("ey", mp.Ey), ("hz", mp.Hz))
        }
        if self.sum_ex2 is None:
            self.sum_ex2 = np.zeros_like(fields["ex"])
            self.sum_ey2 = np.zeros_like(fields["ey"])
            self.sum_hz2 = np.zeros_like(fields["hz"])

        self.sum_ex2 += fields["ex"] ** 2
        self.sum_ey2 += fields["ey"] ** 2
        self.sum_hz2 += fields["hz"] ** 2
        self.count += 1

    def rms(self):
        if self.count == 0:
            raise RuntimeError("No final-window field samples were collected.")
        return (
            np.sqrt(self.sum_ex2 / self.count),
            np.sqrt(self.sum_ey2 / self.count),
            np.sqrt(self.sum_hz2 / self.count),
        )


def valid_modes(modes):
    valid = []
    for mode in modes:
        values = (mode.freq, mode.Q, mode.decay, abs(mode.amp), abs(mode.err))
        if not all(math.isfinite(float(value)) for value in values):
            continue
        if mode.Q <= 0 or mode.decay >= 0:
            continue
        if FREQUENCY_MIN <= mode.freq <= FREQUENCY_MAX:
            valid.append(mode)
    return valid


def nearest_mode(modes):
    modes = valid_modes(modes)
    trusted = [mode for mode in modes if abs(mode.err) <= MAX_HARMINV_ERROR]
    if not modes:
        return None
    return min(
        trusted or modes,
        key=lambda mode: (
            abs(mode.freq - TARGET_FREQUENCY),
            abs(mode.err),
            -mode.Q,
        ),
    )


def select_mode(ey_modes, hz_modes):
    candidates = []
    for component, modes in (("Ey", ey_modes), ("Hz", hz_modes)):
        for mode in valid_modes(modes):
            candidates.append((component, mode, abs(mode.err) <= MAX_HARMINV_ERROR))

    if not candidates:
        return None, None
    if any(trusted for _, _, trusted in candidates):
        candidates = [item for item in candidates if item[2]]

    component, mode, _ = min(
        candidates,
        key=lambda item: (
            abs(item[1].freq - TARGET_FREQUENCY),
            abs(item[1].err),
            -abs(item[1].amp),
            -item[1].Q,
        ),
    )
    return component, mode


def weighted_quantile(values, weights, q):
    values = np.asarray(values, dtype=float).ravel()
    weights = np.asarray(weights, dtype=float).ravel()
    valid = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    values = values[valid]
    weights = weights[valid]
    if values.size == 0:
        return float("nan")

    order = np.argsort(values)
    values = values[order]
    weights = weights[order]
    return float(
        np.interp(
            np.clip(q, 0.0, 1.0) * np.sum(weights),
            np.cumsum(weights),
            values,
        )
    )


def calculate_metrics(epsilon, ey_rms, x, y, weights):
    energy = epsilon * ey_rms**2
    gaas_energy = np.where(epsilon > GAAS_THRESHOLD, energy, 0.0)
    total_energy = float(np.sum(weights * energy))
    total_gaas = float(np.sum(weights * gaas_energy))
    peak_gaas = float(np.max(gaas_energy))
    if total_energy <= 0 or total_gaas <= 0 or peak_gaas <= 0:
        raise RuntimeError("Invalid Ey energy distribution.")

    central = np.broadcast_to((np.abs(x) <= L_MOIRE / 2)[:, None], energy.shape)
    central_gaas = float(np.sum(weights * np.where(central, gaas_energy, 0.0)))
    peak_index = np.unravel_index(int(np.argmax(gaas_energy)), gaas_energy.shape)
    ux = np.sum(weights * gaas_energy, axis=1)
    ux_total = float(np.sum(ux))
    ux_peak = float(np.max(ux))

    return {
        "A_eff_y_2D_over_aA2": total_energy / peak_gaas,
        "C_moire": central_gaas / total_gaas,
        "peak_x_a": float(x[peak_index[0]]),
        "peak_y_a": float(y[peak_index[1]]),
        "effective_x_length_a": ux_total / ux_peak if ux_peak > 0 else float("nan"),
        "x_width_90_a": weighted_quantile(x, ux, 0.95) - weighted_quantile(x, ux, 0.05),
    }


def save_fields(path, x, y, weights, epsilon, ex_rms, ey_rms, hz_rms, component, mode, structure_length, sample_count, metrics):
    path.parent.mkdir(parents=True, exist_ok=True)
    with h5py.File(path, "w") as h5:
        h5.create_dataset("x", data=x)
        h5.create_dataset("y", data=y)
        h5.create_dataset("weights", data=weights)
        h5.create_dataset("epsilon", data=epsilon)
        h5.create_dataset("ex", data=ex_rms)
        h5.create_dataset("ey", data=ey_rms)
        h5.create_dataset("hz", data=hz_rms)

        h5.attrs["label"] = LABEL
        h5.attrs["resolution"] = RESOLUTION
        h5.attrs["runtime_after_sources"] = RUNTIME_AFTER_SOURCES
        h5.attrs["central_B_offset"] = CENTRAL_B_OFFSET
        h5.attrs["right_center_transition_radius"] = RIGHT_CENTER_TRANSITION_RADIUS
        h5.attrs["control_type"] = "final_fixed_design"
        h5.attrs["sweep_name"] = "fixed_design"
        h5.attrs["sweep_value"] = 0.0
        h5.attrs["save_fields"] = True
        h5.attrs["frequency"] = float(mode.freq)
        h5.attrs["Q"] = float(mode.Q)
        h5.attrs["decay"] = float(mode.decay)
        h5.attrs["amplitude"] = float(abs(mode.amp))
        h5.attrs["harminv_error"] = float(abs(mode.err))
        h5.attrs["harminv_monitor"] = component
        h5.attrs["a_A"] = A_A
        h5.attrs["a_B"] = A_B
        h5.attrs["L_moire"] = L_MOIRE
        h5.attrs["structure_length"] = structure_length
        h5.attrs["beam_width"] = BEAM_WIDTH
        h5.attrs["field_representation"] = "sqrt(time-average(real field squared))"
        h5.attrs["field_average_span"] = FIELD_AVERAGE_SPAN
        h5.attrs["field_sample_interval"] = FIELD_SAMPLE_INTERVAL
        h5.attrs["field_sample_count"] = sample_count
        h5.attrs["nearest_interface_gap"] = nearest_interface_gap()
        for key, value in metrics.items():
            h5.attrs[key] = value


def result_template(status, message):
    result = {key: "" for key in RESULT_COLUMNS}
    result.update(
        {
            "label": LABEL,
            "status": status,
            "message": message,
            "control_type": "final_fixed_design",
            "sweep_name": "fixed_design",
            "sweep_value": 0.0,
            "resolution": RESOLUTION,
            "runtime_after_sources": RUNTIME_AFTER_SOURCES,
            "central_B_offset": CENTRAL_B_OFFSET,
            "right_center_transition_radius": RIGHT_CENTER_TRANSITION_RADIUS,
            "left_center_transition_radius": "",
            "nearest_interface_gap": nearest_interface_gap(),
        }
    )
    return result


def write_result(result):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / "final_results.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESULT_COLUMNS)
        writer.writeheader()
        writer.writerow(result)
    print(f"Saved: {path}")


def run_final_design():
    print("\n" + "=" * 72)
    print(f"Running {LABEL}")
    print(
        f"resolution={RESOLUTION}, runtime={RUNTIME_AFTER_SOURCES:.0f}, "
        f"offset={CENTRAL_B_OFFSET:+.6f}, gap={nearest_interface_gap():+.6f}"
    )
    print("=" * 72)

    simulation = None
    started = time.perf_counter()
    try:
        simulation, cell_size, structure_length = create_simulation()
        ey_harminv = mp.Harminv(mp.Ey, SOURCE_POINT, FCEN, DF)
        hz_harminv = mp.Harminv(mp.Hz, SOURCE_POINT, FCEN, DF)
        accumulator = FieldAccumulator(cell_size)

        simulation.run(
            mp.after_sources(accumulator.mark_source_end),
            mp.after_sources(ey_harminv),
            mp.after_sources(hz_harminv),
            mp.at_every(FIELD_SAMPLE_INTERVAL, accumulator.sample),
            until_after_sources=RUNTIME_AFTER_SOURCES,
        )

        component, mode = select_mode(ey_harminv.modes, hz_harminv.modes)
        if mode is None:
            raise RuntimeError(
                f"No valid tracked mode in [{FREQUENCY_MIN}, {FREQUENCY_MAX}]."
            )

        ey_mode = nearest_mode(ey_harminv.modes)
        hz_mode = nearest_mode(hz_harminv.modes)
        ex_rms, ey_rms, hz_rms = accumulator.rms()
        epsilon = np.asarray(
            simulation.get_array(
                center=mp.Vector3(), size=cell_size, component=mp.Dielectric
            ),
            dtype=float,
        )
        x, y, _, weights = simulation.get_array_metadata(
            center=mp.Vector3(), size=cell_size
        )
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
        weights = np.asarray(weights, dtype=float)

        expected_shape = (len(x), len(y))
        for name, array in {
            "weights": weights,
            "epsilon": epsilon,
            "ex": ex_rms,
            "ey": ey_rms,
            "hz": hz_rms,
        }.items():
            if array.shape != expected_shape:
                raise RuntimeError(f"{name} shape {array.shape} != {expected_shape}")

        metrics = calculate_metrics(epsilon, ey_rms, x, y, weights)
        field_path = OUTPUT_DIR / "fields" / f"{LABEL}.h5"
        save_fields(
            field_path,
            x,
            y,
            weights,
            epsilon,
            ex_rms,
            ey_rms,
            hz_rms,
            component,
            mode,
            structure_length,
            accumulator.count,
            metrics,
        )

        result = result_template("ok", "")
        result.update(
            {
                "frequency": float(mode.freq),
                "Q": float(mode.Q),
                "decay": float(mode.decay),
                "amplitude": float(abs(mode.amp)),
                "harminv_error": float(abs(mode.err)),
                "harminv_monitor": component,
                "Ey_frequency": float(ey_mode.freq) if ey_mode else math.nan,
                "Ey_Q": float(ey_mode.Q) if ey_mode else math.nan,
                "Hz_frequency": float(hz_mode.freq) if hz_mode else math.nan,
                "Hz_Q": float(hz_mode.Q) if hz_mode else math.nan,
                **metrics,
                "Q_over_A_eff_y": float(mode.Q) / metrics["A_eff_y_2D_over_aA2"],
                "field_samples": accumulator.count,
                "runtime_minutes": (time.perf_counter() - started) / 60.0,
                "field_h5": str(field_path),
            }
        )
        print("\nSelected result")
        for key in ("harminv_monitor", "frequency", "Q", "A_eff_y_2D_over_aA2", "Q_over_A_eff_y", "C_moire"):
            print(f"{key:30s} = {result[key]}")
    except Exception as error:
        result = result_template("failed", f"{type(error).__name__}: {error}")
        print(f"[FAILED] {result['message']}")
    finally:
        if simulation is not None:
            simulation.reset_meep()

    write_result(result)
    return result


if __name__ == "__main__":
    run_final_design()
