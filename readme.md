# plotmap - easier map creation with basemap #

The plotmap class provides easy wrappers to the Matplotlib basemap module, enabling you to plot maps more quickly.

## Installation ##
Clone the repository to a location that you can add to your `PYTHONPATH`.

Dependencies: 

- `GeoRaster` (github.com/atedstone/georaster)
- `basemap`
- `matplotlib`


## Use ##

    import plotmap


## Create a map ##

    mymap = plotmap.Map(**kwargs)

The Map object must be created with georeferencing information. This can be provided in two ways:
     
1. *With the `ds_file` argument* : str, link to a raster dataset understood by GeoRaster. The extent of the plotting area and the lon_0 will be set according to the properties of the dataset.

2. *By setting `extent` and `lon_0` manually* :

    extent = (lon_lower_left,lon_upper_right,lat_lower_left,lat_upper_right)
    lon_0 = float, longitude of origin


By default a new matplotlib Figure will be created and new Axes to contain the map. You may optionally control the size of the new figure by passing `figsize=(x,y)`.

Alternatively, provide an existing Axes, in which case `figsize` is ignored, e.g.:

    fig = plt.figure(figsize(6,6))
    ax = plt.subplot(111)
    mymap = plotmap.Map(fig=fig,ax=ax,**kwargs)

You can then get access to the following references:

- mymap.map : matplotlib basemap instance of the map
- mymap.fig : Figure handle
- mymap.ax : Axes handle
- mymap.extent : (xmin,xmax,ymin,ymax) of the map area



## Adding data to the map ##

You can either use any of the several simple functions provided to add data to the map, e.g.:

	myimage = georaster.SingleBandRaster('myimg.tif')
    mymap.plot_data(myimage)


Or for more complicated cases you can use matplotlib directly to add raster data:

    myimage = georaster.SingleBandRaster('myimg.tif')
    plt.gca()
    # GeoRaster loads band data into r attribute
    # The basemap instance exposed by mymap.map is a pyproj conversion 
    # function between the map projection system and WGS84.
    plt.imshow(myimage.r,extent=myimage.get_extent_projected(mymap.map))


Shapefiles can also be plotted (no simple functions to do this yet, to do) by first loading them in using Basemap's readshapefile() function:

    shp_info = mymap.map.readshapefile('file','name',drawbounds=False)
    for shape,shapedict in zip(mymap.map.name,mymap.map.name_info):
	    xx,yy = zip(*shape)
	    mymap.map.plot(xx,yy)


Add point data:

    x,y = mymap.map(lon,lat)
    plt.plot(x,y,'^k')



## Add map features ##

Create a scale bar (various **kwargs available):

    scale_obj = mymap.plot_scale(length)


Add a geographic grid:

    mymap.geo_ticks(x_spacing,y_spacing)


Add a colorbar (various **kwargs available):

    cbar = mymap.plot_colorbar()




