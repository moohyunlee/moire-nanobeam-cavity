import meep as mp


def main():
    '''
    Normalized A as 1
    '''
    resolution = 32
    eps = 13.0
    beam_width = 3.4
    row_spacing = 1.0
    hole_radius = 0.31
    aB_over_aA = 13 / 14
    L_moire = 13.0
    structure_length = L_moire
    dpml = 1.0
    x_pad = 2.0
    y_pad = 2.0
    sx = structure_length + 2 * x_pad + 2 * dpml
    sy = beam_width + 2 * y_pad + 2 * dpml

    cell = mp.Vector3(sx, sy, 0)
    gaas = mp.Medium(epsilon=eps)
    
    #Geometry
    geometry = [
            mp.Block(
                size=mp.Vector3(mp.inf, beam_width, mp.inf),
                center=mp.Vector3(0, 0),
                material=gaas,
                )
            ]

    #finite repeated 13A-14B moire cells
    cell_shift = 0.0
    
    #moire A upper and lower
    for n in range(13):
        x = cell_shift + (n - 6) * 1.0

        geometry.append(
                mp.Cylinder(
                    radius=hole_radius,
                    center=mp.Vector3(x, row_spacing),
                    material=mp.air,
                    )
                )

        geometry.append(
                mp.Cylinder(
                    radius=hole_radius,
                    center=mp.Vector3(x, -row_spacing),
                    material=mp.air,
                    )
                )

    #moire B center
    for m in range(14):
        x = cell_shift + (m - 6.5) * aB_over_aA

        geometry.append(
                mp.Cylinder(
                    radius=hole_radius,
                    center=mp.Vector3(x, 0),
                    material=mp.air,
                    )
                )
    
    #PML
    pml_layers = [mp.PML(dpml)]

    # Source
    # MPB candidates:
    #   Band 93: f ~ 0.289
    fcen = 0.2845
    df = 0.004

    #Source
    source_point = mp.Vector3(0.0, 0.3)
    sources = [
            mp.Source(
                src=mp.GaussianSource(
                    frequency=fcen,
                    fwidth=df,
                    ),
                component=mp.Ey,
                center=source_point,
                )
            ]

    #Simulation
    sim = mp.Simulation(
            cell_size=cell,
            geometry=geometry,
            boundary_layers=pml_layers,
            sources=sources,
            resolution=resolution,
            dimensions=2,
            )

    #harminv
    harminv_point = source_point
    h = mp.Harminv(
            mp.Hz,
            harminv_point,
            fcen,
            df,
            )

    #Run
    sim.run(
            mp.at_beginning(mp.output_epsilon),
            mp.after_sources(h),
            mp.at_end(mp.output_hfield_z),
            mp.at_end(mp.output_efield_y),
            until_after_sources=800,
            )

if __name__ == "__main__":
    main()
