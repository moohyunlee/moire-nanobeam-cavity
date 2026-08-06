import meep as mp
from meep import mpb


def main():
    '''
    Aim to have wavelength: 930nm
    A:B = 13:14
    GaAs: epsilon=13
    ABA
    '''
    Lx = 13.0
    Ly = 5.0
    aB_over_aA = 13 / 14
    beam_width = 3.4
    row_spacing = 1.0
    hole_radius = 0.31
    resolution=48
    num_bands = 120
    epsilon_gaas = 13.0
    gaas = mp.Medium(epsilon=epsilon_gaas)

    #geometry
    geometry_lattice = mp.Lattice(
            size=mp.Vector3(Lx, Ly))

    geometry = [
            mp.Block(
                size=mp.Vector3(mp.inf, beam_width, mp.inf),
                material=gaas
                )]

    for n in range(13):
            x = (n - 6) * 1.0

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

    for m in range(14):
            x = (m - 6.5) * aB_over_aA

            geometry.append(
                mp.Cylinder(
                    radius=hole_radius,
                    center=mp.Vector3(x, 0),
                    material=mp.air,
                    )
                )

    #Brillouin zone
    gamma = mp.Vector3(0, 0)
    zone_edge = mp.Vector3(0.5, 0)

    set_k_points = mp.interpolate(
            40,
            [gamma, zone_edge]
            )

    #Solver
    ms = mpb.ModeSolver(
            num_bands=num_bands,
            resolution=resolution,
            geometry_lattice=geometry_lattice,
            geometry=geometry,
            default_material=mp.air,
            k_points=set_k_points,
            )

    ms.run_te()

if __name__=="__main__":
    main()

