# Below is an example of a json file that can be submitted to run_case
# 
# base_config = {
#     "base_case":"/home/openfoam/run/pyramid/base_case",
#     "solver":"scalarPisoFoam",
#     "output_root":"/home/openfoam/run/pyramid/one_source_yoffset",
#     "mesh_file":"/home/openfoam/git/crick-cfd/meshes/pyramid_2_6_w500mm_l3000mm_n20_mf4_gsz10mm.msh",
#     "solver":"scalarPisoFoam",
#     "fix_patches":
#     {
#         "leftWall":"wall",
#         "rightWall":"wall",
#         "defaultFaces":"wall",
#         "floor":"empty",
#         "ceiling":"empty"
#     },
#     "base_case_scalar":"S1",
#     "scalar_inlet_config":
#     {
#         "S1":"Y >= 0.2 && Y<0.22",
#     }
# }

import os, sys, re, argparse, json, logging
logging.basicConfig(level=logging.INFO)

log = logging.getLogger("run_case")

def fix_polyMesh_boundary_file(items, case_root = ".", create_backup = True):
    # parse boundary file
    new_lines = []
    state = None
    boundary_file = os.path.join(case_root, "constant", "polyMesh", "boundary")
    with open(boundary_file, "r") as in_file:
        log.info("Reading %s" % (boundary_file))
        for line_no, line in enumerate(in_file):
            for key in items:
                if key in line:
                    state = key
            if "}" in line:
                state = None
            new_lines.append(line if not state else re.sub(r"([A-Z|a-z]+)ype([ ]+)[a-z]+;", "\\1ype\\2%s;" % items[state], line))
            if new_lines[-1] != line:
                log.info("LINE %d (%s)" % (line_no, state))
                log.info("old: %s" % (line),)
                log.info("new: %s" % (new_lines[-1]))
    
    if create_backup:
        os.system("mv {} {}.bak".format(boundary_file, boundary_file))
    with open(boundary_file, "w") as out_file:
        out_file.write("".join(new_lines))
    log.info("Wrote {}.".format(boundary_file))


def configure_scalar_inlet_0(scalar_inlet_config, path_to_scalar):
    # Look at the base case file
    # Modify the code to reflect the configuration
    inlet_header = """
    inlet
    {
 	    type             codedFixedValue;
    	value            uniform 0;
    	redirectType     inletProfile;
   
	code
    	#{
            const fvPatch& boundaryPatch = patch(); 
            const vectorField& Cf = boundaryPatch.Cf();
            scalarField& field = *this; 

            //scalar tmp=1;
 	    forAll(Cf, faceI)
            {
    """

    inlet_footer = """
	    }
   	#};         

  	codeOptions
  	#{

            -I$(LIB_SRC)/finiteVolume/lnInclude \
            -I$(LIB_SRC)/meshTools/lnInclude

   	#};

  	codeInclude
   	#{
      	    #include "fvCFD.H"
      	    #include <cmath>
     	    #include <iostream>
  	#};
    }
    """

    log.info("Determining inlet code.")
    inlet_code = {}
    for scalar, config in scalar_inlet_config.iteritems():
        inlet_main = "field[faceI] = %s ? 1. : 0.;" % (config.replace("X", "Cf[faceI].x()").replace("Y", "Cf[faceI].y()"))
        log.info("%s: %s" % (scalar, inlet_main))
        inlet_code[scalar] = inlet_header + inlet_main + inlet_footer

    # Now read the base case scalar file and figure out all the lines that don't involve the inlet
    log.info("Reading header and footer from %s." % (path_to_scalar))
    header_lines = []
    footer_lines = []
    state = "header"
    n_brace = 0
    with open(path_to_scalar, "r") as in_file:
        for line in in_file:
            if state == "header":
                if "inlet" in line:
                    state = "inlet_start"
                else:
                    header_lines.append(line)
            elif state == "inlet_start":
                if "{" in line:
                    state = "inlet_main"
                    n_brace = n_brace + line.count("{") - line.count("}")
            elif state == "inlet_main":
                if "{" in line:
                    n_brace += line.count("{")
                if "}" in line:
                    n_brace -= line.count("}")
                if n_brace == 0:
                    state = "footer"
            elif state == "footer":
                footer_lines.append(line)
    
    # Now create one file for each scalar and replace the inlet code with what we created above
    scalar_output_root = os.path.dirname(path_to_scalar)
    log.info("Writing scalars to %s." % (scalar_output_root))
    for scalar, code in inlet_code.iteritems():
        output_file = os.path.join(scalar_output_root, scalar)
        log.info("Writing %s to %s." % (scalar, output_file))
        with open(output_file, "w") as f:
            f.write("".join(header_lines))
            f.write(code)
            f.write("".join(footer_lines))


def safe_exec(cmd):
    log.info(cmd)
    if os.system(cmd):
        raise Exception("Failed executing command %s." % (cmd))
            

