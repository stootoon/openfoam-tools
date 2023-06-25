# openfoam-tools
Set of software tools for running and processing OpenFOAM cases.
## Useful utility functions
Describe what fieldstats.py does: 
- [fieldstats](./fieldstats.py): Lists several statistics about a field. Useful for determining the range of a field for plotting.
## Steps for creating a case
1. Creating the mesh.
### Creating meshes

## The post-processing pipeline
### Folder structure
- We generally like to keep the actual runs for a series in a 'raw' sub folder.
- E.g. SERIES_NAME/raw/Y0.[500|510|520] etc.
- The probe results and snapshots are placed in a corresponding 'proc' sub folder.
- E.g. SERIES_NAME/proc/Y0.[500|510|520]
- The advantage of this is that 'raw' can then be archived, 
### 1. Unzip the polyMesh files
   list | xargs -I {} sh -c "cd {}/constant/polyMesh; python $CFDGITPY/listdir.py --files | grep 'gz$' | xargs gzip -d"
### 1.5 Unzip the 0/S1.gz
- This is needed from some of the openfoam functions to work.
### 2. Probe the fields. 
   - This can be done using probe.py.
   - No need to unzip the files, this is done automatically in the scirpt.
   - Here's an example
       `cat yvals | xargs -I {} sh -c 'cd ff_int_sym_slow_high_tres_Y0.{}; python    $CFDGITPY/cmd2job.py "python -u \$CFDGITPY/probe.py S1 --xmin 0.2 --nx 41 --ny 21" --jobname p{} --submit;'`
### 3. Register the probe results
   - This copies the data files from their output locations to the probe registry.
    `list | grep ff_int | grep slow | grep -Po "0[^Y]+" | xargs -I {} sh -c "python $CFDGITPY/regprobe.py ff_int_sym_slow_Y{} sim cylgrid/ff_int_sym_slow_Y{} 10 '[1.2,0.5]' '[0.4,{}]' S1 --overwrite`
### 4. Figure out the field stats.
   `fieldstats S1`
   - This will give you the range of the data for the latest time point.
   - You can then use this to give you bounds for the snapshots.
### 5. Generate snapshots.
   - This generates a bunch of jobs that call ofsnapshot to take snapshots of the field at different points.
   `cat yvals | xargs -I {} sh -c "cd Y0.{}; rm job*.sh; python $CFDGITPY/gensnapjobs.py S1 --vmin 0 --vmax 10000 --every 10 --cmap gray --nperjob 50"`
### 6. Submit the jobs to generate the snapshots:
   `cat yvals | xargs -I {} sh -c "cd Y0.{}; ls job*.sh | grep -v 'job.sh' | xargs -n1 sbatch"`
   - We're remove job.sh because this can be left over from some other cmd2job scripts.
### 7. Move the snapshots to their own folder
   `cat yvals | xargs -I {} sh -c "cd Y0.{}; mkdir Y0.{}.png; mv S1*.png Y0.{}.png; tar -czvf Y0.{}.png.tar.gz Y0.{}.png;"`
   #+END_SRC
### 8. (Zip the snapshots folder - don't need this anymore) and remove the original folder
   `echo "230 235 265 270" | sed s/\ /\\n/g | xargs -I {} sh -c "cd ff_int_sym_slow_high_tres_Y0.{}; tar -czvf Y0.{}_png.tar.gz Y0.{}; rm -rf Y0.{};"`
   #+END_SRC
## 9. After this the zip files can e.g. be copied to a local machine for inspection with ImageJ.
  - E.g. from my mac:
  `echo "230 235 265 270" | sed s/\ /,/g | tr , '\n' | xargs -n1 -I {} cp ~/CAMP/Y0.{}_png.tar.gz`
### 10. Combine pngs into avi movies
- Use the _combine_pngs_ script.
- It takes optional --framerate (100) and --quality (1, highest) options.
- It takes zip files of gray scale PNGs, combines them using the Boulder colouring scheme, and writes the output to comb.avi.
- Here I move that avi to w2_y6_y9.avi
`python $CFDGITPY/combine_pngs.py w2_y6/w2_y6.png.tar.gz w2_y9/w2_y9.png.tar.gz; mv comb.avi w2_y6_y9.avi;`
### Unregistering probes
`python $CFDGITPY/unregprobe.py first-slow-series sim --unregister`
