#!/usr/bin/env python3

from argparse import ArgumentParser, RawTextHelpFormatter
from firedrake import *

parser = ArgumentParser(description="""
Use Firedrake's nonlinear solver for the Poisson problem
  -Laplace(u) = f        in the unit square
            u = g        on the boundary
Compare c/ch6/fish.c.  The PETSc solver prefix is 's_'.""",
                    formatter_class=RawTextHelpFormatter)
parser.add_argument('-mx', type=int, default=3, metavar='MX',
                    help='number of mesh points in x-direction')
parser.add_argument('-my', type=int, default=3, metavar='MY',
                    help='number of mesh points in y-direction')
parser.add_argument('-o', metavar='NAME', type=str, default='',
                    help='output file name ending with .pvd')
parser.add_argument('-order', type=int, default=1, metavar='X',
                    help='polynomial degree for elements')
parser.add_argument('-quad', action='store_true', default=False,
                    help='use quadrilateral finite elements')
parser.add_argument('-refine', type=int, default=-1, metavar='X',
                    help='number of refinement levels (e.g. for GMG)')
args, unknown = parser.parse_known_args()

# Create mesh, enabling geometric multigrid using heirarchy
mx, my = args.mx, args.my
mesh = UnitSquareMesh(mx-1, my-1, quadrilateral=args.quad)
if args.refine > 0:
    hierarchy = MeshHierarchy(mesh, args.refine)
    mesh = hierarchy[-1]     # i.e. the fine mesh
    mx, my = (mx-1) * 2**args.refine + 1, (my-1) * 2**args.refine + 1
x,y = SpatialCoordinate(mesh)

# Define function space, right-hand side, and weak form.
W = FunctionSpace(mesh, 'Lagrange', degree=args.order)
f_rhs = Function(W).interpolate(x * exp(y))  # manufactured
u = Function(W)  # initialized to zero
v = TestFunction(W)
F = (dot(grad(u), grad(v)) - f_rhs * v) * dx

# Call solver, including boundary conditions
g_bdry = Function(W).interpolate(- x * exp(y))  # = exact solution
bdry_ids = (1, 2, 3, 4)   # all four sides of boundary
bc = DirichletBC(W, g_bdry, bdry_ids)
solve(F == 0, u, bcs = [bc], options_prefix = 's',
      solver_parameters = {'snes_type': 'ksponly',
                           'ksp_type': 'cg'})

# Compute error in L_infty and L_2 norm
elementstr = '%s^%d' % (['P','Q'][args.quad],args.order)
u_exact = g_bdry
error_Linf = max(abs(u.vector().array() - u_exact.vector().array()))
error_L2 = sqrt(assemble(dot(u - u_exact, u - u_exact) * dx))
print('done on %d x %d grid with %s elements:' % (mx,my,elementstr))
print('  error |u-uexact|_inf = %.3e, |u-uexact|_h = %.3e' \
      % (error_Linf,error_L2))

# Optionally save to a .pvd file viewable with Paraview
if len(args.o) > 0:
    print('saving solution to %s ...' % args.o)
    u.rename('u')
    File(args.o).write(u)