def update_control_dict(field_name, value, case_root = "."):
    in_file_path = os.path.join(case_root, "system", "controlDict")
    log.info("Setting {} to {} in {}".format(field_name, value, in_file_path))
    with open(in_file_path, "r") as in_file:
        with open("controlDict.new", "w") as out_file:
            for line in in_file:
                out_file.write(re.sub("^{}.*;".format(field_name), "{}\t{}; // Set by run_case.py".format(field_name, value), line))
    safe_exec("mv controlDict.new {}".format(in_file_path))
    log.info("Done updating controlDict.")


def run_case(config_json, run_in_foreground = False, run = False):
    """
    Runs the specified case using the configuration 
    provided in the json file.
    """
    warnings = []
    errors = []
    ## LOAD THE CONFIG FILE
    with open(config_json, "r") as f:
        config = json.load(f)

    ## LOG.INFO(OUT THE CONFIG)
    log.info("*"*80)
    log.info("Run configuation:")
    for field in config:
        log.info("{:>20}: {}".format(field,  config[field]))
    log.info("*"*80)
    log.info("")

    base_case        = os.path.abspath(config["base_case"])
    if not os.path.exists(base_case):
        log.error("Could not find base case {}.".format(base_case))
        exit()
    
    mesh_file        = os.path.abspath(config["mesh_file"])
    if not os.path.exists(mesh_file):
        log.error("Could not find mesh file {}.".format(mesh_file))
        exit()
        
    output_root      = os.path.abspath(config["output_root"])
    solver           = config["solver"]
    base_case_scalar = config["base_case_scalar"]
    end_time         = config.get("end_time")
    write_interval   = config.get("write_interval")
    time_step        = config.get("delta_t")

    fix_patches         = config.get("fix_patches")
    scalar_inlet_config = config.get("scalar_inlet_config")
    

    log.info("Creating output directory.")
    safe_exec("mkdir -p {}".format(output_root))

    log.info("Copying base case contents to output directory.")
    # First get rid of the / if it exists, then add it, so that we copy the contents.
    base_case_root = os.path.dirname(os.path.join(base_case, ""))
    safe_exec("cp -a {}/. {}".format(base_case_root, output_root))
    
    log.info("Removing any mesh files from case root.")
    safe_exec("rm -f {}/*.msh".format(output_root))

    log.info("Copying mesh file to the case root.")
    safe_exec("cp -f {} {}".format(mesh_file, output_root))

    log.info("Changing directory to case root.")
    os.chdir(output_root)

    if scalar_inlet_config:
        log.info("Configuring scalars.")
        n_scalars = len(scalar_inlet_config)
        log.info("%d scalars found." % (n_scalars))
        if n_scalars > 1:
            solver += str(n_scalars)
            log.info("Solver name changed to %s." % (solver))
  
        path_to_scalar = os.path.join(output_root, "0", base_case_scalar)        
        configure_scalar_inlet_0(scalar_inlet_config, path_to_scalar)
    else:
        log.info("Using scalar configuration in base case.")

    log.info("Running gmshToFoam.")
    cmd = "gmshToFoam {} > output.gmshToFoam".format(os.path.basename(mesh_file))
    safe_exec(cmd)
    
    log.info("Running checkMesh.")
    cmd = "checkMesh > output.checkMesh"
    safe_exec(cmd)

    log.info("Examining checkMesh output.")
    checkMesh_output_file = "output.checkMesh"
    with open(checkMesh_output_file, "r") as f:
        if "Mesh OK" not in f.read():
            warnings.append("Could not find 'Mesh OK' in {}. Problem with mesh?".format(os.path.join(output_root, checkMesh_output_file)))
            log.warning(warnings[-1])
        else:
            log.info("Mesh is OK.")

    log.info("Fixing polyMesh boundary file.")
    fix_polyMesh_boundary_file(fix_patches)

    if write_interval:
        update_control_dict("writeInterval", write_interval, case_root = ".")

    if end_time:
        update_control_dict("endTime", end_time, case_root = ".")

    if time_step:
        update_control_dict("deltaT", time_step, case_root = ".")

    if run:
        if run_in_foreground:
            log.info("Starting case in foreground.")
            cmd = solver
        else:
            log.info("Starting case with foamJob.")
            cmd = "foamJob %s" % (solver)
            safe_exec(cmd)
    else:
        log.info("Done preparing case.")

    log.info("%d warnings.", len(warnings))
    for w in warnings:        
        log.warning(w)
    log.info("%d errors.", len(errors))
    for e in errors:
        log.error(e)
    log.info("Bye!")

    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("config_json", type=str, help="The json file containing the run configuration.")
    parser.add_argument("--foreground", help="If set will run the job in the foreground.", action="store_true")
    parser.add_argument("--run", help="If set will run the case.", action="store_true")
    args, unknown_args = parser.parse_known_args()
    # Get the remaining args, which should be e.g. 'leftWall=wall rightWall=wall etc.'
    run_case(args.config_json, args.foreground, args.run)
