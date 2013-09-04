# -*- coding: UTF-8 -*-
r'''
Name: gdal_calculator
Purpose: Perform simple tiled raster calculations (AKA "map algebra")
         from the commandline

Notes:
         Can handle rasters with different extents and coordinate systems
         as long as they overlap.

         Cellsizes must be the same.

Required parameters:
     --calc     : calculation in numpy syntax, rasters specified as using
                  any legal python variable name syntax, band numbers are
                  specified using square brackets (zero based indexing)
     --outfile  : output filepath
     --{*}      : filepaths for raster variables used in --calc
                  e.g. --calc='(someraster[0]+2)*c' --someraster='foo.tif' --c='bar.tif'

Optional parameters:
     --of            : GDAL format for output file (default "GTiff")')
     --co            : Creation option to the output format driver.
                       Multiple options may be listed.
     --extent        : one of MINOF|INTERSECT|MAXOF|UNION|"xmin ymin xmax ymax"
                       (Default=MINOF)
     --nodata        : handle nodata using masked arrays (Default=False)
                       uses numpy.ma.MaskedArray to handle NoData values
                       MaskedArrays can be much slower...
     --notile        : don't use tiled processing, faster but uses more memory (Default=False)
     --overwrite     : overwrite if required (Default=False)
     --reproject     : reproject if required (Default=False)
                       datasets are projected to the SRS of the first input
                       dataset in an expression
     --resampling    : one of "AVERAGE"|"BILINEAR"|"CUBIC"|"CUBICSPLINE"|
                       "LANCZOS"|"MODE"|"NEAREST"|gdal.GRA_*)
                       (Default="NEAREST")
     --tempdir       : temporary working directory

Example:
       gdal_calculator.py --outfile=../testdata/ndvi.tif       \
            --calc="((nir[3]-red[2].astype(numpy.float32))/(nir[3]+red[2].astype(numpy.float32)))" \
            --red=../testdata/landsat_utm50.tif  \
            --nir=../testdata/landsat_geo.tif    \
            --overwrite --reproject --extent=MAXOF
'''
#-------------------------------------------------------------------------------
# Copyright: (c) Luke Pinner 2013
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
#-------------------------------------------------------------------------------
if __name__=='__main__':
    import numpy,tempfile
    from gdal_dataset import Dataset,Env,ArrayDataset,Progress,geometry,gdal

    try: #Python == 2.7.x
        raise ImportError
        from argparse import (ArgumentParser,HelpFormatter)
        argparser=ArgumentParser()
    except ImportError: #python < 2.7, emulate argparse.ArgumentParser
        from optparse import (OptionParser,BadOptionError,HelpFormatter, Option)
        Option.ATTRS.append('required')
        class ArgumentParser(OptionParser):

            def parse_args(self, *args,**kwargs):
                known, unknown = OptionParser.parse_args(self,*args,**kwargs)
                #Make unknown list the same format as that returned by argparse.parse_known_args
                unknown=map('='.join,zip(unknown[::2],unknown[1::2]))
                return known, unknown

            def _process_args(self, largs, rargs, values):
                while rargs: #Dump unrecognised args into 'largs'
                    try:
                        OptionParser._process_args(self,largs,rargs,values)
                    except (BadOptionError), e:
                        largs.append(e.opt_str)

                #Check for required args - i.e. anything without a default
                for opt in self.option_list[1:]: #Skip --help
                    if getattr(self.values, opt.dest) is None and opt.required:
                        self.error('%s argument not supplied' % opt)

        argparser=ArgumentParser()
        argparser.parse_known_args=argparser.parse_args
        argparser.add_argument=argparser.add_option

    class formatter(HelpFormatter): #Just use the doc string as is.
        def format_help(self):return __doc__
    argparser.formatter_class=formatter

    #Parse command line args.
    ##Some args below originally derived from gdal_calc.py (MIT/X license)
    ##http://svn.osgeo.org/gdal/trunk/gdal/swig/python/scripts/gdal_calc.py

    #Required parameters
    argparser.add_argument('--calc', dest='calc', help='calculation in numpy syntax using +-/* or numpy array functions (i.e. numpy.logical_and())', required=True)
    argparser.add_argument('--outfile', dest='outfile', help='output file to Generate.', required=True)

    #Optional parameters
    argparser.add_argument('-q', dest='quiet', default=False, action='store_true', help='Suppress progress meter')
    argparser.add_argument('--of', dest='outformat', default='GTiff', help='GDAL format for output file (default "GTiff")')
    argparser.add_argument(
        '--creation-option', '--co', dest='creation_options', default=[], action='append',
        help='Passes a creation option to the output format driver. Multiple'
        'options may be listed. See format specific documentation for legal'
        'creation options for each format.')
    argparser.add_argument('--extent', dest='extent', default='MINOF', help='Output extent - one of "MINOF", "INTERSECT", "MAXOF", "UNION", "xmin ymin xmax ymax"')
    argparser.add_argument("--nodata", dest="nodata", default=False, action='store_true', help='Account for nodata  (Note this uses masked arrays which can be much slower)')
    argparser.add_argument('--overwrite', dest='overwrite', default=False, action='store_true', help='Overwrite output file if it already exists')
    argparser.add_argument('--reproject', dest='reproject', default=False, action='store_true', help='Reproject input rasters if required (datasets are projected to the SRS of the first input dataset in an expression)')
    argparser.add_argument('--resampling', dest='resampling', default='NEAREST', help='Resampling type when reprojecting - one of "AVERAGE"|"BILINEAR"|"CUBIC"|"CUBICSPLINE"|"LANCZOS"|"MODE"|"NEAREST"|gdal.GRA_*)')
    argparser.add_argument('--tempdir', dest='tempdir', default=tempfile.gettempdir(), help='Temp working directory')
    argparser.add_argument("--notile", dest='notile', default=False, action='store_true', help='Don\'t use tiled processing - True/False')

    args, rasters = argparser.parse_known_args()

    #Set environment variables
    try:Env.extent=map(float,args.extent.split())
    except:Env.extent=args.extent
    Env.nodata=args.nodata
    Env.overwrite=args.overwrite
    Env.reproject=args.reproject
    try:Env.resampling=int(args.resampling)
    except:Env.resampling=args.resampling
    Env.tempdir=args.tempdir
    Env.tiled=not args.notile

    #get Datset objects from input files
    datasets=[]
    for arg in rasters:
        var,path=arg.split('=')
        var=var.lstrip('-')
        locals()[var]=Dataset(path)
        datasets.append(locals()[var])

    #Setup progress meter
    if not args.quiet:
        try:
            import ast
            ops=ast.parse(args.calc,mode='eval')
            #How many operations/method calls?
            ops=len([i for i in ast.walk(ops.body) if isinstance(i,(ast.BinOp,ast.Call))])
        except:ops=len(datasets)+1
        Env.progress=Progress(ops)

    #Run the calculation
    try:
        #numexpr is sooo much quicker...
        #but can't use expressions like 'a[2]' or 'a.GetRasterBand(3)'
        import numexpr
        outfile=ArrayDataset(numexpr.evaluate(args.calc), prototype_ds=datasets[0])
    except:
        outfile = eval(args.calc)

    outfile.save(args.outfile,args.outformat,args.creation_options)
