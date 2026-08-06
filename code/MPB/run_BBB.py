import meep as mp
from meep import mpb


def main():
    '''
    Aim to have wavelength: 930nm

    BBB parent is computed in a_B-normalized units.
    Since a_B/a_A = 13/14, transverse dimensions are scaled by 14/13.
        A:B = 13:14
        B = A * 13/14 (normalized for A as 1)
    
    GaAs: epsilon=13
    BBB vertically
    '''
    beam_width = 3.66154 #A * 14 / 13
    row_spacing = 1.07692 #A * 14 / 13
    hole_radius = 0.33385 #A * 14 / 13
    resolution=32
    num_bands = 8
    epsilon_gaas = 13.0
    gaas = mp.Medium(epsilon=epsilon_gaas)
    supercell_y = 5.38462 #A * 14 / 13

    #Geometry
    geometry_lattice = mp.Lattice(
            size=mp.Vector3(1, supercell_y))

    geometry = [
            mp.Block(
                size=mp.Vector3(mp.inf, beam_width, mp.inf),
                material=gaas
                ),

            mp.Cylinder(
                radius=hole_radius,
                center=mp.Vector3(0, row_spacing),
                material=mp.air),

            mp.Cylinder(
                radius=hole_radius,
                center=mp.Vector3(0, 0),
                material=mp.air),

            mp.Cylinder(
                radius=hole_radius,
                center=mp.Vector3(0, -row_spacing),
                material=mp.air)
            ]
    
    #Brillouin zone
    gamma = mp.Vector3(0, 0)
    zone_edge = mp.Vector3(0.5, 0)

    set_k_points = mp.interpolate(
            100,
            [gamma, zone_edge]
            )

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
