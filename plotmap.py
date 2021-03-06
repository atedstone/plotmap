#coding=utf-8
"""
plotmap.py

Map : class to generate Basemap figures.

Creates a geo-referenced Basemap figure, and provides a number of methods 
to add different types of layers and information.

The methods are broadly arranged in the expected calling sequence. See 
method docstrings for further information.

Once the Map object has been created calling further methods of the object are
not necessary.

E.g. Add axes to subplot of existing figure:
>>> fig = plt.figure(figsize=(3,7))
>>> ax1 = plt.subplot(211)
>>> map1 = plotmap.Map(dsfile='myfile.tif', fig=fig, ax=ax)

Author : Andrew Tedstone
Date: October 2014

"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib import colors
from mpl_toolkits.basemap import Basemap
from mpl_toolkits.axes_grid1 import make_axes_locatable
import warnings
from matplotlib.colors import LightSource
from matplotlib import rcParams
import pandas as pd

import georaster


class Map:

    map = None
    fig = None
    extent = None

    def __init__(self,ds_file=None,
                      georaster=None,
                      extent=None,lon_0=None,
                      projection='tmerc',
                      figsize=None,fig=None,ax=None):
        """

        Create a new map.

        The Map object must be initialised with georeferencing information.
        This can be provided in three ways:

        (1)
            ds_file : str, link to a dataset understood by GDAL. 
                      The extent of the plotting area and the lon_0 will be 
                      set according to the properties of the dataset.
        
        (2) 
            extent : (lon_lower_left,lon_upper_right,lat_lower_left,
                      lat_upper_right)
            lon_0 : float, longitude of origin

        (3)
            provide a georaster.SingleBandRaster or MultiBandRaster instance 
            to the kwarg georaster

        Creation of the matplotlib figure:
        There are two options.
        1) Create figure automatically. 
                If desired, set figsize=(x,y).
                Leave fig=None and ax=None.
        2) Use existing axes.
                set fig=figure_obj and ax=ax_obj.
                figsize is ignored.

        E.g.
        >>> mymap = Map(ds_file='myim.tif')

        E.g.
        >>> mymap = Map(extent=(-50,-48,67,68),lon_0=70)

        """

        # Use handle to existing figure
        if fig != None and ax != None:
            self.fig = fig
            self.ax = ax
        # Create figure of specified size
        elif figsize != None:
            self.fig = plt.figure(figsize=figsize)
            self.ax = plt.subplot(111)
        # Create figure at system default size
        else:
            self.fig = plt.figure()
            self.ax = plt.subplot(111)


        # Get basic georeferencing info for map
        # From a geoTIFF
        if ds_file != None:
            ds = georaster.SingleBandRaster(ds_file,load_data=False)
            extent = ds.get_extent_latlon()  
            lon_0 = ds.srs.GetProjParm('central_meridian')
        elif georaster != None:
            extent = georaster.get_extent_latlon()  
            lon_0 = georaster.srs.GetProjParm('central_meridian')

        # Otherwise check that it has been provided manually
        else:
            if (extent == None) or (lon_0 == None):
                print('Either ds_file must be provided, or extent and lon_0.')
                raise AttributeError

        self.extent = extent
        lonll, lonur, latll, latur = extent

        # Create Basemap    
        self.map = Basemap(llcrnrlon=lonll,llcrnrlat=latll,urcrnrlon=lonur,
                      urcrnrlat=latur,resolution='i',projection=projection,
                      lon_0=lon_0,lat_0=0)



    def plot_background(self,bg_file,region='all',coarse=False):
        """
        Plot a background image onto the Basemap, in black and white.

        Optionally, coarsen resolution of background image, which will
        result in smaller file sizes in saved vector formats.

        Inputs:
            bg_file : str, path and filename of single-band GeoTIFF
            region : 'all' or latlon tuple (lonll,lonur,latll,latur)
            coarse : False or int to coarsen image by (e.g. 2)

        """

        if region == 'all':
            bg = georaster.SingleBandRaster(bg_file)
        else:
            bg = georaster.SingleBandRaster(bg_file,load_data=region,
                                              latlon=True)

        # Reduce image resolution
        if coarse != False:
            if type(coarse) == int:
                bg.r = bg.r[::coarse,::coarse]

        bg.r = np.where(bg.r == 0,np.nan,bg.r)   #remove black color
        plt.imshow(bg.r,cmap=cm.Greys_r,
                  extent=bg.get_extent_projected(self.map),
                  interpolation='nearest')



    def plot_dem(self,dem_file,region='all',azdeg=100,altdeg=65):
        """
        Plot a DEM using light-shading on the Basemap.

        Inputs:
            dem_file : path and filename of GeoTIFF DEM.
            region : 'all' or latlon tuple (lonll,lonur,latll,latur)
            azdeg/altdeg : azimuth (measured clockwise from south) and altitude (measured up from the plane of the surface) of the light source in degrees.
        """
 
        if region == 'all':
            dem = georaster.SingleBandRaster(dem_file)
        else:
            dem = georaster.SingleBandRaster(dem_file,load_data=region,
                                              latlon=True)
            
        ls = LightSource(azdeg=azdeg,altdeg=altdeg)
        rgb = ls.shade(dem.r,cmap=cm.Greys_r)  
        plt.imshow(rgb,extent=dem.get_extent_projected(self.map),
            interpolation='nearest')



    def plot_mask(self,mask_file,color='turquoise',region='all',alpha=1):
        """
        Plot masked values of the provided dataset.

        This can be useful to display 'bad' regions. If the colormap is set to
        discrete, the regions will be plotted in red, otherwise in white.

        Arguments:
            mask_file : str, path to geoTIFF of mask
            color : any matplotlib color, str or RGB triplet
            region : optional, latlon tuple (lonll,lonur,latll,latur) 

        """
        
        if region == 'all':
            mask = georaster.SingleBandRaster(mask_file)
        else:
            mask = georaster.SingleBandRaster(mask_file,load_data=region,
                                              latlon=True)

        #Pixels outside mask are transparent
        mask.r = np.where(mask.r==0,np.nan,1)

        # Now plot the bad data values
        cmap = cm.jet
        if color == 'turquoise':
            cmap.set_over((64./255,224./255,208./255))
        elif color == 'discr':
            cmap.set_under((155./255,0./255,0./255)) #gaps displayed in red
        else:
            try:
                cmap.set_over(eval(color))  #color is a RGB triplet
            except NameError: 
                cmap.set_over(color)      #color is str, e.g red, white...

        plt.imshow(mask.r,extent=mask.get_extent_projected(self.map),
                  cmap=cmap,vmin=-1,vmax=0,interpolation='nearest',alpha=alpha)



    def plot_data(self,data,vmin='min',vmax='max',cmap='jet'):
        """
        Basic function to plot a dataset with minimum and maximum values.

        In many cases you will be better off calling plt.imshow yourself
        instead.

        Arguments:
            data : georaster object of data to plot
            vmin : 'min' or minimum value to plot
            vmax : 'max' or maximum value to plot
            cmap : str, matplotlib colormap

        """

        if vmin == 'min':
            vmin = np.nanmin(data.r)
        if vmax == 'max':
            vmax = np.nanmax(data.r)
        # Discrete colormap option
        if cmap=='discr':
            cmap = cm.Blues
            bounds = [0,5,10,15,20,30,40,80,120,200]
            norm = colors.BoundaryNorm(bounds, cmap.N)
            plt.imshow(data.r,extent=data.get_extent_projected(self.map),
                cmap=cmap,
                vmin=0,norm=norm,interpolation='nearest',alpha=1)
        # Continuous colormap option
        else:
            plt.imshow(data.r,extent=data.get_extent_projected(self.map),
                cmap=plt.get_cmap(cmap),
                vmin=vmin,vmax=vmax,interpolation='nearest',alpha=1)


    def load_polygons(self, shp_file, label, drop_invalid=True):

        """
        Load polygons into a pandas DataFrame and return them.

        :param shp_file: the path to the shapefile (do not provide suffix)
        :type shp_file: str
        :param label: the label to give the features in the shapefile
        :type label: str

        :returns: a pandas DataFrame of polygons, with 'poly' column
        :rtype: pandas.DataFrame

        """

        from shapely.geometry import Polygon

        self.map.readshapefile(shp_file, label, drawbounds=False)

        # Load the polygons
        df = pd.DataFrame({
            'poly': [Polygon(xy) for xy in getattr(self.map, label)]
            })

        # Get all shapefile fields
        firstrow = getattr(self.map, label + '_info')[0]
        fields = [k for k in firstrow.keys()]

        # Assign fields to dataframe
        for f in fields:
            df[f] = [field[f] for field in getattr(self.map, label + '_info')]

        # Assign whether geometry valid
        if drop_invalid:
            df = df.assign(valid=[item.is_valid for item in df['poly']])
            # Delete invalid geometry
            df = df[df['valid']]

        return df



    def plot_polygons(self, df=None, shp_file=None, label=None, plot_kws=dict(), **kwargs):
        """
        Plot polygons on map.

        Either:
        (1) provide a pandas DataFrame with the `df` argument, likely
        loaded in using `load_polygons` and then manipulated in some way, or;
        (2) Provide a file path and associated label for a shapefile, the
        entire contents of the shapefile will be plotted.

        :param df: a pandas DataFrame containing a 'poly' column of shapely Polygons
        :type df: pandas.DataFrame
        :param shp_file: the path to the shapefile (do not provide suffix)
        :type shp_file: str
        :param label: the label to give the features in the shapefile
        :type label: str
        :param plot_kws: style keywords to apply to each PolygonPatch.
        :type plot_kws: dict
        :param drop_invalid: if True, drop all invalid geometries before plotting
        :type drop_invalid: bool

        :returns: nothing

        """

        from matplotlib.collections import PatchCollection
        from descartes import PolygonPatch

        if df is None and (shp_file is None or label is None):
            raise('Provide either df or both shp_file and label!')

        if df is None:
            df = self.load_polygons(shp_file, label)

        # Convert to Patches
        df['patches'] = df['poly'].map(lambda x: PolygonPatch(
                x, **plot_kws))

        # Plot on map
        self.ax.add_collection(PatchCollection(df['patches'].values, 
            match_original=True))  



    def geo_ticks(self,mstep,pstep,rotate_parallels=False,
                    mlabels=(0,0,0,1),plabels=(1,0,0,0),
                    round_to=0, **kwargs):
        """
        Add geographic (lat/lon) ticks to plot.

        :param mstep: meridians stepping in degrees
        :type mstep: float
        :param pstep: parallels stepping in degrees
        :type pstep: float
        :param rotate_parallels: if true then rotate parallel labels 90deg
        :type rotate_parallels: bool
        :param mlabels: specify which edges to draw meridian labels on
        :type mlabels: tuple
        :param plabels: specify which edges to draw parallel labels on
        :type plabels: tuple
        :param round_to: dp to round meridian and parallel steps to
        :type round_to: int
        :returns: none

        kwargs are passed directly to drawparallels() and drawmeridians().

        """

        m0 = int(np.round(self.map.lonmin/mstep,round_to))*mstep
        m1 = int(np.round(self.map.lonmax/mstep,round_to))*mstep
        p0 = int(np.round(self.map.latmin/pstep,round_to))*pstep
        p1 = int(np.round(self.map.latmax/pstep,round_to))*pstep

        
        parallels = self.map.drawparallels(np.arange(p0,p1,pstep),
            labels=plabels, **kwargs)

        if rotate_parallels == True and 1 in plabels:
            # Rotate text labels for parallels to save space
            for k,p in parallels.items():
                # p[1][0] is a text instance
                item = p[1][0]
                item.set_rotation('vertical')
        
        self.map.drawmeridians(np.arange(m0,m1,mstep),
                            labels=mlabels, **kwargs)



    def plot_scale(self,length,xpos=0.8,ypos=0.12,color='k'):
        """
        Plot a scale bar on the figure.

        Arguments:
            length : float, length of scale bar in map units.
            xpos : float, x position of scale in axes coordinates
            ypos : float, y position of scale in axes coordinates
            color : colour of scale bar

        Returns:
            scale object

        """
        lonll, lonur, latll, latur = self.extent
        xloc = lonll + xpos * (lonur-lonll)
        yloc = latll + ypos * (latur-latll)
        scale = self.map.drawmapscale(xloc,yloc,(lonur+lonll)/2,
                         (latur+latll)/2,length,fontcolor=color,
                         barstyle='fancy',fontsize=rcParams['font.size'])

        return scale




    def plot_colorbar(self,label=None,extend='neither',ticks=None):
        """
        Draw colorbar of the same height as the figure.

        Arguments:
            label : str, text to label colorbar with
            extend : 'neither', 'both'
            ticks : None (automatic ticks) or list of tick positions

        Returns:
            Colorbar object.

        """
        ax = self.ax   #get axis properties
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.1)
        if isinstance(ticks,list):
            cb = plt.colorbar(cax=cax, extend=extend,drawedges=False,
                ticks=ticks)
        else:
            cb = plt.colorbar(cax=cax, extend=extend,drawedges=False)
        if label != None:
            cb.set_label(label)
        cb.set_alpha(1)  #no transparency
        cb.draw_all()

        return cb



    def save_figure(self,outfile,dpi=300,left=0.1,right=0.9,top=0.95,bottom=0.07):
        """
        Save figure to outfile, having adjusted subplots, with 300dpi resn.

        Arguments:
            outfile : str, path and filename of file to save to.
            dpi : image resolution in dots per inch (default is 300)
            left/right/bottom/top : coordinates of the margins relative to the figure size
        """

        self.fig.subplots_adjust(left=left, right=right, top=top, bottom=bottom)
        self.fig.savefig(outfile,dpi=dpi)
