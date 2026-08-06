import meep as mp
from meep import mpb


def main():
    '''
    Aim to have wavelength: 930nm
    A:B = 13:14
    GaAs: epsilon=13
    AAA vertically 
    '''
    beam_width = 3.4
    row_spacing = 1.0
    hole_radius = 0.31
    resolution=32
    num_bands = 8
    epsilon_gaas = 13.0
    gaas = mp.Medium(epsilon=epsilon_gaas)
    supercell_y = 5.0

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